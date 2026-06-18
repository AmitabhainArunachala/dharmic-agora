"""
SAB Witness Chain

Hash-chained audit log for tamper-evident moderation decisions and system actions.

WITNESS LAYER BOUNDARY:
- This module is the SABP witness (publication provenance): queue decisions,
  moderation transitions, and runtime/admin actions in the API layer.
- Artifact derivation provenance is intentionally separate and lives in
  `agent_core/core/witness_event.py`.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .config import get_db_path
    from .witness_service import (
        PUBLICATION_WITNESS_DOMAIN,
        attach_witness_meta,
        decode_related_link_ids,
        encode_related_link_ids,
    )
except ImportError:  # Allow running as script
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from agora.config import get_db_path
    from agora.witness_service import (
        PUBLICATION_WITNESS_DOMAIN,
        attach_witness_meta,
        decode_related_link_ids,
        encode_related_link_ids,
    )


class WitnessChain:
    """Hash-chained audit log. Every entry references the previous hash."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        def ensure_column(table: str, column_name: str, column_def: str) -> None:
            cursor.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in cursor.fetchall()}
            if column_name not in existing:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS witness_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                agent_address TEXT,
                content_id TEXT,
                details TEXT NOT NULL,
                witness_domain TEXT NOT NULL DEFAULT 'publication',
                witness_link_id TEXT,
                related_link_ids_json TEXT NOT NULL DEFAULT '[]',
                prev_hash TEXT,
                hash TEXT NOT NULL
            )
            """
        )
        ensure_column("witness_chain", "witness_domain", "witness_domain TEXT DEFAULT 'publication'")
        ensure_column("witness_chain", "witness_link_id", "witness_link_id TEXT")
        ensure_column(
            "witness_chain",
            "related_link_ids_json",
            "related_link_ids_json TEXT NOT NULL DEFAULT '[]'",
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_witness_content ON witness_chain(content_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_witness_action ON witness_chain(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_witness_link ON witness_chain(witness_link_id)")
        conn.commit()
        conn.close()

    def _get_last_hash(self, cursor: sqlite3.Cursor) -> Optional[str]:
        cursor.execute("SELECT hash FROM witness_chain ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None

    def record(
        self,
        action: str,
        agent_id: str,
        details: Dict[str, Any],
        content_id: Optional[str] = None,
        *,
        witness_domain: str = PUBLICATION_WITNESS_DOMAIN,
        witness_link_id: Optional[str] = None,
        related_link_ids: Optional[List[str]] = None,
        subject_type: Optional[str] = None,
        subject_id: Optional[Any] = None,
        origin: str = "agora.witness",
    ) -> Dict[str, Any]:
        witness_link_id, details_with_meta, normalized_related = attach_witness_meta(
            details,
            domain=witness_domain,
            action=action,
            actor_id=agent_id,
            subject_type=subject_type or "content",
            subject_id=subject_id if subject_id is not None else content_id,
            origin=origin,
            witness_link_id=witness_link_id,
            related_link_ids=related_link_ids,
        )
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "agent_id": agent_id,
            "details": details_with_meta,
            "prev_hash": None,
            "content_id": content_id,
            "witness_domain": witness_domain,
            "witness_link_id": witness_link_id,
            "related_link_ids_json": encode_related_link_ids(normalized_related),
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        prev_hash = self._get_last_hash(cursor)
        entry["prev_hash"] = prev_hash

        entry_bytes = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()
        entry_hash = hashlib.sha256(entry_bytes).hexdigest()
        entry["hash"] = entry_hash

        cursor.execute(
            """
            INSERT INTO witness_chain (
                timestamp,
                action,
                agent_address,
                content_id,
                details,
                witness_domain,
                witness_link_id,
                related_link_ids_json,
                prev_hash,
                hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry["timestamp"],
                entry["action"],
                entry["agent_id"],
                entry["content_id"],
                json.dumps(details_with_meta),
                entry["witness_domain"],
                entry["witness_link_id"],
                entry["related_link_ids_json"],
                entry["prev_hash"],
                entry["hash"],
            ),
        )
        conn.commit()
        conn.close()
        entry["related_link_ids"] = normalized_related
        return entry

    def list_entries(
        self,
        content_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if content_id is not None:
            cursor.execute(
                """
                SELECT * FROM witness_chain
                WHERE content_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (str(content_id), limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM witness_chain
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        rows = cursor.fetchall()
        conn.close()
        entries = [dict(row) for row in rows]
        for entry in entries:
            entry["related_link_ids"] = decode_related_link_ids(entry.get("related_link_ids_json"))
        return entries

    def list_entries_for_verification(self) -> List[Dict[str, Any]]:
        """Return entries oldest-first for hash-link verification."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM witness_chain ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        entries = [dict(row) for row in rows]
        for entry in entries:
            entry["related_link_ids"] = decode_related_link_ids(entry.get("related_link_ids_json"))
        return entries

    def verify_linkage(self) -> Dict[str, Any]:
        """Verify hash linkage for the persisted witness chain."""
        entries = self.list_entries_for_verification()
        return {
            "checked": True,
            "entry_count": len(entries),
            "linkage_valid": self.verify_chain(entries),
        }

    def verify_chain(self, entries: List[Dict[str, Any]]) -> bool:
        """Verify no entries have been tampered with."""
        prev_hash = None
        for entry in entries:
            if entry.get("prev_hash") != prev_hash:
                return False
            details = entry.get("details")
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    return False
            related_link_ids_json = entry.get("related_link_ids_json")
            if related_link_ids_json is None and "related_link_ids" in entry:
                related_link_ids_json = encode_related_link_ids(entry.get("related_link_ids"))
            check = {
                "timestamp": entry.get("timestamp"),
                "action": entry.get("action"),
                "agent_id": entry.get("agent_id", entry.get("agent_address")),
                "details": details,
                "prev_hash": entry.get("prev_hash"),
                "content_id": entry.get("content_id"),
                "witness_domain": entry.get("witness_domain", PUBLICATION_WITNESS_DOMAIN),
                "witness_link_id": entry.get("witness_link_id"),
                "related_link_ids_json": related_link_ids_json or "[]",
            }
            expected = hashlib.sha256(
                json.dumps(check, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            if entry.get("hash") != expected:
                return False
            prev_hash = entry.get("hash")
        return True
