"""CUSTOM (MASS-GPT): copy selected tool user-valve credentials to a table other apps can read.

Off unless both variables are set (PostgreSQL only):

  TOOL_CREDENTIALS_EXPORT      tool_id:username_field:password_field[,more...]
                               e.g. cosec_attendance:cosec_username:cosec_password
  TOOL_CREDENTIALS_EXPORT_KEY  Fernet key shared with the reading app; never WEBUI_SECRET_KEY

When a user saves the valves of a listed tool, the username is written as is and the password
Fernet-encrypted to integration.user_tool_credentials. Clearing either field, or deleting the
user, removes the row. Open WebUI never reads the table. The schema is outside Alembic, so
upstream migrations do not touch it. See docs/TOOL_CREDENTIALS_EXPORT.md.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

from cryptography.fernet import Fernet
from sqlalchemy import text

log = logging.getLogger(__name__)

SCHEMA = 'integration'
TABLE = f'{SCHEMA}.user_tool_credentials'


@dataclass(frozen=True)
class ExportSpec:
    tool_id: str
    username_field: str
    password_field: str


def parse_specs(raw: str | None) -> dict[str, ExportSpec]:
    specs: dict[str, ExportSpec] = {}
    for item in (raw or '').split(','):
        item = item.strip()
        if not item:
            continue
        parts = [p.strip() for p in item.split(':')]
        if len(parts) != 3 or not all(parts):
            raise ValueError(f'TOOL_CREDENTIALS_EXPORT entry must be tool_id:username_field:password_field, got {item!r}')
        specs[parts[0]] = ExportSpec(*parts)
    return specs


def credentials_from_valves(spec: ExportSpec, valves: dict | None) -> tuple[str, str] | None:
    """Return (username, password), or None when either one is empty."""
    valves = valves or {}
    username = str(valves.get(spec.username_field) or '').strip()
    password = str(valves.get(spec.password_field) or '')
    return (username, password) if username and password else None


class _Exporter:
    def __init__(self, specs: dict[str, ExportSpec], fernet: Fernet | None):
        self.specs = specs
        self.fernet = fernet
        self.ready = False  # set once the table exists on a PostgreSQL database

    @property
    def configured(self) -> bool:
        return bool(self.specs) and self.fernet is not None


def _load() -> _Exporter:
    specs = parse_specs(os.getenv('TOOL_CREDENTIALS_EXPORT'))
    key = os.getenv('TOOL_CREDENTIALS_EXPORT_KEY', '').strip()
    if not specs:
        return _Exporter({}, None)
    if not key:
        raise RuntimeError('TOOL_CREDENTIALS_EXPORT is set: configure TOOL_CREDENTIALS_EXPORT_KEY as well')
    try:
        fernet = Fernet(key.encode())
    except ValueError as exc:
        raise RuntimeError('TOOL_CREDENTIALS_EXPORT_KEY is not a valid Fernet key') from exc
    return _Exporter(specs, fernet)


_exporter = _load()


async def install(engine) -> None:
    """Create the schema and table when the export is configured. Called once at startup."""
    if not _exporter.configured:
        return
    if engine.dialect.name != 'postgresql':
        log.warning('TOOL_CREDENTIALS_EXPORT needs PostgreSQL; export disabled on %s', engine.dialect.name)
        return
    async with engine.begin() as conn:
        await conn.execute(text('SELECT pg_advisory_xact_lock(73193403)'))
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {SCHEMA}'))
        await conn.execute(
            text(
                f"""CREATE TABLE IF NOT EXISTS {TABLE} (
                user_id      TEXT   NOT NULL,
                tool_id      TEXT   NOT NULL,
                user_email   TEXT,
                username     TEXT   NOT NULL,
                password_enc TEXT   NOT NULL,
                updated_at   BIGINT NOT NULL,
                PRIMARY KEY (user_id, tool_id))"""
            )
        )
    _exporter.ready = True
    log.info('Tool credentials export enabled for: %s', ', '.join(sorted(_exporter.specs)))


async def export_user_valves(user_id: str, user_email: str | None, tool_id: str, valves: dict | None) -> None:
    """Upsert or remove one user's exported credentials. Never raises into the caller."""
    if not _exporter.ready or tool_id not in _exporter.specs:
        return
    from open_webui.internal.db import async_engine

    try:
        creds = credentials_from_valves(_exporter.specs[tool_id], valves)
        async with async_engine.begin() as conn:
            if creds is None:
                await conn.execute(
                    text(f'DELETE FROM {TABLE} WHERE user_id = :u AND tool_id = :t'), {'u': user_id, 't': tool_id}
                )
                return
            username, password = creds
            await conn.execute(
                text(
                    f"""INSERT INTO {TABLE} (user_id, tool_id, user_email, username, password_enc, updated_at)
                    VALUES (:u, :t, :e, :n, :p, :ts)
                    ON CONFLICT (user_id, tool_id) DO UPDATE SET
                    user_email = EXCLUDED.user_email, username = EXCLUDED.username,
                    password_enc = EXCLUDED.password_enc, updated_at = EXCLUDED.updated_at"""
                ),
                {
                    'u': user_id,
                    't': tool_id,
                    'e': user_email,
                    'n': username,
                    'p': _exporter.fernet.encrypt(password.encode()).decode(),
                    'ts': int(time.time()),
                },
            )
    except Exception as exc:
        # The valves are already saved; never fail the user's save over the copy. No secrets in the log.
        log.warning('Tool credentials export failed for tool %s: %s', tool_id, type(exc).__name__)


async def remove_user(user_id: str) -> None:
    """Drop every exported credential of a deleted user."""
    if not _exporter.ready:
        return
    from open_webui.internal.db import async_engine

    try:
        async with async_engine.begin() as conn:
            await conn.execute(text(f'DELETE FROM {TABLE} WHERE user_id = :u'), {'u': user_id})
    except Exception as exc:
        log.warning('Tool credentials export cleanup failed: %s', type(exc).__name__)
