#!/usr/bin/env bash
set -euo pipefail

# Live-safe SQLite backup for the SAB authority database.
# Uses sqlite3.Connection.backup because the sqlite3 CLI is not guaranteed on Agni.

DB_PATH="${SAB_BACKUP_DB_PATH:-${SAB_AUTHORITY_DB_PATH:-${SAB_DB_PATH:-/home/openclaw/saraswati-dharmic-agora/data/sabp.db}}}"
BACKUP_ROOT="${SAB_BACKUP_ROOT:-/root/sab-db-backups}"
RETENTION_DAYS="${SAB_BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_PATH="${BACKUP_ROOT}/sabp-${STAMP}.db"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "SAB backup failed: DB not found at ${DB_PATH}" >&2
  exit 1
fi

install -d -m 700 "${BACKUP_ROOT}"
umask 077

python3 - "${DB_PATH}" "${BACKUP_PATH}" <<'PY'
import sqlite3
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
backup_path = Path(sys.argv[2])

source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
try:
    destination = sqlite3.connect(backup_path)
    try:
        source.backup(destination)
    finally:
        destination.close()
finally:
    source.close()
PY

sha256sum "${BACKUP_PATH}" > "${BACKUP_PATH}.sha256"

find "${BACKUP_ROOT}" -type f \( -name 'sabp-*.db' -o -name 'sabp-*.db.sha256' \) -mtime "+${RETENTION_DAYS}" -delete

echo "SAB backup ok: ${BACKUP_PATH}"
