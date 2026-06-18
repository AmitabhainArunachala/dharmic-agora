from __future__ import annotations

import importlib
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _reset_agora_modules() -> None:
    for mod_name in list(sys.modules):
        if mod_name == "agora" or mod_name.startswith("agora."):
            del sys.modules[mod_name]


def test_runtime_surfaces_can_share_authority_db(tmp_path, monkeypatch):
    shared_db = tmp_path / "sab_authority.db"
    shadow_summary = tmp_path / "shadow_loop" / "run_summary.json"
    shadow_summary.parent.mkdir(parents=True, exist_ok=True)
    shadow_summary.write_text(
        '{"timestamp":"2026-04-15T00:00:00+00:00","status":"stable","alert_count":0,"high_alert_count":0}'
    )

    monkeypatch.setenv("SAB_AUTHORITY_DB_PATH", str(shared_db))
    monkeypatch.delenv("SAB_DB_PATH", raising=False)
    monkeypatch.delenv("SAB_SPARK_DB_PATH", raising=False)
    monkeypatch.setenv("SAB_SHADOW_SUMMARY_PATH", str(shadow_summary))

    _reset_agora_modules()
    api_server = importlib.import_module("agora.api_server")
    web_app = importlib.import_module("agora.app")

    assert Path(api_server.AGORA_DB) == shared_db
    assert web_app.SPARK_DB == shared_db
