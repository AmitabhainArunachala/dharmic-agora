from __future__ import annotations

import json
import secrets
import sqlite3
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query, status


SEED_STATES = {
    "pending_seed",
    "challenge_window_open",
    "challenged",
    "corrected",
    "witnessed",
    "standing_active",
    "canon_candidate",
    "canon",
    "compost",
    "revoked",
    "expired",
}

CHALLENGE_STATUSES = {"pending", "responded", "sustained", "rejected"}
STANDING_STATUSES = {"active", "challenged", "revoked", "expired", "canon", "compost"}
WITNESS_EVENT_TYPES = {
    "submit",
    "gate_scored",
    "challenge",
    "response",
    "correction",
    "affirm",
    "refuse",
    "standing_issued",
    "revoked",
    "expired",
    "canon",
    "compost",
}


@dataclass(frozen=True)
class SabSeedingDeps:
    init_db: Callable[[], None]
    db: Callable[[], AbstractContextManager[sqlite3.Connection]]
    verify_agent_signature: Callable[[sqlite3.Connection, str, bytes, str], None]
    system_sign: Callable[[Dict[str, Any]], str]
    utc_now: Callable[[], str]
    invalidate_web_cache: Callable[[], None]


def create_sab_seeding_router(deps: SabSeedingDeps) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["sab-seeding-v1"])

    @router.post("/agents/register", status_code=status.HTTP_201_CREATED)
    async def register_agent_identity(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        deps.init_db()
        public_key = _required_str(payload, "public_key")
        display_name = str(payload.get("display_name") or payload.get("name") or "sab-agent").strip()
        if not display_name:
            raise HTTPException(status_code=400, detail="display_name is required")
        subject_id = str(payload.get("subject_id") or _subject_id_for_public_key(public_key)).strip()
        if not subject_id.startswith("agent_"):
            raise HTTPException(status_code=400, detail="subject_id must be an agent identity")
        identity_ref = str(payload.get("identity_ref") or f"sab_identity_{subject_id}").strip()
        created_at = deps.utc_now()
        identity = {
            "schema": "sab.agent_identity.v1",
            "subject_id": subject_id,
            "identity_ref": identity_ref,
            "display_name": display_name,
            "identity_rail": str(payload.get("identity_rail") or "ed25519"),
            "public_key": public_key,
            "controller": str(payload.get("controller") or "unknown"),
            "operator_backing": payload.get("operator_backing") if isinstance(payload.get("operator_backing"), dict) else {},
            "external_attestations": payload.get("external_attestations")
            if isinstance(payload.get("external_attestations"), list)
            else [],
            "created_at": created_at,
            "revocation_status": "active",
            "evidence_refs": [f"web_agents:{subject_id}"],
        }
        with deps.db() as conn:
            _init_v1_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO web_agents
                    (id, name, public_key, created_at, witness_count, witness_accuracy)
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM web_agents WHERE id = ?), ?), 0, 0.0)
                """,
                (subject_id, display_name, public_key, subject_id, created_at),
            )
            deps.invalidate_web_cache()
        return identity

    @router.get("/agents/me/home")
    async def agent_home(subject_id: str = Query(...)) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            agent = conn.execute(
                "SELECT id, name, public_key, created_at FROM web_agents WHERE id = ?",
                (subject_id,),
            ).fetchone()
            if agent is None:
                raise HTTPException(status_code=404, detail="agent not found")
            seed_rows = conn.execute(
                """
                SELECT seed_id, state, challenge_window_closes_at
                FROM sab_seed_packets_v1
                WHERE claimant_identity = ?
                ORDER BY id DESC
                LIMIT 25
                """,
                (subject_id,),
            ).fetchall()
            challenge_rows = conn.execute(
                """
                SELECT challenge_id, target_seed_id, status
                FROM sab_challenge_packets_v1
                WHERE challenger_identity = ? OR target_seed_id IN (
                    SELECT seed_id FROM sab_seed_packets_v1 WHERE claimant_identity = ?
                )
                ORDER BY id DESC
                LIMIT 25
                """,
                (subject_id, subject_id),
            ).fetchall()
            return {
                "schema": "sab.agent_home.v1",
                "subject_id": subject_id,
                "identity_status": "active",
                "agent": dict(agent),
                "active_authority_leases": [],
                "pending_seeds": [
                    {
                        "seed_id": str(row["seed_id"]),
                        "state": str(row["state"]),
                        "challenge_window_closes_at": row["challenge_window_closes_at"],
                    }
                    for row in seed_rows
                    if str(row["state"]) not in {"canon", "compost", "revoked", "expired"}
                ],
                "challenges_requiring_response": [
                    {
                        "challenge_id": str(row["challenge_id"]),
                        "target_seed_id": str(row["target_seed_id"]),
                        "status": str(row["status"]),
                    }
                    for row in challenge_rows
                    if str(row["status"]) == "pending"
                ],
                "witness_requests": [],
                "expiries": [],
                "recommended_next_action": "submit_seed_or_review_challenges",
            }

    @router.post("/seeds", status_code=status.HTTP_201_CREATED)
    async def submit_seed(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            seed_packet = _extract_object(payload, "seed_packet", "packet")
            signature_hex = _extract_signature(seed_packet, payload)
            packet_for_hash = _without_signature(seed_packet)

            seed_id = _required_str(packet_for_hash, "seed_id")
            claimant_identity = _claimant_identity(packet_for_hash, seed_packet)
            authority_lease = _validate_authority_lease(
                packet_for_hash.get("authority_lease"),
                expected_subject=claimant_identity,
                purpose="submit_seed",
            )
            created_at = _required_str(packet_for_hash, "created_at")
            _ensure_not_expired(authority_lease["expires_at"], "authority lease expired")

            seed_packet_hash = _hash_json(packet_for_hash)
            message = _seed_submit_message(
                seed_packet_hash=seed_packet_hash,
                claimant_identity=claimant_identity,
                authority_lease_id=authority_lease["lease_id"],
                created_at=created_at,
            )
            deps.verify_agent_signature(conn, claimant_identity, _canonical_bytes(message), signature_hex)
            _record_signature_use(conn, signature_hex, _hash_json(message), claimant_identity)

            if conn.execute("SELECT 1 FROM sab_seed_packets_v1 WHERE seed_id = ?", (seed_id,)).fetchone():
                raise HTTPException(status_code=409, detail="seed already exists")

            claim = _object_value(packet_for_hash, "claim")
            claim_id = str(claim.get("claim_id") or f"sab_claim_{_sha256_hex(str(claim.get('text', '')).encode())[:16]}")
            challenge_window_closes_at = _challenge_window_closes_at(packet_for_hash, created_at)
            spark_projection_id: Optional[int] = None
            if bool(payload.get("create_spark_projection", True)):
                spark_projection_id = _create_spark_projection(conn, packet_for_hash, claimant_identity, seed_id)

            _upsert_authority_lease(conn, authority_lease, claimant_identity)
            now = deps.utc_now()
            conn.execute(
                """
                INSERT INTO sab_seed_packets_v1
                    (
                        seed_id, seed_type, title, claim_id, claimant_identity,
                        authority_lease_id, state, packet_json, packet_hash,
                        spark_projection_id, challenge_window_closes_at,
                        created_at, updated_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    seed_id,
                    str(packet_for_hash.get("seed_type") or "claim"),
                    str(packet_for_hash.get("title") or seed_id),
                    claim_id,
                    claimant_identity,
                    authority_lease["lease_id"],
                    "pending_seed",
                    _json_dumps(seed_packet),
                    seed_packet_hash,
                    spark_projection_id,
                    challenge_window_closes_at,
                    created_at,
                    now,
                ),
            )
            witness = _record_seed_transition(
                deps,
                conn,
                seed_id=seed_id,
                actor_identity=claimant_identity,
                event_type="submit",
                to_state="pending_seed",
                payload={
                    "seed_packet_hash": seed_packet_hash,
                    "authority_lease_id": authority_lease["lease_id"],
                    "spark_projection_id": spark_projection_id,
                },
                signature_hex=signature_hex,
                update_state=False,
            )
            deps.invalidate_web_cache()
            return {
                "accepted": True,
                "seed_id": seed_id,
                "state": "pending_seed",
                "spark_projection_id": spark_projection_id,
                "challenge_window_closes_at": challenge_window_closes_at,
                "witness_head": witness["hash"],
                "next_actions": ["fetch_seed", "challenge_seed", "submit_witness_event"],
            }

    @router.get("/seeds/{seed_id}")
    async def get_seed(seed_id: str) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            row = _seed_row(conn, seed_id)
            return _serialize_seed(conn, row)

    @router.get("/seeds/{seed_id}/chain")
    async def get_seed_chain(seed_id: str) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            _seed_row(conn, seed_id)
            return _seed_chain(conn, seed_id)

    @router.get("/seeds")
    async def list_seeds(
        state: Optional[str] = Query(default=None),
        status_filter: Optional[str] = Query(default=None, alias="status"),
        type_filter: Optional[str] = Query(default=None, alias="type"),
        claimant: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            clauses: List[str] = []
            params: List[Any] = []
            wanted_state = state or status_filter
            if wanted_state:
                clauses.append("state = ?")
                params.append(wanted_state)
            if type_filter:
                clauses.append("seed_type = ?")
                params.append(type_filter)
            if claimant:
                clauses.append("claimant_identity = ?")
                params.append(claimant)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = conn.execute(
                f"""
                SELECT *
                FROM sab_seed_packets_v1
                {where}
                ORDER BY id DESC
                LIMIT ?
                """,  # nosec B608 - where only contains fixed clauses.
                (*params, limit),
            ).fetchall()
            return {"items": [_serialize_seed(conn, row, include_packet=False) for row in rows]}

    @router.post("/seeds/{seed_id}/correct")
    async def correct_seed(seed_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            row = _seed_row(conn, seed_id)
            _ensure_seed_lease_active(conn, row)
            actor_identity = _required_str(payload, "actor_identity")
            created_at = _required_str(payload, "created_at")
            correction_payload = payload.get("correction") or payload.get("corrected_seed_packet") or {}
            correction_hash = _hash_json(correction_payload if isinstance(correction_payload, dict) else {"value": correction_payload})
            signature_hex = _required_str(payload, "signature")
            message = {
                "kind": "sab_seed_correct",
                "target_seed_id": seed_id,
                "actor_identity": actor_identity,
                "correction_sha256": correction_hash,
                "created_at": created_at,
            }
            deps.verify_agent_signature(conn, actor_identity, _canonical_bytes(message), signature_hex)
            _record_signature_use(conn, signature_hex, _hash_json(message), actor_identity)
            witness = _record_seed_transition(
                deps,
                conn,
                seed_id=seed_id,
                actor_identity=actor_identity,
                event_type="correction",
                to_state="corrected",
                payload={"correction_hash": correction_hash, "correction": correction_payload},
                signature_hex=signature_hex,
            )
            deps.invalidate_web_cache()
            return {"seed_id": seed_id, "state": "corrected", "witness_head": witness["hash"]}

    @router.post("/seeds/{seed_id}/withdraw")
    async def withdraw_seed(seed_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            row = _seed_row(conn, seed_id)
            actor_identity = _required_str(payload, "actor_identity")
            if actor_identity != str(row["claimant_identity"]):
                raise HTTPException(status_code=403, detail="only the claimant may withdraw the seed")
            created_at = _required_str(payload, "created_at")
            reason = str(payload.get("reason") or "")
            signature_hex = _required_str(payload, "signature")
            message = {
                "kind": "sab_seed_withdraw",
                "target_seed_id": seed_id,
                "actor_identity": actor_identity,
                "reason_sha256": _sha256_hex(reason.encode()),
                "created_at": created_at,
            }
            deps.verify_agent_signature(conn, actor_identity, _canonical_bytes(message), signature_hex)
            _record_signature_use(conn, signature_hex, _hash_json(message), actor_identity)
            witness = _record_seed_transition(
                deps,
                conn,
                seed_id=seed_id,
                actor_identity=actor_identity,
                event_type="compost",
                to_state="compost",
                payload={"reason": reason, "withdrawn": True},
                signature_hex=signature_hex,
            )
            deps.invalidate_web_cache()
            return {"seed_id": seed_id, "state": "compost", "witness_head": witness["hash"]}

    @router.post("/seeds/{seed_id}/challenges", status_code=status.HTTP_201_CREATED)
    async def submit_challenge(seed_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            seed = _seed_row(conn, seed_id)
            _ensure_seed_lease_active(conn, seed)
            challenge_packet = _extract_object(payload, "challenge_packet", "packet")
            packet_for_hash = _without_signature(challenge_packet)
            if str(packet_for_hash.get("target_seed_id") or seed_id) != seed_id:
                raise HTTPException(status_code=400, detail="challenge target_seed_id does not match URL")
            challenge_id = _required_str(packet_for_hash, "challenge_id")
            target_claim_id = str(packet_for_hash.get("target_claim_id") or seed["claim_id"])
            if target_claim_id != str(seed["claim_id"]):
                raise HTTPException(status_code=400, detail="challenge target_claim_id does not match seed claim")
            challenger_identity = _required_str(packet_for_hash, "challenger_identity")
            created_at = _required_str(packet_for_hash, "created_at")
            challenge_lease = packet_for_hash.get("authority_lease")
            if challenge_lease is not None:
                lease = _validate_authority_lease(challenge_lease, expected_subject=challenger_identity, purpose="challenge")
                _ensure_not_expired(lease["expires_at"], "authority lease expired")
                _upsert_authority_lease(conn, lease, challenger_identity)

            signature_hex = _extract_signature(challenge_packet, payload)
            signature_signer = _signature_signer(challenge_packet) or challenger_identity
            challenge_packet_hash = _hash_json(packet_for_hash)
            message = _challenge_submit_message(
                target_seed_id=seed_id,
                target_claim_id=target_claim_id,
                challenge_packet_hash=challenge_packet_hash,
                challenger_identity=challenger_identity,
                created_at=created_at,
            )
            deps.verify_agent_signature(conn, signature_signer, _canonical_bytes(message), signature_hex)
            _record_signature_use(conn, signature_hex, _hash_json(message), signature_signer)
            if conn.execute(
                "SELECT 1 FROM sab_challenge_packets_v1 WHERE challenge_id = ?",
                (challenge_id,),
            ).fetchone():
                raise HTTPException(status_code=409, detail="challenge already exists")

            now = deps.utc_now()
            conn.execute(
                """
                INSERT INTO sab_challenge_packets_v1
                    (
                        challenge_id, target_seed_id, target_claim_id, challenger_identity,
                        status, packet_json, packet_hash, response_json,
                        created_at, updated_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    challenge_id,
                    seed_id,
                    target_claim_id,
                    challenger_identity,
                    "pending",
                    _json_dumps(challenge_packet),
                    challenge_packet_hash,
                    None,
                    created_at,
                    now,
                ),
            )
            witness = _record_seed_transition(
                deps,
                conn,
                seed_id=seed_id,
                actor_identity=challenger_identity,
                event_type="challenge",
                to_state="challenged",
                payload={"challenge_id": challenge_id, "challenge_packet_hash": challenge_packet_hash},
                signature_hex=signature_hex,
            )
            challenge = _challenge_row(conn, challenge_id)
            deps.invalidate_web_cache()
            return {
                **_serialize_challenge(challenge),
                "state": "challenged",
                "seed_state": "challenged",
                "witness_head": witness["hash"],
            }

    @router.get("/challenges/{challenge_id}")
    async def get_challenge(challenge_id: str) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            return _serialize_challenge(_challenge_row(conn, challenge_id))

    @router.post("/challenges/{challenge_id}/respond", status_code=status.HTTP_201_CREATED)
    async def respond_to_challenge(challenge_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        return _resolve_challenge_action(deps, challenge_id, payload, action="respond", challenge_status="responded", seed_state="corrected")

    @router.post("/challenges/{challenge_id}/sustain", status_code=status.HTTP_201_CREATED)
    async def sustain_challenge(challenge_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        return _resolve_challenge_action(deps, challenge_id, payload, action="sustain", challenge_status="sustained", seed_state="compost")

    @router.post("/challenges/{challenge_id}/reject", status_code=status.HTTP_201_CREATED)
    async def reject_challenge(challenge_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        return _resolve_challenge_action(
            deps,
            challenge_id,
            payload,
            action="reject",
            challenge_status="rejected",
            seed_state="challenge_window_open",
        )

    @router.post("/witness-events", status_code=status.HTTP_201_CREATED)
    async def submit_witness_event(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            event_type = _required_str(payload, "event_type")
            if event_type not in WITNESS_EVENT_TYPES:
                raise HTTPException(status_code=400, detail="unsupported witness event_type")
            actor_identity = _required_str(payload, "actor_identity")
            subject_type = _required_str(payload, "subject_type")
            subject_id = _required_str(payload, "subject_id")
            created_at = _required_str(payload, "created_at")
            event_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
            signature_hex = _required_str(payload, "signature")
            subject_seed_id = _subject_seed_id(conn, subject_type, subject_id)
            expected_prev_hash = _latest_witness_hash(conn, subject_seed_id or f"{subject_type}:{subject_id}")
            supplied_prev_hash = str(payload.get("prev_hash") or expected_prev_hash)
            if supplied_prev_hash != expected_prev_hash:
                raise HTTPException(status_code=409, detail="prev_hash is stale")
            payload_hash = _hash_json(event_payload)
            message = _witness_event_message(
                event_type=event_type,
                subject_type=subject_type,
                subject_id=subject_id,
                payload_hash=payload_hash,
                prev_hash=expected_prev_hash,
                created_at=created_at,
            )
            deps.verify_agent_signature(conn, actor_identity, _canonical_bytes(message), signature_hex)
            _record_signature_use(conn, signature_hex, _hash_json(message), actor_identity)
            event = _append_witness_event(
                conn,
                event_type=event_type,
                actor_identity=actor_identity,
                subject_type=subject_type,
                subject_id=subject_id,
                subject_seed_id=subject_seed_id,
                payload=event_payload,
                signature_hex=signature_hex,
                timestamp=created_at,
                expected_prev_hash=expected_prev_hash,
            )
            if subject_type == "seed" and subject_seed_id:
                state = _state_for_witness_event(event_type)
                if state:
                    _record_seed_transition(
                        deps,
                        conn,
                        seed_id=subject_seed_id,
                        actor_identity=actor_identity,
                        event_type=event_type,
                        to_state=state,
                        payload={"witness_event_id": event["event_id"], "payload_hash": payload_hash},
                        signature_hex=signature_hex,
                        precreated_witness=event,
                    )
            deps.invalidate_web_cache()
            return event

    @router.get("/witness-events/{event_id}")
    async def get_witness_event(event_id: str) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            row = conn.execute(
                "SELECT * FROM sab_witness_events_v1 WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="witness event not found")
            return _serialize_witness_event(row)

    @router.get("/witness/chain")
    async def get_witness_chain(
        seed_id: Optional[str] = Query(default=None),
        subject_type: Optional[str] = Query(default=None),
        subject_id: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            rows = _witness_rows(conn, seed_id=seed_id, subject_type=subject_type, subject_id=subject_id, limit=limit)
            return {
                "verified": _verify_witness_rows(rows),
                "entries": [_serialize_witness_event(row) for row in rows],
            }

    @router.get("/witness/verify")
    async def verify_witness_chain(
        seed_id: Optional[str] = Query(default=None),
        subject_type: Optional[str] = Query(default=None),
        subject_id: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            rows = _witness_rows(conn, seed_id=seed_id, subject_type=subject_type, subject_id=subject_id, limit=10000)
            return {
                "verified": _verify_witness_rows(rows),
                "entry_count": len(rows),
                "head": str(rows[-1]["event_hash"]) if rows else "genesis",
            }

    @router.post("/standing/review", status_code=status.HTTP_201_CREATED)
    async def review_standing(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            if "standing_lease" not in payload and "lease" not in payload and "standing_id" not in payload:
                return _review_standing_request(deps, conn, payload)
            standing_lease = _extract_object(payload, "standing_lease", "lease")
            lease_for_hash = _without_signature(standing_lease)
            standing_id = _required_str(lease_for_hash, "standing_id")
            subject_seed_id = _required_str(lease_for_hash, "subject_seed_id")
            subject_claim_id = _required_str(lease_for_hash, "subject_claim_id")
            seed = _seed_row(conn, subject_seed_id)
            if str(seed["claim_id"]) != subject_claim_id:
                raise HTTPException(status_code=400, detail="standing subject_claim_id does not match seed")
            if _pending_challenge_count(conn, subject_seed_id) > 0:
                raise HTTPException(status_code=409, detail="standing review requires resolved challenge path")
            if _challenge_count(conn, subject_seed_id) < 1:
                raise HTTPException(status_code=409, detail="standing review requires a challenge")
            if _seed_witness_count(conn, subject_seed_id) < 1:
                raise HTTPException(status_code=409, detail="standing review requires a witness event")
            _validate_standing_lease(lease_for_hash)
            _ensure_not_expired(_standing_expiry(lease_for_hash), "standing lease expired")
            reviewer_identity = str(payload.get("reviewer_identity") or lease_for_hash.get("issued_by") or "")
            if not reviewer_identity:
                raise HTTPException(status_code=400, detail="reviewer_identity is required")
            created_at = str(lease_for_hash.get("issued_at") or payload.get("created_at") or "")
            if not created_at:
                raise HTTPException(status_code=400, detail="issued_at is required")
            signature_hex = _extract_signature(standing_lease, payload)
            standing_lease_hash = _hash_json(lease_for_hash)
            message = {
                "kind": "sab_standing_review",
                "standing_lease_sha256": standing_lease_hash,
                "subject_seed_id": subject_seed_id,
                "reviewer_identity": reviewer_identity,
                "created_at": created_at,
            }
            deps.verify_agent_signature(conn, reviewer_identity, _canonical_bytes(message), signature_hex)
            _record_signature_use(conn, signature_hex, _hash_json(message), reviewer_identity)
            if conn.execute(
                "SELECT 1 FROM sab_standing_leases_v1 WHERE standing_id = ?",
                (standing_id,),
            ).fetchone():
                raise HTTPException(status_code=409, detail="standing already exists")
            now = deps.utc_now()
            conn.execute(
                """
                INSERT INTO sab_standing_leases_v1
                    (
                        standing_id, subject_seed_id, subject_claim_id, scope, purpose,
                        status, lease_json, lease_hash, expiry, revoker,
                        challenge_path, issued_by, issued_at, updated_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    standing_id,
                    subject_seed_id,
                    subject_claim_id,
                    str(lease_for_hash.get("scope") or ""),
                    str(lease_for_hash.get("purpose") or ""),
                    "active",
                    _json_dumps(standing_lease),
                    standing_lease_hash,
                    _standing_expiry(lease_for_hash),
                    str(lease_for_hash.get("revoker") or ""),
                    str(lease_for_hash.get("challenge_path") or ""),
                    reviewer_identity,
                    created_at,
                    now,
                ),
            )
            event = _record_standing_event(
                deps,
                conn,
                standing_id=standing_id,
                actor_identity=reviewer_identity,
                event_type="standing_issued",
                to_status="active",
                payload={"standing_lease_hash": standing_lease_hash},
                signature_hex=signature_hex,
            )
            _record_seed_transition(
                deps,
                conn,
                seed_id=subject_seed_id,
                actor_identity=reviewer_identity,
                event_type="standing_issued",
                to_state="standing_active",
                payload={"standing_id": standing_id, "standing_lease_hash": standing_lease_hash},
                signature_hex=signature_hex,
                precreated_witness=event,
            )
            deps.invalidate_web_cache()
            return {**_serialize_standing(_standing_row(conn, standing_id)), "witness_head": event["hash"]}

    @router.get("/standing/{standing_id}")
    async def get_standing(standing_id: str) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            row = _expire_standing_if_needed(deps, conn, _standing_row(conn, standing_id))
            return _serialize_standing(row)

    @router.get("/standing")
    async def list_standing(
        subject: Optional[str] = Query(default=None),
        status_filter: Optional[str] = Query(default=None, alias="status"),
        scope: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> Dict[str, Any]:
        deps.init_db()
        with deps.db() as conn:
            _init_v1_tables(conn)
            clauses: List[str] = []
            params: List[Any] = []
            if subject:
                clauses.append("subject_seed_id = ?")
                params.append(subject)
            if status_filter:
                clauses.append("status = ?")
                params.append(status_filter)
            if scope:
                clauses.append("scope = ?")
                params.append(scope)
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = conn.execute(
                f"""
                SELECT *
                FROM sab_standing_leases_v1
                {where}
                ORDER BY id DESC
                LIMIT ?
                """,  # nosec B608 - where only contains fixed clauses.
                (*params, limit),
            ).fetchall()
            rows = [_expire_standing_if_needed(deps, conn, row) for row in rows]
            return {"items": [_serialize_standing(row, include_lease=False) for row in rows]}

    @router.post("/standing/{standing_id}/challenge")
    async def challenge_standing(standing_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        return _standing_action(deps, standing_id, payload, action="challenge", to_status="challenged", seed_state="challenged")

    @router.post("/standing/{standing_id}/revoke")
    async def revoke_standing(standing_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        return _standing_action(deps, standing_id, payload, action="revoke", to_status="revoked", seed_state="revoked")

    @router.post("/standing/{standing_id}/revalidate")
    async def revalidate_standing(standing_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        promote_to_canon = bool(payload.get("promote_to_canon") or payload.get("canon"))
        return _standing_action(
            deps,
            standing_id,
            payload,
            action="revalidate",
            to_status="canon" if promote_to_canon else "active",
            seed_state="canon" if promote_to_canon else "canon_candidate",
        )

    return router


def _init_v1_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_signature_index_v1 (
            signature TEXT PRIMARY KEY,
            message_hash TEXT NOT NULL,
            actor_identity TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_authority_leases_v1 (
            lease_id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            purpose TEXT NOT NULL,
            scope TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoker TEXT NOT NULL,
            challenge_path TEXT NOT NULL,
            lease_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_seed_packets_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed_id TEXT NOT NULL UNIQUE,
            seed_type TEXT NOT NULL,
            title TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            claimant_identity TEXT NOT NULL,
            authority_lease_id TEXT NOT NULL,
            state TEXT NOT NULL,
            packet_json TEXT NOT NULL,
            packet_hash TEXT NOT NULL,
            spark_projection_id INTEGER,
            challenge_window_closes_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_seed_packets_state ON sab_seed_packets_v1(state, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_seed_packets_claimant ON sab_seed_packets_v1(claimant_identity, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_seed_packets_claim ON sab_seed_packets_v1(claim_id)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_seed_events_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            seed_id TEXT NOT NULL,
            actor_identity TEXT NOT NULL,
            event_type TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            witness_event_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_seed_events_seed ON sab_seed_events_v1(seed_id, id ASC)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_challenge_packets_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id TEXT NOT NULL UNIQUE,
            target_seed_id TEXT NOT NULL,
            target_claim_id TEXT NOT NULL,
            challenger_identity TEXT NOT NULL,
            status TEXT NOT NULL,
            packet_json TEXT NOT NULL,
            packet_hash TEXT NOT NULL,
            response_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_challenge_seed ON sab_challenge_packets_v1(target_seed_id, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_challenge_status ON sab_challenge_packets_v1(status, id DESC)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_witness_events_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            chain_scope TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor_identity TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            subject_seed_id TEXT,
            timestamp TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            signature TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            event_hash TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_witness_chain_scope ON sab_witness_events_v1(chain_scope, id ASC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_witness_subject ON sab_witness_events_v1(subject_type, subject_id, id ASC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_witness_seed ON sab_witness_events_v1(subject_seed_id, id ASC)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_standing_leases_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            standing_id TEXT NOT NULL UNIQUE,
            subject_seed_id TEXT NOT NULL,
            subject_claim_id TEXT NOT NULL,
            scope TEXT NOT NULL,
            purpose TEXT NOT NULL,
            status TEXT NOT NULL,
            lease_json TEXT NOT NULL,
            lease_hash TEXT NOT NULL,
            expiry TEXT NOT NULL,
            revoker TEXT NOT NULL,
            challenge_path TEXT NOT NULL,
            issued_by TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_standing_seed ON sab_standing_leases_v1(subject_seed_id, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_standing_status ON sab_standing_leases_v1(status, id DESC)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sab_standing_events_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            standing_id TEXT NOT NULL,
            actor_identity TEXT NOT NULL,
            event_type TEXT NOT NULL,
            from_status TEXT,
            to_status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            witness_event_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sab_standing_events_standing ON sab_standing_events_v1(standing_id, id ASC)")


def _extract_object(payload: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return payload


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _canonical_bytes(payload: Dict[str, Any]) -> bytes:
    return _json_dumps(payload).encode()


def _sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _hash_json(payload: Any) -> str:
    if isinstance(payload, dict):
        return _sha256_hex(_canonical_bytes(payload))
    return _sha256_hex(_json_dumps(payload).encode())


def _subject_id_for_public_key(public_key: str) -> str:
    return f"agent_ed25519_{_sha256_hex(public_key.encode())[:16]}"


def _without_signature(payload: Dict[str, Any]) -> Dict[str, Any]:
    stripped = json.loads(_json_dumps(payload))
    if isinstance(stripped, dict):
        stripped.pop("signature", None)
    return stripped


def _extract_signature(*payloads: Dict[str, Any]) -> str:
    for payload in payloads:
        signature = payload.get("signature")
        if isinstance(signature, dict):
            value = signature.get("signature") or signature.get("value")
        else:
            value = signature
        if isinstance(value, str) and value:
            return value
    raise HTTPException(status_code=400, detail="signature is required")


def _signature_signer(*payloads: Dict[str, Any]) -> Optional[str]:
    for payload in payloads:
        signature = payload.get("signature")
        if isinstance(signature, dict):
            signer = signature.get("signer")
            if isinstance(signer, str) and signer.strip():
                return signer.strip()
    return None


def _identity_ref_subject(conn: sqlite3.Connection, identity_ref: str) -> Optional[str]:
    if not identity_ref.startswith("sab_identity_"):
        return None
    suffix = identity_ref[len("sab_identity_") :]
    if not suffix:
        return None
    direct = conn.execute("SELECT id FROM web_agents WHERE id = ?", (suffix,)).fetchone()
    if direct is not None:
        return str(direct["id"])
    by_name = conn.execute(
        "SELECT id FROM web_agents WHERE name = ? ORDER BY created_at DESC LIMIT 1",
        (suffix,),
    ).fetchone()
    if by_name is not None:
        return str(by_name["id"])
    return None


def _verify_signature_with_fallback(
    deps: SabSeedingDeps,
    conn: sqlite3.Connection,
    actor_id: str,
    message: Dict[str, Any],
    signature_hex: str,
) -> bool:
    try:
        deps.verify_agent_signature(conn, actor_id, _canonical_bytes(message), signature_hex)
        return True
    except HTTPException:
        return False


def _required_str(payload: Dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=400, detail=f"{key} is required")
    return value.strip()


def _object_value(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail=f"{key} is required")
    return value


def _claimant_identity(packet: Dict[str, Any], signed_packet: Dict[str, Any]) -> str:
    claimant = packet.get("claimant_identity")
    if isinstance(claimant, dict):
        subject_id = claimant.get("subject_id")
        if isinstance(subject_id, str) and subject_id.strip():
            return subject_id.strip()
    signature = signed_packet.get("signature")
    if isinstance(signature, dict):
        signer = signature.get("signer")
        if isinstance(signer, str) and signer.strip():
            return signer.strip()
    raise HTTPException(status_code=400, detail="claimant_identity.subject_id is required")


def _validate_authority_lease(
    lease: Any,
    *,
    expected_subject: str,
    purpose: str,
) -> Dict[str, str]:
    if not isinstance(lease, dict):
        raise HTTPException(status_code=400, detail="authority_lease is required")
    scope = str(lease.get("scope") or "").strip()
    expires_at = str(lease.get("expires_at") or lease.get("expiry") or "").strip()
    revoker = str(lease.get("revoker") or "").strip()
    challenge_path = str(lease.get("challenge_path") or "").strip()
    lease_id = str(lease.get("lease_ref") or lease.get("lease_id") or "").strip()
    if not scope:
        raise HTTPException(status_code=400, detail="authority_lease.scope is required")
    if not expires_at:
        raise HTTPException(status_code=400, detail="authority_lease.expires_at is required")
    if not revoker:
        raise HTTPException(status_code=400, detail="authority_lease.revoker is required")
    if not challenge_path:
        raise HTTPException(status_code=400, detail="authority_lease.challenge_path is required")
    subject_id = str(lease.get("subject_id") or expected_subject).strip()
    if subject_id != expected_subject:
        raise HTTPException(status_code=400, detail="authority_lease subject does not match actor")
    if not lease_id:
        lease_id = f"sab_lease_{_hash_json(lease)[:16]}"
    return {
        "lease_id": lease_id,
        "subject_id": subject_id,
        "purpose": str(lease.get("purpose") or purpose),
        "scope": scope,
        "expires_at": expires_at,
        "revoker": revoker,
        "challenge_path": challenge_path,
        "lease_json": _json_dumps(lease),
    }


def _parse_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ensure_not_expired(value: str, detail: str) -> None:
    if _parse_datetime(value) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail=detail)


def _upsert_authority_lease(conn: sqlite3.Connection, lease: Dict[str, str], subject_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO sab_authority_leases_v1
            (
                lease_id, subject_id, purpose, scope, expires_at, revoker,
                challenge_path, lease_json, status, created_at, updated_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        ON CONFLICT(lease_id) DO UPDATE SET
            subject_id = excluded.subject_id,
            purpose = excluded.purpose,
            scope = excluded.scope,
            expires_at = excluded.expires_at,
            revoker = excluded.revoker,
            challenge_path = excluded.challenge_path,
            lease_json = excluded.lease_json,
            updated_at = excluded.updated_at
        """,
        (
            lease["lease_id"],
            subject_id,
            lease["purpose"],
            lease["scope"],
            lease["expires_at"],
            lease["revoker"],
            lease["challenge_path"],
            lease["lease_json"],
            now,
            now,
        ),
    )


def _challenge_window_closes_at(packet: Dict[str, Any], created_at: str) -> str:
    plan = packet.get("challenge_plan") if isinstance(packet.get("challenge_plan"), dict) else {}
    window = str(plan.get("challenge_window") or "P7D")
    start = _parse_datetime(created_at)
    duration = timedelta(days=7)
    compact = window.strip().upper()
    try:
        if compact.startswith("P") and compact.endswith("D"):
            duration = timedelta(days=int(compact[1:-1]))
        elif compact.endswith("D"):
            duration = timedelta(days=int(compact[:-1]))
        elif compact.endswith("H"):
            duration = timedelta(hours=int(compact[:-1].replace("PT", "")))
    except ValueError:
        duration = timedelta(days=7)
    return (start + duration).isoformat()


def _seed_submit_message(
    *,
    seed_packet_hash: str,
    claimant_identity: str,
    authority_lease_id: str,
    created_at: str,
) -> Dict[str, str]:
    return {
        "kind": "sab_seed_submit",
        "seed_packet_sha256": seed_packet_hash,
        "claimant_identity": claimant_identity,
        "authority_lease_id": authority_lease_id,
        "created_at": created_at,
    }


def _challenge_submit_message(
    *,
    target_seed_id: str,
    target_claim_id: str,
    challenge_packet_hash: str,
    challenger_identity: str,
    created_at: str,
) -> Dict[str, str]:
    return {
        "kind": "sab_challenge_submit",
        "target_seed_id": target_seed_id,
        "target_claim_id": target_claim_id,
        "challenge_packet_sha256": challenge_packet_hash,
        "challenger_identity": challenger_identity,
        "created_at": created_at,
    }


def _challenge_response_message(
    *,
    challenge_id: str,
    responder_identity: str,
    response_body: str,
) -> Dict[str, str]:
    return {
        "kind": "sab_challenge_response",
        "challenge_id": challenge_id,
        "responder_identity": responder_identity,
        "response_sha256": _sha256_hex(response_body.encode()),
    }


def _witness_event_message(
    *,
    event_type: str,
    subject_type: str,
    subject_id: str,
    payload_hash: str,
    prev_hash: str,
    created_at: str,
) -> Dict[str, str]:
    return {
        "kind": "sab_witness_event",
        "event_type": event_type,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "payload_hash": payload_hash,
        "prev_hash": prev_hash,
        "created_at": created_at,
    }


def _record_signature_use(conn: sqlite3.Connection, signature: str, message_hash: str, actor_identity: str) -> None:
    row = conn.execute(
        "SELECT message_hash FROM sab_signature_index_v1 WHERE signature = ?",
        (signature,),
    ).fetchone()
    if row is not None:
        if str(row["message_hash"]) != message_hash:
            raise HTTPException(status_code=409, detail="signature replayed for different payload")
        return
    conn.execute(
        """
        INSERT INTO sab_signature_index_v1 (signature, message_hash, actor_identity, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (signature, message_hash, actor_identity, datetime.now(timezone.utc).isoformat()),
    )


def _create_spark_projection(
    conn: sqlite3.Connection,
    packet: Dict[str, Any],
    claimant_identity: str,
    seed_id: str,
) -> int:
    claim = packet.get("claim") if isinstance(packet.get("claim"), dict) else {}
    content = str(claim.get("text") or packet.get("title") or seed_id)
    gate_scores = {
        "dimensions": {},
        "composite": 0.0,
        "rv_contraction": None,
        "rv_measurement_state": "not_evaluated",
        "rv_signal": {
            "signal_label": "not_evaluated",
            "warnings": ["v1_seed_projection_not_gate_scored"],
        },
    }
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sparks
            (
                content, content_type, author_id, created_at, gate_scores, status,
                rv_contraction, composite_score, claim_packet_ref,
                artifact_refs_json, red_team_refs_json, witness_refs_json,
                lineage_root_id, parent_spark_id, sublation_status, founding_seed
            )
        VALUES (?, 'text', ?, ?, ?, 'spark', NULL, 0.0, ?, '[]', '[]', '[]', NULL, NULL, 'seed_projection', 0)
        """,
        (
            content,
            claimant_identity,
            datetime.now(timezone.utc).isoformat(),
            _json_dumps(gate_scores),
            seed_id,
        ),
    )
    return int(cursor.lastrowid)


def _seed_row(conn: sqlite3.Connection, seed_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM sab_seed_packets_v1 WHERE seed_id = ?", (seed_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="seed not found")
    return row


def _challenge_row(conn: sqlite3.Connection, challenge_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM sab_challenge_packets_v1 WHERE challenge_id = ?",
        (challenge_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="challenge not found")
    return row


def _standing_row(conn: sqlite3.Connection, standing_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM sab_standing_leases_v1 WHERE standing_id = ?",
        (standing_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="standing not found")
    return row


def _ensure_seed_lease_active(conn: sqlite3.Connection, seed: sqlite3.Row) -> None:
    lease = conn.execute(
        "SELECT expires_at, status FROM sab_authority_leases_v1 WHERE lease_id = ?",
        (str(seed["authority_lease_id"]),),
    ).fetchone()
    if lease is None:
        raise HTTPException(status_code=400, detail="authority lease not found")
    if str(lease["status"]) != "active":
        raise HTTPException(status_code=400, detail="authority lease is not active")
    _ensure_not_expired(str(lease["expires_at"]), "authority lease expired")


def _latest_witness_hash(conn: sqlite3.Connection, chain_scope: str) -> str:
    row = conn.execute(
        """
        SELECT event_hash
        FROM sab_witness_events_v1
        WHERE chain_scope = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (chain_scope,),
    ).fetchone()
    return str(row["event_hash"]) if row is not None else "genesis"


def _append_witness_event(
    conn: sqlite3.Connection,
    *,
    event_type: str,
    actor_identity: str,
    subject_type: str,
    subject_id: str,
    subject_seed_id: Optional[str],
    payload: Dict[str, Any],
    signature_hex: str,
    timestamp: str,
    expected_prev_hash: Optional[str] = None,
) -> Dict[str, Any]:
    chain_scope = subject_seed_id or f"{subject_type}:{subject_id}"
    prev_hash = expected_prev_hash if expected_prev_hash is not None else _latest_witness_hash(conn, chain_scope)
    event_id = f"sab_witness_{secrets.token_hex(12)}"
    payload_json = _json_dumps(payload)
    payload_hash = _sha256_hex(payload_json.encode())
    material = {
        "event_id": event_id,
        "chain_scope": chain_scope,
        "event_type": event_type,
        "actor_identity": actor_identity,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "subject_seed_id": subject_seed_id,
        "timestamp": timestamp,
        "payload_hash": payload_hash,
        "payload_json": payload_json,
        "signature": signature_hex,
        "prev_hash": prev_hash,
    }
    event_hash = _hash_json(material)
    conn.execute(
        """
        INSERT INTO sab_witness_events_v1
            (
                event_id, chain_scope, event_type, actor_identity, subject_type,
                subject_id, subject_seed_id, timestamp, payload_hash,
                payload_json, signature, prev_hash, event_hash
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            chain_scope,
            event_type,
            actor_identity,
            subject_type,
            subject_id,
            subject_seed_id,
            timestamp,
            payload_hash,
            payload_json,
            signature_hex,
            prev_hash,
            event_hash,
        ),
    )
    return {
        "event_id": event_id,
        "event_type": event_type,
        "actor_identity": actor_identity,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "subject_seed_id": subject_seed_id,
        "timestamp": timestamp,
        "payload_hash": payload_hash,
        "payload": payload,
        "signature": signature_hex,
        "prev_hash": prev_hash,
        "hash": event_hash,
        "event_hash": event_hash,
    }


def _record_seed_transition(
    deps: SabSeedingDeps,
    conn: sqlite3.Connection,
    *,
    seed_id: str,
    actor_identity: str,
    event_type: str,
    to_state: str,
    payload: Dict[str, Any],
    signature_hex: str,
    update_state: bool = True,
    precreated_witness: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if to_state not in SEED_STATES:
        raise HTTPException(status_code=400, detail="unsupported seed state")
    row = _seed_row(conn, seed_id)
    from_state = str(row["state"])
    transition_payload = {
        **payload,
        "from_state": from_state,
        "to_state": to_state,
    }
    witness = precreated_witness or _append_witness_event(
        conn,
        event_type=event_type,
        actor_identity=actor_identity,
        subject_type="seed",
        subject_id=seed_id,
        subject_seed_id=seed_id,
        payload=transition_payload,
        signature_hex=signature_hex,
        timestamp=deps.utc_now(),
    )
    seed_event_id = f"sab_seed_event_{secrets.token_hex(10)}"
    conn.execute(
        """
        INSERT INTO sab_seed_events_v1
            (
                event_id, seed_id, actor_identity, event_type, from_state,
                to_state, payload_json, witness_event_id, created_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            seed_event_id,
            seed_id,
            actor_identity,
            event_type,
            from_state,
            to_state,
            _json_dumps(transition_payload),
            witness["event_id"],
            deps.utc_now(),
        ),
    )
    if update_state and from_state != to_state:
        conn.execute(
            """
            UPDATE sab_seed_packets_v1
            SET state = ?, updated_at = ?
            WHERE seed_id = ?
            """,
            (to_state, deps.utc_now(), seed_id),
        )
        _update_spark_projection_state(conn, row["spark_projection_id"], to_state)
    return witness


def _record_standing_event(
    deps: SabSeedingDeps,
    conn: sqlite3.Connection,
    *,
    standing_id: str,
    actor_identity: str,
    event_type: str,
    to_status: str,
    payload: Dict[str, Any],
    signature_hex: str,
) -> Dict[str, Any]:
    if to_status not in STANDING_STATUSES:
        raise HTTPException(status_code=400, detail="unsupported standing status")
    row = _standing_row(conn, standing_id)
    from_status = str(row["status"])
    subject_seed_id = str(row["subject_seed_id"])
    event_payload = {
        **payload,
        "standing_id": standing_id,
        "from_status": from_status,
        "to_status": to_status,
    }
    witness = _append_witness_event(
        conn,
        event_type=event_type,
        actor_identity=actor_identity,
        subject_type="standing",
        subject_id=standing_id,
        subject_seed_id=subject_seed_id,
        payload=event_payload,
        signature_hex=signature_hex,
        timestamp=deps.utc_now(),
    )
    standing_event_id = f"sab_standing_event_{secrets.token_hex(10)}"
    conn.execute(
        """
        INSERT INTO sab_standing_events_v1
            (
                event_id, standing_id, actor_identity, event_type, from_status,
                to_status, payload_json, witness_event_id, created_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            standing_event_id,
            standing_id,
            actor_identity,
            event_type,
            from_status,
            to_status,
            _json_dumps(event_payload),
            witness["event_id"],
            deps.utc_now(),
        ),
    )
    if from_status != to_status:
        conn.execute(
            """
            UPDATE sab_standing_leases_v1
            SET status = ?, updated_at = ?
            WHERE standing_id = ?
            """,
            (to_status, deps.utc_now(), standing_id),
        )
    return witness


def _update_spark_projection_state(conn: sqlite3.Connection, spark_projection_id: Any, seed_state: str) -> None:
    if spark_projection_id is None:
        return
    if seed_state == "canon":
        spark_status = "canon"
    elif seed_state in {"compost", "revoked", "expired"}:
        spark_status = "compost"
    else:
        spark_status = "spark"
    conn.execute("UPDATE sparks SET status = ? WHERE id = ?", (spark_status, spark_projection_id))


def _serialize_seed(conn: sqlite3.Connection, row: sqlite3.Row, *, include_packet: bool = True) -> Dict[str, Any]:
    seed_id = str(row["seed_id"])
    head = _latest_witness_hash(conn, seed_id)
    item = {
        "schema": "sab.seed_packet.v1",
        "seed_id": seed_id,
        "seed_type": str(row["seed_type"]),
        "title": str(row["title"]),
        "claim_id": str(row["claim_id"]),
        "claimant_identity": str(row["claimant_identity"]),
        "authority_lease_id": str(row["authority_lease_id"]),
        "state": str(row["state"]),
        "packet_hash": str(row["packet_hash"]),
        "spark_projection_id": row["spark_projection_id"],
        "challenge_window_closes_at": row["challenge_window_closes_at"],
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
        "witness_head": head,
    }
    if include_packet:
        item["seed_packet"] = json.loads(str(row["packet_json"]))
    return item


def _serialize_challenge(row: sqlite3.Row) -> Dict[str, Any]:
    response_raw = row["response_json"]
    return {
        "challenge_id": str(row["challenge_id"]),
        "target_seed_id": str(row["target_seed_id"]),
        "target_claim_id": str(row["target_claim_id"]),
        "challenger_identity": str(row["challenger_identity"]),
        "status": str(row["status"]),
        "packet_hash": str(row["packet_hash"]),
        "challenge_packet": json.loads(str(row["packet_json"])),
        "response": json.loads(str(response_raw)) if response_raw else None,
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


def _serialize_witness_event(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "event_id": str(row["event_id"]),
        "event_type": str(row["event_type"]),
        "actor_identity": str(row["actor_identity"]),
        "subject_type": str(row["subject_type"]),
        "subject_id": str(row["subject_id"]),
        "subject_seed_id": row["subject_seed_id"],
        "timestamp": str(row["timestamp"]),
        "payload_hash": str(row["payload_hash"]),
        "payload": json.loads(str(row["payload_json"])),
        "signature": str(row["signature"]),
        "prev_hash": str(row["prev_hash"]),
        "hash": str(row["event_hash"]),
        "event_hash": str(row["event_hash"]),
    }


def _serialize_standing(row: sqlite3.Row, *, include_lease: bool = True) -> Dict[str, Any]:
    item = {
        "standing_id": str(row["standing_id"]),
        "subject_seed_id": str(row["subject_seed_id"]),
        "subject_claim_id": str(row["subject_claim_id"]),
        "scope": str(row["scope"]),
        "purpose": str(row["purpose"]),
        "status": str(row["status"]),
        "lease_hash": str(row["lease_hash"]),
        "expiry": str(row["expiry"]),
        "revoker": str(row["revoker"]),
        "challenge_path": str(row["challenge_path"]),
        "issued_by": str(row["issued_by"]),
        "issued_at": str(row["issued_at"]),
        "updated_at": str(row["updated_at"]),
    }
    if include_lease:
        item["standing_lease"] = json.loads(str(row["lease_json"]))
    return item


def _seed_chain(conn: sqlite3.Connection, seed_id: str) -> Dict[str, Any]:
    rows = _witness_rows(conn, seed_id=seed_id, subject_type=None, subject_id=None, limit=10000)
    return {
        "seed_id": seed_id,
        "verified": _verify_witness_rows(rows),
        "head": str(rows[-1]["event_hash"]) if rows else "genesis",
        "entries": [_serialize_witness_event(row) for row in rows],
        "events": [_serialize_witness_event(row) for row in rows],
        "state_events": [
            dict(row)
            for row in conn.execute(
                """
                SELECT event_id, seed_id, actor_identity, event_type, from_state,
                       to_state, payload_json, witness_event_id, created_at
                FROM sab_seed_events_v1
                WHERE seed_id = ?
                ORDER BY id ASC
                """,
                (seed_id,),
            ).fetchall()
        ],
    }


def _witness_rows(
    conn: sqlite3.Connection,
    *,
    seed_id: Optional[str],
    subject_type: Optional[str],
    subject_id: Optional[str],
    limit: int,
) -> List[sqlite3.Row]:
    clauses: List[str] = []
    params: List[Any] = []
    if seed_id:
        clauses.append("subject_seed_id = ?")
        params.append(seed_id)
    if subject_type:
        clauses.append("subject_type = ?")
        params.append(subject_type)
    if subject_id:
        clauses.append("subject_id = ?")
        params.append(subject_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return conn.execute(
        f"""
        SELECT *
        FROM sab_witness_events_v1
        {where}
        ORDER BY chain_scope ASC, id ASC
        LIMIT ?
        """,  # nosec B608 - where only contains fixed clauses.
        (*params, limit),
    ).fetchall()


def _verify_witness_rows(rows: List[sqlite3.Row]) -> bool:
    heads: Dict[str, str] = {}
    for row in rows:
        chain_scope = str(row["chain_scope"])
        expected_prev = heads.get(chain_scope, "genesis")
        material = {
            "event_id": row["event_id"],
            "chain_scope": row["chain_scope"],
            "event_type": row["event_type"],
            "actor_identity": row["actor_identity"],
            "subject_type": row["subject_type"],
            "subject_id": row["subject_id"],
            "subject_seed_id": row["subject_seed_id"],
            "timestamp": row["timestamp"],
            "payload_hash": row["payload_hash"],
            "payload_json": row["payload_json"],
            "signature": row["signature"],
            "prev_hash": row["prev_hash"],
        }
        if str(row["prev_hash"]) != expected_prev:
            return False
        if str(row["event_hash"]) != _hash_json(material):
            return False
        heads[chain_scope] = str(row["event_hash"])
    return True


def _subject_seed_id(conn: sqlite3.Connection, subject_type: str, subject_id: str) -> Optional[str]:
    if subject_type == "seed":
        _seed_row(conn, subject_id)
        return subject_id
    if subject_type == "challenge":
        return str(_challenge_row(conn, subject_id)["target_seed_id"])
    if subject_type == "standing":
        return str(_standing_row(conn, subject_id)["subject_seed_id"])
    if subject_type == "claim":
        row = conn.execute(
            "SELECT seed_id FROM sab_seed_packets_v1 WHERE claim_id = ? ORDER BY id DESC LIMIT 1",
            (subject_id,),
        ).fetchone()
        return str(row["seed_id"]) if row is not None else None
    if subject_type == "authority_lease":
        return None
    raise HTTPException(status_code=400, detail="unsupported subject_type")


def _state_for_witness_event(event_type: str) -> Optional[str]:
    return {
        "affirm": "witnessed",
        "refuse": "challenged",
        "response": "corrected",
        "correction": "corrected",
        "standing_issued": "standing_active",
        "revoked": "revoked",
        "expired": "expired",
        "canon": "canon",
        "compost": "compost",
    }.get(event_type)


def _resolve_challenge_action(
    deps: SabSeedingDeps,
    challenge_id: str,
    payload: Dict[str, Any],
    *,
    action: str,
    challenge_status: str,
    seed_state: str,
) -> Dict[str, Any]:
    deps.init_db()
    with deps.db() as conn:
        _init_v1_tables(conn)
        challenge = _challenge_row(conn, challenge_id)
        seed_id = str(challenge["target_seed_id"])
        seed = _seed_row(conn, seed_id)
        _ensure_seed_lease_active(conn, seed)
        actor_identity = str(
            payload.get("actor_identity")
            or payload.get("responder_identity")
            or payload.get("reviewer_identity")
            or ""
        ).strip()
        if not actor_identity:
            raise HTTPException(status_code=400, detail="actor_identity is required")
        created_at = str(payload.get("created_at") or datetime.now(timezone.utc).isoformat()).strip()
        body = payload.get("response") if action == "respond" else payload.get("reason")
        if body is None and action == "respond":
            body = payload.get("correction")
        body_payload = body if isinstance(body, dict) else {"value": str(body or "")}
        signature_hex = _required_str(payload, "signature")
        signature_signer = _signature_signer(payload) or _identity_ref_subject(conn, actor_identity) or actor_identity
        body_hash = _hash_json(body_payload)
        message = {
            "kind": f"sab_challenge_{action}",
            "challenge_id": challenge_id,
            "actor_identity": actor_identity,
            "payload_sha256": body_hash,
            "created_at": created_at,
        }
        if not _verify_signature_with_fallback(deps, conn, signature_signer, message, signature_hex):
            legacy_message = _challenge_response_message(
                challenge_id=challenge_id,
                responder_identity=actor_identity,
                response_body=str(body or ""),
            )
            deps.verify_agent_signature(conn, signature_signer, _canonical_bytes(legacy_message), signature_hex)
            message = legacy_message
        _record_signature_use(conn, signature_hex, _hash_json(message), signature_signer)
        conn.execute(
            """
            UPDATE sab_challenge_packets_v1
            SET status = ?, response_json = ?, updated_at = ?
            WHERE challenge_id = ?
            """,
            (challenge_status, _json_dumps(body_payload), deps.utc_now(), challenge_id),
        )
        witness = _record_seed_transition(
            deps,
            conn,
            seed_id=seed_id,
            actor_identity=actor_identity,
            event_type="response" if action == "respond" else ("compost" if action == "sustain" else "challenge"),
            to_state=seed_state,
            payload={"challenge_id": challenge_id, "action": action, "payload_hash": body_hash, "payload": body_payload},
            signature_hex=signature_hex,
        )
        deps.invalidate_web_cache()
        return {
            "challenge_id": challenge_id,
            "challenge": _serialize_challenge(_challenge_row(conn, challenge_id)),
            "response_id": witness["event_id"],
            "state": seed_state,
            "seed_id": seed_id,
            "seed_state": seed_state,
            "witness_head": witness["hash"],
        }


def _review_standing_request(
    deps: SabSeedingDeps,
    conn: sqlite3.Connection,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    subject_seed_id = _required_str(payload, "subject_seed_id")
    seed = _seed_row(conn, subject_seed_id)
    if _pending_challenge_count(conn, subject_seed_id) > 0:
        raise HTTPException(status_code=409, detail="standing review requires resolved challenge path")
    if _challenge_count(conn, subject_seed_id) < 1:
        raise HTTPException(status_code=409, detail="standing review requires a challenge")
    witness_refs = payload.get("witness_refs") if isinstance(payload.get("witness_refs"), list) else []
    if not witness_refs:
        raise HTTPException(status_code=409, detail="standing review requires witness refs")

    requested = str(payload.get("requested_state") or "provisional").strip()
    if requested in {"compost", "rejected"}:
        event_type = "compost"
        state = "compost"
        system_payload = {"standing_review": "compost", "reason": payload.get("reason") or "review rejected"}
    else:
        event_type = "standing_issued"
        state = "standing_active"
        system_payload = {
            "standing_review": "provisional",
            "scope": str(payload.get("scope") or seed["claim_id"]),
            "challenge_summary": payload.get("challenge_summary") if isinstance(payload.get("challenge_summary"), list) else [],
            "witness_refs": witness_refs,
        }
    signature = deps.system_sign(
        {
            "kind": "sab_standing_review",
            "subject_seed_id": subject_seed_id,
            "state": state,
            "payload": system_payload,
        }
    )
    witness = _record_seed_transition(
        deps,
        conn,
        seed_id=subject_seed_id,
        actor_identity="system",
        event_type=event_type,
        to_state=state,
        payload=system_payload,
        signature_hex=signature,
    )
    deps.invalidate_web_cache()
    return {
        "state": state,
        "seed_id": subject_seed_id,
        "subject_seed_id": subject_seed_id,
        "witness_head": witness["hash"],
    }


def _challenge_count(conn: sqlite3.Connection, seed_id: str) -> int:
    return int(
        conn.execute(
            "SELECT COUNT(*) AS c FROM sab_challenge_packets_v1 WHERE target_seed_id = ?",
            (seed_id,),
        ).fetchone()["c"]
    )


def _pending_challenge_count(conn: sqlite3.Connection, seed_id: str) -> int:
    return int(
        conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM sab_challenge_packets_v1
            WHERE target_seed_id = ? AND status = 'pending'
            """,
            (seed_id,),
        ).fetchone()["c"]
    )


def _seed_witness_count(conn: sqlite3.Connection, seed_id: str) -> int:
    return int(
        conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM sab_witness_events_v1
            WHERE subject_seed_id = ? AND event_type IN ('affirm', 'refuse', 'response', 'correction')
            """,
            (seed_id,),
        ).fetchone()["c"]
    )


def _validate_standing_lease(lease: Dict[str, Any]) -> None:
    for key in ("scope", "purpose", "revoker", "challenge_path"):
        if not str(lease.get(key) or "").strip():
            raise HTTPException(status_code=400, detail=f"standing lease {key} is required")
    if not _standing_expiry(lease):
        raise HTTPException(status_code=400, detail="standing lease expiry is required")


def _standing_expiry(lease: Dict[str, Any]) -> str:
    return str(lease.get("expiry") or lease.get("expires_at") or "").strip()


def _expire_standing_if_needed(
    deps: SabSeedingDeps,
    conn: sqlite3.Connection,
    row: sqlite3.Row,
) -> sqlite3.Row:
    status_value = str(row["status"])
    if status_value in {"revoked", "expired", "compost"}:
        return row
    if _parse_datetime(str(row["expiry"])) > datetime.now(timezone.utc):
        return row
    signature = deps.system_sign(
        {
            "kind": "sab_standing_expired",
            "standing_id": str(row["standing_id"]),
            "expiry": str(row["expiry"]),
        }
    )
    event = _record_standing_event(
        deps,
        conn,
        standing_id=str(row["standing_id"]),
        actor_identity="system",
        event_type="expired",
        to_status="expired",
        payload={"expiry": str(row["expiry"])},
        signature_hex=signature,
    )
    _record_seed_transition(
        deps,
        conn,
        seed_id=str(row["subject_seed_id"]),
        actor_identity="system",
        event_type="expired",
        to_state="expired",
        payload={"standing_id": str(row["standing_id"])},
        signature_hex=signature,
        precreated_witness=event,
    )
    return _standing_row(conn, str(row["standing_id"]))


def _standing_action(
    deps: SabSeedingDeps,
    standing_id: str,
    payload: Dict[str, Any],
    *,
    action: str,
    to_status: str,
    seed_state: str,
) -> Dict[str, Any]:
    deps.init_db()
    with deps.db() as conn:
        _init_v1_tables(conn)
        standing = _expire_standing_if_needed(deps, conn, _standing_row(conn, standing_id))
        current_status = str(standing["status"])
        if current_status == "revoked":
            raise HTTPException(status_code=409, detail="standing is revoked")
        if current_status == "expired":
            raise HTTPException(status_code=409, detail="standing is expired")
        actor_identity = _required_str(payload, "actor_identity")
        if action == "revoke":
            revoker = str(standing["revoker"])
            issued_by = str(standing["issued_by"])
            if actor_identity not in {revoker, issued_by}:
                raise HTTPException(status_code=403, detail="actor is not standing revoker")
        created_at = _required_str(payload, "created_at")
        evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
        reason = str(payload.get("reason") or "")
        action_payload = {"reason": reason, "evidence": evidence}
        signature_hex = _required_str(payload, "signature")
        message = {
            "kind": f"sab_standing_{action}",
            "standing_id": standing_id,
            "actor_identity": actor_identity,
            "payload_sha256": _hash_json(action_payload),
            "created_at": created_at,
        }
        deps.verify_agent_signature(conn, actor_identity, _canonical_bytes(message), signature_hex)
        _record_signature_use(conn, signature_hex, _hash_json(message), actor_identity)
        event_type = {
            "challenge": "challenge",
            "revoke": "revoked",
            "revalidate": "canon" if to_status == "canon" else "standing_issued",
        }[action]
        event = _record_standing_event(
            deps,
            conn,
            standing_id=standing_id,
            actor_identity=actor_identity,
            event_type=event_type,
            to_status=to_status,
            payload=action_payload,
            signature_hex=signature_hex,
        )
        _record_seed_transition(
            deps,
            conn,
            seed_id=str(standing["subject_seed_id"]),
            actor_identity=actor_identity,
            event_type=event_type,
            to_state=seed_state,
            payload={"standing_id": standing_id, **action_payload},
            signature_hex=signature_hex,
            precreated_witness=event,
        )
        deps.invalidate_web_cache()
        return {
            "standing": _serialize_standing(_standing_row(conn, standing_id)),
            "seed_id": str(standing["subject_seed_id"]),
            "seed_state": seed_state,
            "witness_head": event["hash"],
        }
