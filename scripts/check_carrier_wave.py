#!/usr/bin/env python3
"""Check SAB carrier-wave invariants.

This is intentionally a structural check, not a full schema validator. It keeps
the repo from forgetting the recursive civilization engine contracts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

ROLES = {
    "sparker",
    "challenger",
    "witness",
    "builder",
    "steward",
    "capitalizer",
    "composter",
    "canonizer",
}

LOOP_TEXT = "spark -> challenge -> witness -> standing -> build -> deploy -> learn/earn -> fund -> canon/compost"

SEED_TYPES = {
    "project",
    "company",
    "lab",
    "governance",
    "crypto_protocol",
    "model_training",
    "ecology",
    "commerce_trading",
}

CONSTITUTION_LINES = {
    "Serve invariant truth.",
    "Improve the shared field.",
    "Challenge before amplifying.",
    "Build production-grade artifacts.",
    "Compost failures into future intelligence.",
    "Make authority scoped and temporary.",
    "Route value back into the commons.",
}


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _load_json(path: str | Path) -> Any:
    p = REPO_ROOT / path if isinstance(path, str) else path
    return json.loads(p.read_text(encoding="utf-8"))


def _append_missing(errors: list[str], path: str, needles: list[str]) -> None:
    text = _read(path)
    for needle in needles:
        if needle not in text:
            errors.append(f"{path} missing {needle!r}")


def check_docs(errors: list[str]) -> None:
    _append_missing(
        errors,
        "docs/SAB_RECURSIVE_CIVILIZATION_ENGINE.md",
        [
            LOOP_TEXT,
            "Every artifact in SAB should either:",
            "No Claim Without Scope",
            "No Authority Without Expiry",
            "No Canon Without Challenge",
            "No Build Without Evidence",
            "No Agent Handoff Without Role And Context",
            "No Institution Seed Without Anti-Capture Rules",
            "No Economic Loop Without Commons Return",
        ],
    )
    _append_missing(
        errors,
        "docs/AGENT_CONSTITUTION.md",
        sorted(CONSTITUTION_LINES),
    )
    _append_missing(
        errors,
        "docs/A2A_ROLE_GRAMMAR.md",
        sorted(ROLES) + ["target_ref", "evidence_added", "changed_state"],
    )
    _append_missing(
        errors,
        "docs/INTERNAL_PROPAGATION_CHECKLIST.md",
        [
            "No claim without scope.",
            "No authority without expiry.",
            "No canon without challenge, witness, and correction path.",
            "No authority without revoker.",
            "Economic seeds include commons return.",
        ],
    )
    _append_missing(
        errors,
        "prompts/SAB_CARRIER_WAVE_SYSTEM_PROMPT.md",
        [LOOP_TEXT, "Serve invariant truth.", "Do not use civilizational language to bypass evidence."],
    )
    _append_missing(
        errors,
        "agent_core/agents/README.md",
        [LOOP_TEXT, "Minimal handoff rule:"],
    )


def check_navigation(errors: list[str]) -> None:
    for path in ("README.md", "docs/INDEX.md", "docs/wiki/sab-agent-standing/README.md"):
        _append_missing(
            errors,
            path,
            [
                "docs/SAB_RECURSIVE_CIVILIZATION_ENGINE.md",
                "docs/AGENT_CONSTITUTION.md",
                "docs/A2A_ROLE_GRAMMAR.md",
            ],
        )


def check_schemas(errors: list[str]) -> None:
    handoff_schema = _load_json("nodes/schemas/a2a.handoff.schema.json")
    role_enum = set(handoff_schema["properties"]["role"]["enum"])
    if role_enum != ROLES:
        errors.append(f"a2a.handoff role enum mismatch: {sorted(role_enum)}")
    required = set(handoff_schema.get("required", []))
    for field in ("role", "loop_position", "target_ref", "context_summary", "evidence_added", "changed_state"):
        if field not in required:
            errors.append(f"a2a.handoff schema does not require {field}")
    authority_required = set(handoff_schema["properties"]["authority_lease"]["required"])
    for field in ("scope", "expires_at", "revoker", "challenge_path"):
        if field not in authority_required:
            errors.append(f"a2a.handoff authority_lease does not require {field}")

    seed_schema = _load_json("nodes/schemas/seed.packet.schema.json")
    seed_enum = set(seed_schema["properties"]["seed_type"]["enum"])
    if seed_enum != SEED_TYPES:
        errors.append(f"seed.packet seed_type enum mismatch: {sorted(seed_enum)}")
    seed_required = set(seed_schema.get("required", []))
    for field in (
        "claim",
        "challenge_plan",
        "witness_plan",
        "build_plan",
        "authority_lease",
        "anti_capture_rules",
        "commons_return",
        "canon_compost_policy",
    ):
        if field not in seed_required:
            errors.append(f"seed.packet schema does not require {field}")


def check_seed_templates(errors: list[str]) -> None:
    seen: set[str] = set()
    for path in sorted((REPO_ROOT / "seeds" / "templates").glob("*.seed.json")):
        packet = _load_json(path)
        seed_type = packet.get("seed_type")
        seen.add(str(seed_type))
        prefix = str(path.relative_to(REPO_ROOT))

        claim = packet.get("claim") if isinstance(packet.get("claim"), dict) else {}
        if not str(claim.get("scope", "")).strip():
            errors.append(f"{prefix} claim missing scope")
        if not claim.get("success_conditions") or not claim.get("failure_conditions"):
            errors.append(f"{prefix} claim missing success/failure conditions")

        challenge = packet.get("challenge_plan") if isinstance(packet.get("challenge_plan"), dict) else {}
        if challenge.get("required") is not True:
            errors.append(f"{prefix} challenge_plan.required must be true")
        if not challenge.get("strongest_objections"):
            errors.append(f"{prefix} challenge_plan missing strongest objections")

        build = packet.get("build_plan") if isinstance(packet.get("build_plan"), dict) else {}
        if not build.get("artifact_refs"):
            errors.append(f"{prefix} build_plan missing artifact_refs")

        authority = packet.get("authority_lease") if isinstance(packet.get("authority_lease"), dict) else {}
        for field in ("scope", "expires_at", "revoker", "challenge_path"):
            if not str(authority.get(field, "")).strip():
                errors.append(f"{prefix} authority_lease missing {field}")

        if not packet.get("anti_capture_rules"):
            errors.append(f"{prefix} missing anti_capture_rules")

        commons = packet.get("commons_return") if isinstance(packet.get("commons_return"), dict) else {}
        if not commons.get("mode") or not commons.get("minimum_return"):
            errors.append(f"{prefix} missing commons_return")

        canon = packet.get("canon_compost_policy") if isinstance(packet.get("canon_compost_policy"), dict) else {}
        if not canon.get("canon_conditions") or not canon.get("compost_conditions"):
            errors.append(f"{prefix} missing canon/compost conditions")

    if seen != SEED_TYPES:
        errors.append(f"seed templates mismatch: expected {sorted(SEED_TYPES)}, saw {sorted(seen)}")


def check_ui(errors: list[str]) -> None:
    _append_missing(
        errors,
        "site/standing.html",
        [
            LOOP_TEXT,
            "SAB Recursive Civilization Engine",
            "Agent Standing",
        ],
    )


def run_checks() -> list[str]:
    errors: list[str] = []
    check_docs(errors)
    check_navigation(errors)
    check_schemas(errors)
    check_seed_templates(errors)
    check_ui(errors)
    return errors


def main() -> int:
    errors = run_checks()
    report = {
        "passed": not errors,
        "errors": errors,
        "roles": sorted(ROLES),
        "seed_types": sorted(SEED_TYPES),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
