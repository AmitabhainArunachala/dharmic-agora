from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.project_seed_claims import discover_claim_packet_paths, project_claim
from agora.claim_promotion import discover_claim_files as discover_promotion_claim_files


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _claim_payload(claim_id: str = "claim-a04-test-seed-v1") -> dict:
    return {
        "claim_id": claim_id,
        "node_id": "anchor-04-complex-systems-cybernetics",
        "node_coordinate": "Node_04",
        "title": "Agentic Immune X-Ray seed claim",
        "lane": "venture",
        "status": "witnessed",
        "proposal_hash": "a" * 32,
        "requested_stage": "venture_proposal",
        "promotion": {"requested_stage": "venture_proposal"},
        "summary": "Bounded seed claim for public projection.",
        "artifact_refs": ["artifacts/proof.json"],
        "cross_node_refs": [
            {
                "node_id": "anchor-01-math-formal",
                "node_coordinate": "Node_01",
                "witness_ref": "nodes/anchors/anchor-01-math-formal/witness/wit-a04.json",
            }
        ],
        "red_team_refs": ["claims/redteam/angle-1.md"],
        "created_at": "2026-05-12T00:00:00+00:00",
        "updated_at": "2026-05-12T01:00:00+00:00",
    }


def test_discovery_ignores_witness_mandala_support_json(tmp_path: Path) -> None:
    claim_path = (
        tmp_path
        / "nodes/anchors/anchor-04-complex-systems-cybernetics/claims/claim-a04-test-seed-v1.json"
    )
    mandala_path = (
        tmp_path
        / "nodes/anchors/anchor-04-complex-systems-cybernetics/claims/witness_mandala/"
        / "claim-a04-test-seed-v1-formal.json"
    )
    _write_json(claim_path, _claim_payload())
    _write_json(
        mandala_path,
        {
            "claim_id": "claim-a04-test-seed-v1",
            "role": "formal",
            "witness_id": "mandala-claim-a04-test-seed-v1-formal",
        },
    )

    claim_paths, ignored_support = discover_claim_packet_paths(tmp_path / "nodes")

    assert claim_paths == [claim_path]
    assert ignored_support == [mandala_path]
    assert discover_promotion_claim_files(tmp_path / "nodes") == [claim_path]


def test_projection_refuses_raw_public_spark_json(tmp_path: Path) -> None:
    raw_spark = tmp_path / "site/data/raw_public_spark.json"
    _write_json(raw_spark, {"id": 1, "status": "canon", "content": "raw public spark"})

    claim_paths, ignored_support = discover_claim_packet_paths(tmp_path / "nodes")

    assert claim_paths == []
    assert ignored_support == []


def test_project_claim_includes_witness_and_redteam_refs(tmp_path: Path) -> None:
    claim_path = (
        tmp_path
        / "nodes/anchors/anchor-04-complex-systems-cybernetics/claims/claim-a04-test-seed-v1.json"
    )
    _write_json(claim_path, _claim_payload("claim-a04-agentic-immune-xray-test-v1"))

    projected = project_claim(claim_path, repo_root=tmp_path)

    assert projected["founding_seed"] is True
    assert projected["node_coordinate"] == "Node_04"
    assert projected["requested_stage"] == "venture_proposal"
    assert projected["witness_refs"] == [
        "nodes/anchors/anchor-01-math-formal/witness/wit-a04.json"
    ]
    assert projected["red_team_refs"] == ["claims/redteam/angle-1.md"]
    assert projected["source_policy"] == "claim_packet_only_no_raw_public_spark_projection"


def test_projector_cli_writes_seed_claims_json_from_real_anchor04(tmp_path: Path) -> None:
    output_path = tmp_path / "seed_claims.json"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/project_seed_claims.py",
            "--output",
            str(output_path),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    summary = json.loads(proc.stdout.strip())
    assert summary["claim_packets_projected"] >= 1
    assert summary["support_json_ignored"] >= 1

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    claim_ids = {claim["claim_id"] for claim in payload["claims"]}
    founding_id = (
        "claim-a04-complex-systems-cybernetics-agentic-immune-xray-"
        "internally-gated-proof-20260512-v1"
    )
    assert founding_id in claim_ids
    founding = next(claim for claim in payload["claims"] if claim["claim_id"] == founding_id)
    assert founding["node_coordinate"] == "Node_04"
    assert founding["witness_refs"]
    assert founding["red_team_refs"]
