# Moving the app database from SQLite to PostgreSQL

Open WebUI keeps users, groups, chats, models, tools, settings and usage data in its app database. By default that is the SQLite file `data/webui.db`. This runbook moves it to PostgreSQL.

What stays where it is:

- Uploaded files stay in `data/uploads` (until MinIO/S3 is turned on).
- Knowledge-base vectors stay in Chroma, in `data/vector_db`. They need no re-indexing.
- `webui.db` is not changed or deleted. It is the rollback.

Supported app databases are SQLite and PostgreSQL only. MySQL and MariaDB are not supported for the app database.

## How it works

1. A `postgres` service runs next to Open WebUI (`docker-compose.sso.yaml`).
2. Open WebUI starts once against the empty Postgres. Its Alembic migrations create the full schema.
3. `backend/scripts/migrate_sqlite_to_postgres.py` copies every table from `webui.db` into Postgres. The copy runs in one transaction:
   - Postgres tables are emptied first.
   - IDs are kept, and JSON and boolean values are converted.
   - Triggers are off during the copy, so the RAGFlow sync doesn't queue an event for every copied row.
   - Row counts are compared at the end. Any error or mismatch rolls everything back.
4. Open WebUI is started again with `DATABASE_URL` pointing at Postgres.

The script refuses to run when:

- the two databases are at different Alembic revisions (different Open WebUI versions);
- Postgres has no schema yet;
- Postgres already has users and `--overwrite` was not passed.

`--dry-run` shows the plan without writing anything.

## Settings

| Variable                                                  | Where    | Meaning                                                                                                                                                                                                                          |
| --------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `.env` | Database the `postgres` service creates. Use a URL-safe password (letters and digits).                                                                                                                                         |
| `DATABASE_URL`                                          | `.env` | `postgresql://USER:PASSWORD@HOST:5432/DB`. HOST is `postgres` inside compose and `127.0.0.1` when the backend runs from source (not `localhost`, see Windows notes). Unset means SQLite. Never set it to an empty value. |
| `DATABASE_POOL_SIZE`, `DATABASE_POOL_MAX_OVERFLOW`    | `.env` | Connection pool, default 10 and 10.                                                                                                                                                                                              |
| `POSTGRES_HOST_PORT`                                    | `.env` | Host port, published on all interfaces. Default 5432.                                                                                                                                                                            |

MinIO and Redis are prepared in `docker-compose.sso.yaml` and `.env.example`, but commented out. They are not part of this migration.

## Local run (backend from source)

Run all commands from the repo root.

1. Start Postgres:
   ```bash
   docker compose -f docker-compose.sso.yaml up -d postgres
   ```
2. Stop the backend (the `uvicorn` / `dev.sh` terminal). Keep it stopped until step 6.
3. Back up the SQLite file:
   ```bash
   cp backend/data/webui.db backend/data/webui.db.bak-$(date +%Y%m%d)
   ```
4. In `.env`, uncomment `DATABASE_URL` (host `127.0.0.1`).
5. Create the schema, check the plan, and copy:
   ```bash
   cd backend
   python -c "import open_webui.config"                      # runs the Alembic migrations against Postgres
   python scripts/migrate_sqlite_to_postgres.py --dry-run
   python scripts/migrate_sqlite_to_postgres.py               # add --overwrite if Postgres already has users
   ```

   Like the backend, the script reads `DATABASE_URL` from the repo `.env`; an exported variable or `--target` takes precedence.
6. Start the backend as usual. `start_windows.bat` and `dev.sh` (uses `--reload`) work as they are. Only a `uvicorn` command you type yourself, with one worker and no `--reload`, needs `--loop asyncio:SelectorEventLoop` (see Windows notes).

### Windows notes

These apply only when the backend runs from source on Windows. The Linux Docker image is not affected.

- **`Psycopg cannot use the 'ProactorEventLoop'`:** uvicorn creates a Proactor event loop for a single worker without `--reload`, before Open WebUI loads. Postgres's async driver can't use that loop. `start_windows.bat` already passes `--loop asyncio:SelectorEventLoop`; add it when you start uvicorn yourself, for example:
  ```bash
  uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --forwarded-allow-ips=* --loop asyncio:SelectorEventLoop
  ```

  On Windows, write `--forwarded-allow-ips=*` as one argument. Written as `--forwarded-allow-ips "*"`, uvicorn expands `*` into the file names in the current folder, even inside quotes.
- **Startup hangs at "Installing external dependencies of functions and tools...":** `DATABASE_URL` uses `localhost`. The async driver hangs resolving it on Windows. Use `127.0.0.1`.
- **DBeaver: `invalid value for parameter "TimeZone": "Asia/Calcutta"`:** Java reports the old timezone name. The compose file pins `postgres:16-bookworm`, which still has it. Against a Postgres on the default Debian 13 image, add `-Duser.timezone=Asia/Kolkata` after `-vmargs` in `dbeaver.ini` and restart DBeaver.

## Server (Docker)

1. Pull the release and add the Postgres variables from `.env.example` to the server `.env`. Leave `DATABASE_URL` commented for now.
2. Start Postgres and stop Open WebUI:
   ```bash
   docker compose -f docker-compose.sso.yaml up -d postgres
   docker compose -f docker-compose.sso.yaml stop open-webui
   ```
3. Back up the volume's database:
   ```bash
   docker run --rm -v <project>_open-webui:/data alpine cp /data/webui.db /data/webui.db.bak-$(date +%Y%m%d)
   ```
4. Set `DATABASE_URL=postgresql://USER:PASSWORD@postgres:5432/DB` in `.env`.
5. Start Open WebUI once so it creates the schema. With `ENABLE_OWRF_SYNC=true`, this also creates the sync outbox table, so pending sync events are copied too. When the log shows the server is up, stop it:
   ```bash
   docker compose -f docker-compose.sso.yaml up -d open-webui --build
   docker compose -f docker-compose.sso.yaml logs -f open-webui     # wait for "Application startup complete"
   docker compose -f docker-compose.sso.yaml stop open-webui
   ```
6. Copy:
   ```bash
   docker compose -f docker-compose.sso.yaml run --rm --no-deps open-webui \
     python scripts/migrate_sqlite_to_postgres.py --dry-run
   docker compose -f docker-compose.sso.yaml run --rm --no-deps open-webui \
     python scripts/migrate_sqlite_to_postgres.py --overwrite
   ```

   `--overwrite` is needed here because the first start may already have created the first user.
7. Start Open WebUI:
   ```bash
   docker compose -f docker-compose.sso.yaml up -d open-webui
   ```

## Checks after the switch

- SSO login works, for both an admin and a normal user.
- Admin → Users: the same users, roles and groups, including manually created groups such as `Team-*`.
- Old chats open with their messages, folders, tags and pinned state.
- Admin → Models: RAGFlow models, model groups, connection names and access settings are unchanged.
- Admin Settings keep their saved values (persistent config).
- Usage limits and analytics show the earlier totals.
- A RAGFlow chat answers, and changes still reach the RAGFlow syncer.

## Rollback

Stop Open WebUI and set `DATABASE_URL=sqlite:////app/backend/data/webui.db` in `.env` (from source: comment `DATABASE_URL` out again). Then start Open WebUI. Anything written to Postgres after the switch is not in `webui.db`.

## Backups after the switch

`webui.db` is no longer updated. Back up Postgres instead:

```bash
docker exec open-webui-postgres pg_dump -U openwebui -Fc openwebui > owui-$(date +%Y%m%d).dump
```

Keep backing up the `open-webui` volume as well, since it still holds uploads and Chroma.
