"""Agent-readable SAB MCP tool manifest.

This module defines the public MCP tool surface for SAB agent seeding v1. It is
intentionally a manifest, not a network client: runtime handlers should bind
these names to the canonical `/api/v1` routes once those endpoints are active.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SECRET_HANDLING_WARNING = (
    "Never pass SAB private keys, API keys, session tokens, cookies, identity "
    "tokens, or operator secrets as MCP tool arguments. Mutation tools require "
    "signatures produced by a local signer or approved key manager."
)

MCP_TOOL_NAMES = (
    "sab.seed.submit",
    "sab.seed.status",
    "sab.seed.fetch",
    "sab.challenge.submit",
    "sab.challenge.fetch",
    "sab.witness.fetch",
    "sab.standing.search",
    "sab.standing.fetch",
    "sab.lease.validate",
)

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "sab.seed.submit",
        "kind": "mutation",
        "method": "POST",
        "endpoint": "/api/v1/seeds",
        "description": "Submit a signed sab.seed_packet.v1 into pending_seed.",
        "requires_signature": True,
        "input_schema": {
            "type": "object",
            "required": ["seed_packet"],
            "properties": {
                "seed_packet": {"$ref": "/schemas/sab.seed_packet.v1.schema.json"},
                "signed_message": {"type": "object"},
            },
            "additionalProperties": False,
        },
        "returns": [
            "accepted",
            "seed_id",
            "state",
            "spark_projection_id",
            "challenge_window_closes_at",
            "witness_event_id",
            "witness_head",
            "next_actions",
        ],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.seed.status",
        "kind": "read",
        "method": "GET",
        "endpoint": "/api/v1/seeds/{seed_id}",
        "description": "Fetch seed state, challenge window, standing refs, and projection refs.",
        "requires_signature": False,
        "input_schema": {
            "type": "object",
            "required": ["seed_id"],
            "properties": {"seed_id": {"type": "string", "minLength": 3}},
            "additionalProperties": False,
        },
        "returns": ["seed_id", "state", "challenge_window", "standing_ids", "witness_head"],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.seed.fetch",
        "kind": "read",
        "method": "GET",
        "endpoint": "/api/v1/seeds/{seed_id}",
        "description": "Fetch canonical seed packet, evidence refs, and witness refs.",
        "requires_signature": False,
        "input_schema": {
            "type": "object",
            "required": ["seed_id"],
            "properties": {
                "seed_id": {"type": "string", "minLength": 3},
                "include_chain": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
        "returns": ["seed_packet", "evidence_bundle", "witness_event_ids", "public_url"],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.challenge.submit",
        "kind": "mutation",
        "method": "POST",
        "endpoint": "/api/v1/seeds/{seed_id}/challenges",
        "description": "Submit a signed challenge packet against a seed claim.",
        "requires_signature": True,
        "input_schema": {
            "type": "object",
            "required": ["target_seed_id", "challenge_packet"],
            "properties": {
                "target_seed_id": {"type": "string", "minLength": 3},
                "challenge_packet": {"type": "object"},
                "signed_message": {"type": "object"},
            },
            "additionalProperties": False,
        },
        "returns": ["challenge_id", "target_seed_id", "state", "witness_event_id", "witness_head"],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.challenge.fetch",
        "kind": "read",
        "method": "GET",
        "endpoint": "/api/v1/challenges/{challenge_id}",
        "description": "Fetch challenge packet, severity, status, and resolution refs.",
        "requires_signature": False,
        "input_schema": {
            "type": "object",
            "required": ["challenge_id"],
            "properties": {"challenge_id": {"type": "string", "minLength": 3}},
            "additionalProperties": False,
        },
        "returns": ["challenge_packet", "status", "resolution", "witness_event_ids"],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.witness.fetch",
        "kind": "read",
        "method": "GET",
        "endpoint": "/api/v1/witness-events/{event_id}",
        "alternate_endpoint": "/api/v1/seeds/{seed_id}/chain",
        "description": "Fetch one witness event or a seed witness chain segment.",
        "requires_signature": False,
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "minLength": 3},
                "seed_id": {"type": "string", "minLength": 3},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
            "anyOf": [{"required": ["event_id"]}, {"required": ["seed_id"]}],
            "additionalProperties": False,
        },
        "returns": ["witness_event", "events", "head", "verified"],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.standing.search",
        "kind": "read",
        "method": "GET",
        "endpoint": "/api/v1/standing",
        "description": "Search standing leases by subject, status, scope, or expiry.",
        "requires_signature": False,
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "status": {"type": "string"},
                "scope": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "additionalProperties": False,
        },
        "returns": ["standing_leases", "warnings"],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.standing.fetch",
        "kind": "read",
        "method": "GET",
        "endpoint": "/api/v1/standing/{standing_id}",
        "description": "Fetch a standing lease and its reliance boundaries.",
        "requires_signature": False,
        "input_schema": {
            "type": "object",
            "required": ["standing_id"],
            "properties": {"standing_id": {"type": "string", "minLength": 3}},
            "additionalProperties": False,
        },
        "returns": [
            "standing_id",
            "scope",
            "status",
            "expiry",
            "revoker",
            "challenge_path",
            "allowed_reliance",
            "forbidden_reliance",
            "witness_event_ids",
        ],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
    {
        "name": "sab.lease.validate",
        "kind": "read",
        "method": "GET",
        "endpoint": "/api/v1/authority-leases/{lease_id}",
        "description": (
            "Validate authority lease scope, expiry, revoker, challenge path, and status."
        ),
        "requires_signature": False,
        "input_schema": {
            "type": "object",
            "required": ["lease_id", "intended_action", "intended_scope"],
            "properties": {
                "lease_id": {"type": "string", "minLength": 3},
                "intended_action": {"type": "string", "minLength": 3},
                "intended_scope": {"type": "string", "minLength": 3},
            },
            "additionalProperties": False,
        },
        "returns": [
            "valid",
            "lease_id",
            "scope",
            "expires_at",
            "revoker",
            "challenge_path",
            "warnings",
        ],
        "secret_handling": SECRET_HANDLING_WARNING,
    },
]


def list_tools() -> list[dict[str, Any]]:
    """Return a copy of the SAB MCP tool manifest."""

    return deepcopy(MCP_TOOLS)


def get_tool(name: str) -> dict[str, Any]:
    """Return one SAB MCP tool manifest entry by name."""

    for tool in MCP_TOOLS:
        if tool["name"] == name:
            return deepcopy(tool)
    raise KeyError(f"unknown SAB MCP tool: {name}")


__all__ = [
    "MCP_TOOL_NAMES",
    "MCP_TOOLS",
    "SECRET_HANDLING_WARNING",
    "get_tool",
    "list_tools",
]
