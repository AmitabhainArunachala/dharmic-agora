"""
SAB witness-link helpers.

This module keeps the witness triad logically separate while giving each domain
shared cross-link metadata so related publication and governance events can be
resolved back to the same witnessed action.
"""

from __future__ import annotations

import json
import secrets
from typing import Any, Dict, Iterable, List, Optional

PUBLICATION_WITNESS_DOMAIN = "publication"
ARTIFACT_WITNESS_DOMAIN = "artifact"
GOVERNANCE_WITNESS_DOMAIN = "governance"

_DOMAIN_PREFIX = {
    PUBLICATION_WITNESS_DOMAIN: "pub",
    ARTIFACT_WITNESS_DOMAIN: "art",
    GOVERNANCE_WITNESS_DOMAIN: "gov",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def generate_witness_link_id(domain: str) -> str:
    prefix = _DOMAIN_PREFIX.get(domain, "wit")
    return f"{prefix}_{secrets.token_hex(8)}"


def normalize_related_link_ids(related_link_ids: Optional[Iterable[str]]) -> List[str]:
    if related_link_ids is None:
        return []
    normalized: List[str] = []
    seen: set[str] = set()
    for raw in related_link_ids:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def encode_related_link_ids(related_link_ids: Optional[Iterable[str]]) -> str:
    return _canonical_json(normalize_related_link_ids(related_link_ids))


def decode_related_link_ids(raw_value: Any) -> List[str]:
    if raw_value in (None, "", b""):
        return []
    if isinstance(raw_value, list):
        return normalize_related_link_ids(raw_value)
    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    return normalize_related_link_ids(parsed)


def attach_witness_meta(
    details: Optional[Dict[str, Any]],
    *,
    domain: str,
    action: str,
    actor_id: Optional[str],
    subject_type: Optional[str],
    subject_id: Optional[Any],
    origin: str,
    witness_link_id: Optional[str] = None,
    related_link_ids: Optional[Iterable[str]] = None,
) -> tuple[str, Dict[str, Any], List[str]]:
    link_id = witness_link_id or generate_witness_link_id(domain)
    normalized_related = normalize_related_link_ids(related_link_ids)
    merged = dict(details or {})
    merged["witness_meta"] = {
        "link_id": link_id,
        "domain": domain,
        "action": action,
        "actor_id": actor_id,
        "subject_type": subject_type,
        "subject_id": str(subject_id) if subject_id is not None else None,
        "origin": origin,
        "related_link_ids": normalized_related,
    }
    return link_id, merged, normalized_related
