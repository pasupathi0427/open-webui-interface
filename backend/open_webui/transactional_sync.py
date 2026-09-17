"""OW extension: transactional ID-only notifications, retried signed HTTP delivery.

Installed as open_webui.transactional_sync. No syncer dependency in OW.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from contextlib import asynccontextmanager

import httpx
from sqlalchemy import inspect, text

log = logging.getLogger(__name__)
# Ignore access timestamps/token rotations; capture only sync-relevant mutations.
TABLES = {
    "user": ("user", "id", ("email", "name", "role")),
    "knowledge": ("knowledge", "id", ("name", "description", "user_id")),
    "knowledge_file": ("knowledge", "knowledge_id", ("knowledge_id", "file_id")),
    "file": ("file", "id", ("filename", "path", "meta", "data")),
    "model": ("model", "id", ("name", "base_model_id", "params", "meta", "is_active")),
}


async def install(engine):
    """Triggers run in the business transaction, including bulk SQL and rollbacks."""
    dialect = engine.dialect.name
    if dialect not in {"sqlite", "postgresql"}:
        raise RuntimeError("OW transactional sync supports SQLite or PostgreSQL")
    async with engine.begin() as conn:
        if dialect == "postgresql":
            await conn.execute(text("SELECT pg_advisory_xact_lock(73193402)"))
        else:
            await conn.execute(text("BEGIN IMMEDIATE"))
        await conn.execute(text("""CREATE TABLE IF NOT EXISTS owrf_event_outbox (
            id VARCHAR(64) PRIMARY KEY, entity VARCHAR(32) NOT NULL,
            entity_id TEXT NOT NULL, action VARCHAR(32) NOT NULL,
            delivered_at BIGINT, available_at BIGINT NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0)"""))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS owrf_pending_events "
                                "ON owrf_event_outbox(delivered_at, available_at)"))
        for table, (entity, key, columns) in TABLES.items():
            actual = await conn.run_sync(
                lambda c, table=table: {r["name"] for r in inspect(c).get_columns(table)}
            )
            if not {key, *columns} <= actual:
                raise RuntimeError(f"OW sync schema mismatch: {table}")
            for operation, row in (("INSERT", "NEW"), ("UPDATE", "NEW"), ("DELETE", "OLD")):
                name = f"owrf_{table}_{operation.lower()}"
                action = "membership_changed" if table == "knowledge_file" else (
                    "deleted" if operation == "DELETE" else "updated")
                if dialect == "sqlite":
                    condition = " OR ".join(f'OLD."{col}" IS NOT NEW."{col}"' for col in columns)
                    when = f" WHEN {condition}" if operation == "UPDATE" else ""
                    old_membership = (
                        "INSERT INTO owrf_event_outbox(id,entity,entity_id,action) "
                        "SELECT lower(hex(randomblob(16))),'knowledge',OLD.knowledge_id,'membership_changed' "
                        "WHERE OLD.knowledge_id IS NOT NEW.knowledge_id;"
                        if table == "knowledge_file" and operation == "UPDATE" else ""
                    )
                    await conn.execute(text(f'DROP TRIGGER IF EXISTS "{name}"'))
                    await conn.execute(text(f'''CREATE TRIGGER "{name}"
                        AFTER {operation} ON "{table}"{when} BEGIN
                        INSERT INTO owrf_event_outbox(id,entity,entity_id,action)
                        VALUES(lower(hex(randomblob(16))),'{entity}',{row}."{key}",'{action}');
                        {old_membership} END'''))
                else:
                    condition = " OR ".join(
                        f'OLD."{col}"::text IS DISTINCT FROM NEW."{col}"::text' for col in columns)
                    guard = f"IF NOT ({condition}) THEN RETURN NEW; END IF;" if operation == "UPDATE" else ""
                    old_membership = (
                        "IF OLD.knowledge_id IS DISTINCT FROM NEW.knowledge_id THEN "
                        "INSERT INTO owrf_event_outbox(id,entity,entity_id,action) VALUES("
                        "md5(random()::text || clock_timestamp()::text),'knowledge',"
                        "OLD.knowledge_id,'membership_changed'); END IF;"
                        if table == "knowledge_file" and operation == "UPDATE" else ""
                    )
                    await conn.execute(text(f'''CREATE OR REPLACE FUNCTION "{name}_fn"()
                        RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN {guard}
                        INSERT INTO owrf_event_outbox(id,entity,entity_id,action)
                        VALUES(md5(random()::text || clock_timestamp()::text),
                        '{entity}',{row}."{key}",'{action}'); {old_membership} RETURN {row}; END $$'''))
                    await conn.execute(text(f'DROP TRIGGER IF EXISTS "{name}" ON "{table}"'))
                    await conn.execute(text(f'''CREATE TRIGGER "{name}" AFTER {operation}
                        ON "{table}" FOR EACH ROW EXECUTE FUNCTION "{name}_fn"()'''))


async def deliver_once(engine, client, url, secret):
    async with engine.connect() as conn:
        rows = (await conn.execute(text("SELECT id,entity,entity_id,action,attempts "
            "FROM owrf_event_outbox WHERE delivered_at IS NULL AND available_at<=:now "
            "ORDER BY available_at,id LIMIT 100"), {"now": int(time.time())})).mappings().all()
    for row in rows:
        raw = json.dumps({"id": row["id"], "event": f'{row["entity"]}.{row["action"]}',
                          "subject": {"id": row["entity_id"]}}, separators=(",", ":")).encode()
        stamp = str(int(time.time()))
        signature = hmac.new(secret.encode(), stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        try:
            response = await client.post(url, content=raw, headers={
                "Content-Type": "application/json", "X-Sync-Timestamp": stamp,
                "X-Sync-Signature": signature})
            # Only the durable inbox's explicit acknowledgement permits source ack.
            if response.status_code != 202:
                raise RuntimeError(f"Inbox HTTP {response.status_code}")
        except Exception as exc:
            log.warning("OW sync delivery deferred: %s", type(exc).__name__)
            async with engine.begin() as conn:
                await conn.execute(text("UPDATE owrf_event_outbox SET attempts=attempts+1, "
                    "available_at=:next WHERE id=:id AND delivered_at IS NULL"),
                    {"id": row["id"], "next": int(time.time()) + min(300, 2 ** min(row["attempts"] + 1, 8))})
        else:
            # Multiple OW replicas may deliver the same ID. Inbox deduplication is intentional.
            async with engine.begin() as conn:
                await conn.execute(text("UPDATE owrf_event_outbox SET delivered_at=:now "
                    "WHERE id=:id AND delivered_at IS NULL"), {"id": row["id"], "now": int(time.time())})


@asynccontextmanager
async def lifespan():
    url, secret = os.getenv("OWRF_SYNC_EVENT_URL"), os.getenv("OWRF_SYNC_EVENT_SECRET")
    if not url and not secret:
        yield
        return
    if not url or not secret:
        raise RuntimeError("Configure both OWRF_SYNC_EVENT_URL and OWRF_SYNC_EVENT_SECRET")
    from open_webui.internal.db import async_engine
    await install(async_engine)

    async def relay():
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            while True:
                try:
                    await deliver_once(async_engine, client, url, secret)
                except Exception as exc:
                    log.warning("OW sync outbox unavailable: %s", type(exc).__name__)
                await asyncio.sleep(2)

    task = asyncio.create_task(relay())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
