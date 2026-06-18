#!/usr/bin/env python3
"""
Project schema-shaped node claim packets into the static seed-claim data file.

This is intentionally a one-way projection from node claim packets. It does not
scan public spark rows or support JSON records, so raw public sparks cannot
become seed claims without first passing through an operator/canon claim packet.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODES_ROOT = REPO_ROOT / "nodes"
DEFAULT_OUTPUT = REPO_ROOT / "site" / "data" / "seed_claims.json"

CLAIM_REQUIRED_FIELDS = (
    "claim_id",
    "node_id",
    "node_coordinate",
    "title",
    "status",
    "proposal_hash",
    "created_at",
    "updated_at",
)

NODE_LANES = {
    "dialogue",
    "papers",
    "code",
    "site",
    "venture",
    "claims",
    "witness",
    "runs",
    "artifacts",
}

NODE_COORDINATE_RE = re.compile(r"^Node_(0[1-9]|[1-3][0-9]|4[0-9])$")


class ProjectionError(ValueError):
    """Raised when a source file is not a projectable claim packet."""


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _is_under_claims_lane(path: Path) -> bool:
    return path.parent.name == "claims" and path.parent.parent.name.startswith("anchor-")


def discover_claim_packet_paths(nodes_root: Path) -> Tuple[List[Path], List[Path]]:
    """Return projectable top-level claim JSON paths and ignored support JSON paths."""
    if not nodes_root.exists():
        return [], []

    all_json = [p for p in sorted(nodes_root.rglob("*.json")) if p.is_file()]
    claim_paths: List[Path] = []
    ignored_support: List[Path] = []
    for path in all_json:
        if _is_under_claims_lane(path):
            claim_paths.append(path)
        elif "claims" in path.parts:
            ignored_support.append(path)
    return claim_paths, ignored_support


def _load_json_object(path: Path) -> Dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProjectionError("claim packet must be a JSON object")
    return raw


def _requested_stage(claim: Mapping[str, Any]) -> str:
    direct = claim.get("requested_stage")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    promotion = claim.get("promotion")
    if isinstance(promotion, Mapping):
        nested = promotion.get("requested_stage")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()

    many = claim.get("requested_stages")
    if isinstance(many, list):
        for item in many:
            if isinstance(item, str) and item.strip():
                return item.strip()

    if isinstance(promotion, Mapping):
        nested_many = promotion.get("requested_stages")
        if isinstance(nested_many, list):
            for item in nested_many:
                if isinstance(item, str) and item.strip():
                    return item.strip()

    return ""


def _list_of_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _cross_node_refs(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        node_id = str(item.get("node_id", "")).strip()
        node_coordinate = str(item.get("node_coordinate", "")).strip()
        witness_ref = str(item.get("witness_ref", "")).strip()
        if node_id and node_coordinate and witness_ref:
            refs.append(
                {
                    "node_id": node_id,
                    "node_coordinate": node_coordinate,
                    "witness_ref": witness_ref,
                }
            )
    return refs


def _validate_claim_shape(claim: Mapping[str, Any], path: Path) -> None:
    missing = [field for field in CLAIM_REQUIRED_FIELDS if field not in claim]
    if missing:
        raise ProjectionError(f"{path} is missing claim packet fields: {', '.join(missing)}")

    for field in CLAIM_REQUIRED_FIELDS:
        if not isinstance(claim.get(field), str) or not str(claim.get(field)).strip():
            raise ProjectionError(f"{path} has empty or non-string field: {field}")

    coordinate = str(claim.get("node_coordinate", "")).strip()
    if not NODE_COORDINATE_RE.match(coordinate):
        raise ProjectionError(f"{path} has invalid node_coordinate: {coordinate!r}")

    lane = claim.get("lane")
    if lane is not None and str(lane) not in NODE_LANES:
        raise ProjectionError(f"{path} has invalid lane: {lane!r}")

    if not _requested_stage(claim):
        raise ProjectionError(f"{path} has no requested_stage or promotion.requested_stage")


def project_claim(path: Path, *, repo_root: Path) -> Dict[str, Any]:
    claim = _load_json_object(path)
    _validate_claim_shape(claim, path)

    cross_refs = _cross_node_refs(claim.get("cross_node_refs"))
    witness_refs = _list_of_strings(claim.get("witness_refs"))
    witness_refs.extend(ref["witness_ref"] for ref in cross_refs)

    claim_id = str(claim["claim_id"]).strip()
    node_id = str(claim["node_id"]).strip()
    return {
        "claim_id": claim_id,
        "title": str(claim["title"]).strip(),
        "summary": str(claim.get("summary", "")).strip(),
        "node": node_id,
        "node_id": node_id,
        "node_coordinate": str(claim["node_coordinate"]).strip(),
        "lane": str(claim.get("lane", "")).strip() or "claims",
        "status": str(claim["status"]).strip(),
        "requested_stage": _requested_stage(claim),
        "source_gate": "operator_approved_claim_packet",
        "source_policy": "claim_packet_only_no_raw_public_spark_projection",
        "founding_seed": (
            node_id == "anchor-04-complex-systems-cybernetics"
            and "agentic-immune-xray" in claim_id
        ),
        "claim_path": _relative_path(path, repo_root),
        "artifact_refs": _list_of_strings(claim.get("artifact_refs")),
        "witness_refs": sorted(dict.fromkeys(witness_refs)),
        "cross_node_refs": cross_refs,
        "red_team_refs": _list_of_strings(claim.get("red_team_refs")),
        "human_review_refs": _list_of_strings(claim.get("human_review_refs")),
        "challenge_correction_refs": _list_of_strings(claim.get("challenge_correction_refs")),
        "sublation_refs": _list_of_strings(claim.get("sublation_refs")),
        "supersedes_claim_ids": _list_of_strings(claim.get("supersedes_claim_ids")),
        "created_at": str(claim["created_at"]).strip(),
        "updated_at": str(claim["updated_at"]).strip(),
    }


def _projection_timestamp(claims: Sequence[Mapping[str, Any]]) -> str:
    timestamps = [
        str(claim.get("updated_at") or claim.get("created_at") or "").strip()
        for claim in claims
    ]
    timestamps = [ts for ts in timestamps if ts]
    return max(timestamps) if timestamps else ""


def build_projection(
    *,
    claim_paths: Iterable[Path],
    ignored_support_paths: Iterable[Path],
    repo_root: Path,
) -> Dict[str, Any]:
    claim_path_list = list(claim_paths)
    ignored_support_path_list = list(ignored_support_paths)
    claims = [project_claim(path, repo_root=repo_root) for path in claim_path_list]
    claims.sort(
        key=lambda item: (
            not bool(item.get("founding_seed")),
            str(item.get("node_coordinate", "")),
            str(item.get("title", "")),
        )
    )
    return {
        "schema": "sab.seed_claims.v1",
        "generated_at": _projection_timestamp(claims),
        "source": "schema_valid_node_claim_packets",
        "policy": (
            "Only top-level node claims/*.json packets with requested promotion stages are "
            "projected. Public sparks and claim support JSON, including witness_mandala role "
            "records, are ignored."
        ),
        "claims": claims,
        "stats": {
            "claim_files_scanned": len(claim_path_list),
            "claim_packets_projected": len(claims),
            "support_json_ignored": len(ignored_support_path_list),
        },
    }


def write_projection(output_path: Path, payload: Mapping[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Project node claim packets to site/data/seed_claims.json")
    parser.add_argument(
        "--nodes-root",
        default=str(DEFAULT_NODES_ROOT),
        help="Nodes root to scan when --claim is not provided",
    )
    parser.add_argument(
        "--claim",
        action="append",
        default=[],
        help="Specific top-level claim packet path to project. Can be repeated.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing output")
    args = parser.parse_args()

    repo_root = REPO_ROOT
    if args.claim:
        claim_paths = [Path(p) for p in args.claim]
        ignored_support_paths: List[Path] = []
        invalid_paths = [p for p in claim_paths if not _is_under_claims_lane(p)]
        if invalid_paths:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": "specific --claim paths must be top-level node claims/*.json packets",
                        "paths": [str(p) for p in invalid_paths],
                    },
                    sort_keys=True,
                )
            )
            return 2
    else:
        claim_paths, ignored_support_paths = discover_claim_packet_paths(Path(args.nodes_root))

    try:
        payload = build_projection(
            claim_paths=claim_paths,
            ignored_support_paths=ignored_support_paths,
            repo_root=repo_root,
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2

    if not payload["claims"]:
        print(json.dumps({"status": "error", "error": "no claim packets projected"}, sort_keys=True))
        return 2

    output_path = Path(args.output)
    if not args.dry_run:
        write_projection(output_path, payload)

    print(
        json.dumps(
            {
                "status": "ok",
                "dry_run": bool(args.dry_run),
                "output": str(output_path),
                "claim_packets_projected": payload["stats"]["claim_packets_projected"],
                "support_json_ignored": payload["stats"]["support_json_ignored"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
