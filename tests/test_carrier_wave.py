from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from connectors.a2a_role_grammar import ROLES, validate_handoff


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def test_carrier_wave_check_passes() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/check_carrier_wave.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is True


def test_a2a_role_grammar_rejects_context_free_handoff() -> None:
    errors = validate_handoff(
        {
            "handoff_id": "handoff-test-001",
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "role": "builder",
            "loop_position": "build",
            "target_ref": {},
            "context_summary": "",
            "evidence_added": [],
            "changed_state": "",
            "open_challenges": [],
            "created_at": "2026-07-01T00:00:00Z",
        }
    )
    assert "target_ref must include claim_id, build_id, seed_id, standing_id, or artifact_ref" in errors
    assert "evidence_added must include at least one evidence reference" in errors
    assert "context_summary must be explicit" in errors
    assert "changed_state must say what changed" in errors


def test_a2a_role_grammar_accepts_scoped_handoff() -> None:
    errors = validate_handoff(
        {
            "handoff_id": "handoff-test-002",
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "role": "challenger",
            "loop_position": "challenge",
            "target_ref": {"seed_id": "seed-project-template-v0"},
            "context_summary": "Challenge the seed before build promotion.",
            "evidence_added": ["seeds/templates/project.seed.json"],
            "changed_state": "Moved seed into challenge review.",
            "open_challenges": ["Does the seed define commons return?"],
            "authority_lease": {
                "scope": "Review only.",
                "expires_at": "2026-12-31T00:00:00Z",
                "revoker": "sab-steward-or-witness-quorum",
                "challenge_path": "docs/INTERNAL_PROPAGATION_CHECKLIST.md",
            },
            "created_at": "2026-07-01T00:00:00Z",
        }
    )
    assert errors == []


def test_a2a_schema_role_enum_matches_code() -> None:
    schema = _load_json("nodes/schemas/a2a.handoff.schema.json")
    assert set(schema["properties"]["role"]["enum"]) == set(ROLES)


def test_seed_packet_templates_cover_all_required_seed_types() -> None:
    schema = _load_json("nodes/schemas/seed.packet.schema.json")
    expected = set(schema["properties"]["seed_type"]["enum"])
    seen = {
        _load_json(str(path.relative_to(REPO_ROOT)))["seed_type"]
        for path in (REPO_ROOT / "seeds" / "templates").glob("*.seed.json")
    }
    assert seen == expected


def test_seed_templates_have_non_optional_carrier_wave_fields() -> None:
    for path in (REPO_ROOT / "seeds" / "templates").glob("*.seed.json"):
        packet = _load_json(str(path.relative_to(REPO_ROOT)))
        assert packet["claim"]["scope"]
        assert packet["challenge_plan"]["required"] is True
        assert packet["challenge_plan"]["strongest_objections"]
        assert packet["build_plan"]["artifact_refs"]
        assert packet["authority_lease"]["expires_at"]
        assert packet["authority_lease"]["revoker"]
        assert packet["anti_capture_rules"]
        assert packet["commons_return"]["minimum_return"]
        assert packet["canon_compost_policy"]["canon_conditions"]
        assert packet["canon_compost_policy"]["compost_conditions"]
