# SAB Master Index

Last audited: 2026-07-02
Local audit repo: `/Users/dhyana/dharmic-agora`

## Forensics

Primary Phase 0 artifact:
- Path: `/Users/dhyana/sab-forensics/sab-forensics-20260702T024605Z.tgz`
- SHA256: `98982d5a675d2cc2e7dedcf62e30bb46721024f7f8f777141ce385f9387f6775`

Supplemental artifact for extra Agni workspaces:
- Path: `/Users/dhyana/sab-forensics/sab-forensics-supplemental-20260702T024921Z.tgz`
- SHA256: `28602c13d9297b140ea05a192346dca3e3e7ed8816428911b2303a0ffec680ff`

The artifacts preserve git status/diff manifests, untracked file archives, a live-safe SQLite backup of `sabp.db`, a full live `data/` copy, systemd status, and credential inventories by path/size/mtime only.

## Canonical Repository

Canonical working repo for this audit:
- Path: `/Users/dhyana/dharmic-agora`
- Foundation branch: `codex/sab-foundation-hardening-20260702`
- Base branch: `origin/main`
- Base SHA: `1c71b93a834a7e3e50e246012df61cc9fc40ba0a`
- Foundation PR: `#2`
- Foundation merge SHA: `06b357f5017ebb108ec51daa11278f2c3d367a80`
- Primary remote: `origin https://github.com/AmitabhainArunachala/dharmic-agora.git`
- Local secondary remote retired: `shakti-saraswati https://github.com/shakti-saraswati/dharmic-agora.git`

Branch policy:
- `main` is the merge target.
- Feature and fix work happens on PR branches.
- Production redeploys come only from reviewed, merged `main`.
- No direct edits in production checkouts.

Open naming conflict:
- `pyproject.toml` still points project URLs at `shakti-saraswati/dharmic-agora`.
- The current canonical remote in this checkout is `AmitabhainArunachala/dharmic-agora`.
- Do not treat the old remote as authority unless the owner explicitly reassigns it.

## Runtime Surfaces

SAB has two intentional FastAPI surfaces:
- Public Basin Shell: `agora.app:app`
  - public feed, submit, spark detail, canon, compost, register
  - default DB: `data/spark.db`
- Protocol / Operator Surface: `agora.api_server:app`
  - auth, posts, queue, moderation, governance, federation, health
  - default DB: `data/sabp.db`

Convergence seam:
- `SAB_AUTHORITY_DB_PATH` points both surfaces at one SQLite authority path.
- Agni deploy artifacts should use `/app/data/sabp.db`.

## Where Production Runs

Observed from Phase 0 forensics before cutover:
- Host label: `agni-openclaw`
- Service: `sab-agora.service`
- Live service file: `/etc/systemd/system/sab-agora.service`
- Active process: `/usr/bin/python3 -m uvicorn agora.api_server:app --host 127.0.0.1 --port 8000 --workers 1`
- Live working directory: `/home/openclaw/saraswati-dharmic-agora`
- Live branch: `main`
- Live HEAD: `3bdb408934f2265817a4ae3ccbfd0eade5867dcb`
- Local backend port: `127.0.0.1:8000`
- Public reverse proxy observed: Caddy on `*:80` and `*:443`

Important drift:
- Live production runs `agora.api_server:app` from a dirty checkout.
- Checked-in Docker deployment currently runs `agora.app:app`.
- Deployment work must state which surface is being cut over before restart.

Post-cutover state, 2026-07-02:
- Release path: `/home/openclaw/dharmic-agora-release`
- Release SHA: `06b357f5017ebb108ec51daa11278f2c3d367a80`
- Live service file: `/etc/systemd/system/sab-agora.service`
- Service backup before edit: `/root/sab-agora.service.pre-06b357f-20260702T031334Z`
- Active app target: `agora.api_server:app`
- Active command: `/home/openclaw/dharmic-agora-release/.venv/bin/python -m uvicorn agora.api_server:app --host 127.0.0.1 --port 8000 --workers 1`
- Live data link: `/home/openclaw/dharmic-agora-release/data -> /home/openclaw/saraswati-dharmic-agora/data`
- Health result: `http://127.0.0.1:8000/health` returns `healthy` with `gates: 12`; `https://157.245.193.15/health` returns HTTP 200.
- DNS gap: `agora.dharmic.ai` still has no A/AAAA answer as of this audit.
- Rollback path: restore `/etc/systemd/system/sab-agora.service` from `/root/sab-agora.service.pre-06b357f-20260702T031334Z`, then `systemctl daemon-reload && systemctl restart sab-agora`.

## Deployment Checkouts

Observed Agni repo copies:
- `/home/openclaw/saraswati-dharmic-agora`
  - live service path
  - branch `main`
  - HEAD `3bdb408934f2265817a4ae3ccbfd0eade5867dcb`
  - dirty; preserve until all diffs are reviewed
- `/home/openclaw/repos/saraswati-dharmic-agora`
  - branch `codex/5h-bootstrap-hardening-clean`
  - HEAD `eb0b819f3551bc7a89e4a9727721afaec02a0911`
- `/root/repos/saraswati-dharmic-agora`
  - branch `main`
  - HEAD `9da6b5aa54664b4fcbec5c0b5b3fdb70b7f1a015`
  - has untracked Shakti/Pinchbeck docs
- `/home/openclaw/.openclaw/workspace/dharmic-agora`
  - branch `main`
  - HEAD `ee88d41`
  - untracked federation/transport/DGM artifacts
- `/home/openclaw/.openclaw/workspace/projects/dharmic-agora`
  - branch `main`
  - HEAD `f8af565`
  - ahead 1 with modified deploy/API/auth files

Recommended canonical deployment path after cleanup:
- Use one deploy checkout only.
- Current release path is `/home/openclaw/dharmic-agora-release`.
- Retire dirty live checkouts only after diff preservation, merge decision, and at least one successful bake period.

## Retired / Do Not Use As Source Of Truth

- `/root/repos/saraswati-dharmic-agora`
- `/home/openclaw/dharmic-agora`
- `/home/openclaw/dharmic-agora-working`
- `/home/openclaw/.openclaw/workspace/dharmic-agora`
- `/home/openclaw/.openclaw/workspace/projects/dharmic-agora`
- Any dirty production checkout except as forensic evidence

## Data And Credential Inventory

Credential paths only; never place secret contents in docs:
- `/home/openclaw/dharmic-agora-data/.jwt_secret`
- `/home/openclaw/dharmic-agora-data/.sab_system_ed25519.key`
- `/home/openclaw/dharmic-agora-working/data/.jwt_secret`
- `/home/openclaw/repos/saraswati-dharmic-agora/data/.jwt_secret`
- `/home/openclaw/repos/saraswati-dharmic-agora/data/.sab_system_ed25519.key`
- `/home/openclaw/saraswati-dharmic-agora/data/.jwt_secret`
- `/home/openclaw/saraswati-dharmic-agora/data/.sab_system_ed25519.key`
- `/home/openclaw/saraswati-dharmic-agora/.env.production`
- `/home/openclaw/.openclaw/workspace/dharmic-agora/.env`

Live data copy in forensics:
- `spark.db`
- `sabp.db`
- `agora.db`
- `.jwt_secret`
- `.sab_system_ed25519.key`
- `federation/`

Forensic `sabp.db` row counts:
- `posts`: 39
- `comments`: 2
- `moderation_queue`: 83
- `witness_chain`: 41

## PR To Merge To Redeploy Policy

1. No direct edits in production checkouts.
2. All changes start from canonical `main` on a feature branch.
3. Open a PR and run tests before merge.
4. Review runtime-surface impact: `agora.app:app`, `agora.api_server:app`, or both.
5. Merge to `main` only after checks pass.
6. Redeploy from clean `main`, not from a dirty live tree.
7. Before the first redeploy after this audit, preserve Phase 0 dirty live diffs and decide what to merge, archive, or discard.
8. After deploy, record deployed commit SHA, service unit, app target, DB path/env, health result, and rollback SHA.

## Backups

Authority DB backup script:
- Source: `scripts/backup_sabp_db.sh`
- Agni cron target: `/home/openclaw/dharmic-agora-release/scripts/backup_sabp_db.sh`
- Default DB path: `/home/openclaw/saraswati-dharmic-agora/data/sabp.db`
- Default backup root: `/root/sab-db-backups`
- Default retention: 14 days
- Method: Python `sqlite3.Connection.backup` against a read-only source connection, followed by a SHA256 sidecar file.

Off-box backup status:
- Phase 0 forensics were copied off Agni to `/Users/dhyana/sab-forensics/`.
- Recurring off-box sync is not configured yet; add only after choosing a destination and credential boundary.

## Deferred Foundation Follow-Ups

- Hypothesis kill conditions remain disabled. H1 needs fresh post-fix traffic history; H2 currently measures the compatibility gate harness, not the canonical production gate protocol.
- DGC/security diagnostics are observe-only. `/signals/dgc` records audit and witness evidence for later baseline work but does not block publication.
- Credential consolidation is deferred until after a successful production bake period; do not duplicate or rotate keys during the first cutover.
- Agni stale checkout removal is deferred until all dirty diffs are reviewed and archived.
