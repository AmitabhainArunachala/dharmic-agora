"""SAB A2A role grammar helpers.

This module intentionally stays small: it gives agents and tests one shared
source for the carrier-wave roles and the minimum handoff contract.
"""

from __future__ import annotations

from typing import Any, Mapping


ROLES = (
    "sparker",
    "challenger",
    "witness",
    "builder",
    "steward",
    "capitalizer",
    "composter",
    "canonizer",
)

LOOP_POSITIONS = (
    "spark",
    "challenge",
    "witness",
    "standing",
    "build",
    "deploy",
    "learn_earn",
    "fund",
    "canon_compost",
)

REQUIRED_HANDOFF_FIELDS = (
    "handoff_id",
    "from_agent",
    "to_agent",
    "role",
    "loop_position",
    "target_ref",
    "context_summary",
    "evidence_added",
    "changed_state",
    "open_challenges",
    "created_at",
)

TARGET_REF_FIELDS = ("claim_id", "build_id", "seed_id", "standing_id", "artifact_ref")


def validate_handoff(packet: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a SAB A2A handoff packet."""

    errors: list[str] = []
    for field in REQUIRED_HANDOFF_FIELDS:
        if field not in packet:
            errors.append(f"missing {field}")

    role = packet.get("role")
    if role is not None and role not in ROLES:
        errors.append(f"invalid role: {role}")

    loop_position = packet.get("loop_position")
    if loop_position is not None and loop_position not in LOOP_POSITIONS:
        errors.append(f"invalid loop_position: {loop_position}")

    target_ref = packet.get("target_ref")
    if not isinstance(target_ref, Mapping) or not any(target_ref.get(f) for f in TARGET_REF_FIELDS):
        errors.append("target_ref must include claim_id, build_id, seed_id, standing_id, or artifact_ref")

    evidence_added = packet.get("evidence_added")
    if not isinstance(evidence_added, list) or not any(str(item).strip() for item in evidence_added):
        errors.append("evidence_added must include at least one evidence reference")

    context_summary = packet.get("context_summary")
    if not isinstance(context_summary, str) or len(context_summary.strip()) < 10:
        errors.append("context_summary must be explicit")

    changed_state = packet.get("changed_state")
    if not isinstance(changed_state, str) or len(changed_state.strip()) < 5:
        errors.append("changed_state must say what changed")

    authority_lease = packet.get("authority_lease")
    if authority_lease is not None:
        if not isinstance(authority_lease, Mapping):
            errors.append("authority_lease must be an object when present")
        else:
            for field in ("scope", "expires_at", "revoker", "challenge_path"):
                if not str(authority_lease.get(field, "")).strip():
                    errors.append(f"authority_lease missing {field}")

    return errors
