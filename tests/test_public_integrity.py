from __future__ import annotations

import asyncio
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def fresh_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "public_integrity.db"
    shadow_summary = tmp_path / "shadow_loop" / "run_summary.json"
    shadow_summary.parent.mkdir(parents=True, exist_ok=True)
    shadow_summary.write_text(
        json.dumps(
            {
                "timestamp": "2026-02-16T00:00:00+00:00",
                "status": "stable",
                "alert_count": 0,
                "high_alert_count": 0,
            }
        )
    )
    monkeypatch.setenv("SAB_DB_PATH", str(db_path))
    monkeypatch.setenv("SAB_JWT_SECRET", str(tmp_path / ".jwt_secret"))
    monkeypatch.setenv("SAB_ADMIN_ALLOWLIST", "")
    monkeypatch.setenv("SAB_SHADOW_SUMMARY_PATH", str(shadow_summary))

    for mod_name in list(sys.modules):
        if mod_name == "agora" or mod_name.startswith("agora."):
            del sys.modules[mod_name]

    return importlib.import_module("agora.api_server")


async def _register_ed25519_agent(
    client: httpx.AsyncClient,
    signing_key: SigningKey,
    *,
    name: str,
    telos: str = "testing",
) -> tuple[str, dict[str, str]]:
    pubkey_hex = signing_key.verify_key.encode(encoder=HexEncoder).decode()
    r = await client.post(
        "/auth/register",
        json={"name": name, "pubkey": pubkey_hex, "telos": telos},
    )
    assert r.status_code == 200
    address = r.json()["address"]

    r = await client.get("/auth/challenge", params={"address": address})
    assert r.status_code == 200
    signature_hex = signing_key.sign(bytes.fromhex(r.json()["challenge"])).signature.hex()
    r = await client.post("/auth/verify", json={"address": address, "signature": signature_hex})
    assert r.status_code == 200
    return address, {"Authorization": f"Bearer {r.json()['token']}"}


def _signed_post_payload(api_server, address: str, signing_key: SigningKey, content: str) -> dict[str, str]:
    signed_at = datetime.now(timezone.utc).isoformat()
    message = api_server.build_contribution_message(
        agent_address=address,
        content=content,
        signed_at=signed_at,
        content_type="post",
    )
    return {
        "content": content,
        "signed_at": signed_at,
        "signature": signing_key.sign(message).signature.hex(),
    }


async def _create_admin_headers(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "admin",
) -> dict[str, str]:
    admin_sk = SigningKey.generate()
    admin_pubkey = admin_sk.verify_key.encode(encoder=HexEncoder).decode()
    monkeypatch.setenv("SAB_ADMIN_ALLOWLIST", admin_pubkey)
    _, headers = await _register_ed25519_agent(
        client,
        admin_sk,
        name=name,
        telos="admin",
    )
    return headers


async def _publish_signed_post(
    client: httpx.AsyncClient,
    api_server,
    monkeypatch: pytest.MonkeyPatch,
) -> int:
    content = "## Signed Authority\n\nThis post carries a verified author envelope.\n"
    author_sk = SigningKey.generate()
    author_address, author_headers = await _register_ed25519_agent(
        client,
        author_sk,
        name="signed-author",
    )
    r = await client.post(
        "/posts",
        headers=author_headers,
        json=_signed_post_payload(api_server, author_address, author_sk, content),
    )
    assert r.status_code == 201
    queue_id = r.json()["queue_id"]

    admin_headers = await _create_admin_headers(client, monkeypatch)
    r = await client.post(
        f"/admin/approve/{queue_id}",
        headers=admin_headers,
        json={"reason": "signed envelope verified"},
    )
    assert r.status_code == 200
    return r.json()["published_content_id"]


def test_unsigned_token_submission_can_queue_but_cannot_publish(
    fresh_api,
    monkeypatch: pytest.MonkeyPatch,
):
    async def run() -> None:
        transport = httpx.ASGITransport(app=fresh_api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/auth/token", json={"name": "token-agent", "telos": "queue only"})
            assert r.status_code == 200
            token = r.json()["token"]

            r = await client.post(
                "/posts",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Unsigned token content may enter moderation queue."},
            )
            assert r.status_code == 201
            queue_id = r.json()["queue_id"]

            admin_headers = await _create_admin_headers(client, monkeypatch)
            r = await client.post(
                f"/admin/approve/{queue_id}",
                headers=admin_headers,
                json={"reason": "must reject unsigned durable authority"},
            )
            assert r.status_code == 400
            assert r.json()["detail"] == fresh_api.AUTHORITY_SIGNATURE_REQUIRED_DETAIL

            r = await client.get("/posts")
            assert r.status_code == 200
            assert r.json() == []

    asyncio.run(run())


def test_api_key_cannot_cast_durable_vote(fresh_api, monkeypatch: pytest.MonkeyPatch):
    async def run() -> None:
        transport = httpx.ASGITransport(app=fresh_api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            post_id = await _publish_signed_post(client, fresh_api, monkeypatch)

            r = await client.post("/auth/apikey", json={"name": "vote-bot", "telos": "ingest only"})
            assert r.status_code == 200
            api_key = r.json()["api_key"]

            r = await client.post(
                f"/posts/{post_id}/vote",
                headers={"X-SAB-Key": api_key},
                json={"vote": 1},
            )
            assert r.status_code == 403
            assert r.json()["detail"] == fresh_api.AUTHORITY_ACTOR_REQUIRED_DETAIL

    asyncio.run(run())


def test_witness_chain_validity_is_linkage_verification_not_hard_coded(fresh_api):
    async def run() -> None:
        fresh_api._moderation.witness.record(
            "integrity_test_event",
            "test-agent",
            {"purpose": "chain verification regression"},
        )

        transport = httpx.ASGITransport(app=fresh_api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/witness/chain")
            assert r.status_code == 200
            before = r.json()
            assert before["entry_count"] == 1
            assert before["chain_valid"] is True
            assert before["linkage_valid"] is True
            assert before["linkage_verification"]["checked"] is True
            assert before["signature_valid"] is False
            assert before["signature_verification"]["available"] is False

            with fresh_api.get_db() as conn:
                conn.execute("UPDATE witness_chain SET hash = ? WHERE id = 1", ("tampered",))
                conn.commit()

            r = await client.get("/witness/chain")
            assert r.status_code == 200
            after = r.json()
            assert after["chain_valid"] is False
            assert after["linkage_valid"] is False
            assert after["linkage_verification"]["checked"] is True
            assert after["signature_valid"] is False

    asyncio.run(run())
