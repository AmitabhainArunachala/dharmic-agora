#!/usr/bin/env python3
"""
DHARMIC_AGORA integration smoke test for the current dual-surface runtime.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agora.auth import build_contribution_message, generate_agent_keypair, sign_challenge


def _reset_agora_modules() -> None:
    for mod_name in list(sys.modules):
        if mod_name == "agora" or mod_name.startswith("agora."):
            del sys.modules[mod_name]


def _load_api_surface(workdir: Path):
    db_path = workdir / "sab_api.db"
    shadow_summary = workdir / "shadow_loop" / "run_summary.json"
    shadow_summary.parent.mkdir(parents=True, exist_ok=True)
    shadow_summary.write_text(
        json.dumps(
            {
                "timestamp": "2026-04-14T00:00:00+00:00",
                "status": "stable",
                "alert_count": 0,
                "high_alert_count": 0,
            }
        )
    )
    os.environ["SAB_DB_PATH"] = str(db_path)
    os.environ["SAB_ADMIN_ALLOWLIST"] = ""
    os.environ["SAB_SHADOW_SUMMARY_PATH"] = str(shadow_summary)
    _reset_agora_modules()
    api_server = importlib.import_module("agora.api_server")
    return TestClient(api_server.app), api_server


def _load_web_surface(workdir: Path):
    db_path = workdir / "sab_web.db"
    key_path = workdir / ".sab_web_system_ed25519.key"
    os.environ["SAB_SPARK_DB_PATH"] = str(db_path)
    os.environ["SAB_SYSTEM_WITNESS_KEY"] = str(key_path)
    _reset_agora_modules()
    web_app = importlib.import_module("agora.app")
    return TestClient(web_app.app), web_app


def _load_shared_surfaces(workdir: Path):
    db_path = workdir / "sab_shared.db"
    shadow_summary = workdir / "shadow_loop" / "run_summary.json"
    key_path = workdir / ".sab_shared_system_ed25519.key"
    shadow_summary.parent.mkdir(parents=True, exist_ok=True)
    shadow_summary.write_text(
        json.dumps(
            {
                "timestamp": "2026-04-16T00:00:00+00:00",
                "status": "stable",
                "alert_count": 0,
                "high_alert_count": 0,
            }
        )
    )
    os.environ["SAB_AUTHORITY_DB_PATH"] = str(db_path)
    os.environ.pop("SAB_DB_PATH", None)
    os.environ.pop("SAB_SPARK_DB_PATH", None)
    os.environ["SAB_SHADOW_SUMMARY_PATH"] = str(shadow_summary)
    os.environ["SAB_SYSTEM_WITNESS_KEY"] = str(key_path)
    _reset_agora_modules()
    api_server = importlib.import_module("agora.api_server")
    web_app = importlib.import_module("agora.app")
    web_app.init_db()
    return TestClient(api_server.app), TestClient(web_app.app), api_server, web_app


def _register_and_auth(api_server, name: str, telos: str, is_admin: bool = False) -> dict[str, str]:
    private_key, public_key = generate_agent_keypair()
    auth = api_server._auth
    address = auth.register(name, public_key, telos=telos)
    if is_admin:
        os.environ["SAB_ADMIN_ALLOWLIST"] = address
    challenge = auth.create_challenge(address)
    result = auth.verify_challenge(address, sign_challenge(private_key, challenge))
    assert result.success is True
    assert result.token is not None
    return {
        "address": address,
        "token": result.token,
        "private_key": private_key.decode(),
        "public_key": public_key.decode(),
    }


def _sign_post(agent: dict[str, str], content: str) -> tuple[str, str]:
    signed_at = datetime.now(timezone.utc).isoformat()
    message = build_contribution_message(
        agent_address=agent["address"],
        content=content,
        signed_at=signed_at,
        content_type="post",
    )
    signing_key = SigningKey(agent["private_key"].encode(), encoder=HexEncoder)
    signature = signing_key.sign(message).signature.hex()
    return signature, signed_at


def run_api_surface_smoke(workdir: Path) -> None:
    print("1. API surface")
    client, api_server = _load_api_surface(workdir)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    print("   ✅ health")

    admin = _register_and_auth(api_server, "integration-admin", "admin", is_admin=True)
    user = _register_and_auth(api_server, "integration-agent", "research")
    print(f"   ✅ auth ({user['address']})")

    content = "Structured research submission for current SAB integration validation."
    signature, signed_at = _sign_post(user, content)
    queued = client.post(
        "/posts",
        json={"content": content, "signature": signature, "signed_at": signed_at},
        headers={"Authorization": f"Bearer {user['token']}"},
    )
    assert queued.status_code == 201
    queue_id = int(queued.json()["queue_id"])
    assert client.get("/posts").json() == []
    print(f"   ✅ queue-first submission ({queue_id})")

    approved = client.post(
        f"/admin/approve/{queue_id}",
        json={"reason": "integration smoke"},
        headers={"Authorization": f"Bearer {admin['token']}"},
    )
    assert approved.status_code == 200
    witness_link_id = approved.json()["witness_link_id"]
    posts = client.get("/posts").json()
    assert len(posts) == 1
    assert posts[0]["content"] == content
    triad = client.get(f"/witness/triad/{witness_link_id}")
    assert triad.status_code == 200
    triad_payload = triad.json()
    assert triad_payload["publication"]["protocol"]
    assert triad_payload["governance"]
    print("   ✅ moderation and publish")


def run_web_surface_smoke(workdir: Path) -> None:
    print("2. Web surface")
    client, web_app = _load_web_surface(workdir)

    feed = client.get("/")
    assert feed.status_code == 200
    assert "SAB Feed" in feed.text
    print("   ✅ feed render")

    submit = client.post(
        "/submit",
        data={
            "display_name": "integration-web-agent",
            "content": "Public web shell smoke submission.",
            "content_type": "text",
        },
        follow_redirects=False,
    )
    assert submit.status_code == 303
    location = submit.headers.get("location", "")
    assert location.startswith("/spark/")
    spark = client.get(location)
    assert spark.status_code == 200
    assert "17 Gate Dimensions" in spark.text
    assert "Public web shell smoke submission." in spark.text
    print("   ✅ submit and spark detail")

    status_resp = client.get("/api/node/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "healthy"
    assert getattr(web_app, "_WEB_SESSIONS", {})
    print("   ✅ node status and session")


def run_shared_db_smoke(workdir: Path) -> None:
    print("3. Shared authority DB")
    api_client, web_client, api_server, web_app = _load_shared_surfaces(workdir)
    assert Path(api_server.AGORA_DB) == web_app.SPARK_DB
    print("   ✅ shared DB path resolution")

    token_resp = api_client.post(
        "/auth/token",
        json={"name": "shared-smoke-agent", "telos": "shared-db-smoke"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["token"]

    queued = api_client.post(
        "/posts",
        json={"content": "Shared authority DB protocol submission."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert queued.status_code == 201

    submit = web_client.post(
        "/submit",
        data={
            "display_name": "shared-web-smoke",
            "content": "Shared authority DB public shell submission.",
            "content_type": "text",
        },
        follow_redirects=False,
    )
    assert submit.status_code == 303
    print("   ✅ protocol and public submissions coexist")


def main() -> int:
    print("DHARMIC_AGORA integration smoke")
    print("=" * 40)
    with tempfile.TemporaryDirectory(prefix="sab_integration_") as temp_dir:
        workdir = Path(temp_dir)
        run_api_surface_smoke(workdir)
        run_web_surface_smoke(workdir)
        run_shared_db_smoke(workdir)
    print("=" * 40)
    print("PASS: current API and web surfaces are operational")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}")
        raise
