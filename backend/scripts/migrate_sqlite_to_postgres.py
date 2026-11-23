"""Copy Open WebUI's app data from SQLite to PostgreSQL.

CUSTOM (MASS-GPT): one-time move of webui.db to the Postgres database named
by DATABASE_URL. See docs/POSTGRES_MIGRATION.md for the full runbook.

Preconditions:
  * Open WebUI is stopped, so webui.db does not change during the copy.
  * Open WebUI has started once against the Postgres database, so Alembic
    created the schema, and both databases are at the same Alembic revision.

The copy runs in a single Postgres transaction: target tables are emptied,
rows are inserted in foreign-key order with their original IDs, sequences
are moved past the copied IDs and row counts are compared. Any error or
count mismatch rolls everything back.

Usage (from the backend directory):
  python scripts/migrate_sqlite_to_postgres.py --dry-run
  python scripts/migrate_sqlite_to_postgres.py
  python scripts/migrate_sqlite_to_postgres.py --sqlite data/webui.db --target postgresql://...
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection, make_url

ALEMBIC_TABLE = 'alembic_version'
# Tables Open WebUI creates at startup instead of through Alembic.
SKIP_NOTES = {
    'owrf_event_outbox': 'created at startup only when ENABLE_OWRF_SYNC=true; start once with sync on to copy it',
}
TRUE_STRINGS = {'1', 'true', 't', 'yes', 'y', 'on'}
FALSE_STRINGS = {'0', 'false', 'f', 'no', 'n', 'off', ''}


class MigrationError(Exception):
    pass


def strip_nul(value: Any) -> Any:
    """Remove NUL characters, which Postgres rejects in text and JSON."""
    if isinstance(value, str):
        return value.replace('\x00', '')
    if isinstance(value, list):
        return [strip_nul(v) for v in value]
    if isinstance(value, dict):
        return {strip_nul(k): strip_nul(v) for k, v in value.items()}
    return value


def convert_value(value: Any, column_type: sa.types.TypeEngine) -> Any:
    """Turn a raw SQLite value into what the Postgres column expects."""
    if value is None:
        return None
    if isinstance(column_type, sa.JSON):
        if isinstance(value, (bytes, bytearray)):
            value = value.decode('utf-8')
        if isinstance(value, str):
            value = json.loads(value)
        return strip_nul(value)
    if isinstance(column_type, sa.Boolean):
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in TRUE_STRINGS:
                return True
            if lowered in FALSE_STRINGS:
                return False
            raise ValueError(f'not a boolean: {value!r}')
        return bool(value)
    if isinstance(column_type, sa.Integer) and isinstance(value, str):
        return int(value)
    if isinstance(column_type, sa.String):
        if isinstance(value, (bytes, bytearray)):
            value = value.decode('utf-8', errors='replace')
        elif not isinstance(value, str):
            value = str(value)
        return strip_nul(value)
    return value


def redact(url: str) -> str:
    return make_url(url).render_as_string(hide_password=True)


def sqlite_tables(src: sqlite3.Connection) -> dict[str, list[str]]:
    names = [
        r[0]
        for r in src.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {n: [c[1] for c in src.execute(f'PRAGMA table_info("{n}")')] for n in names}


def alembic_revision_sqlite(src: sqlite3.Connection) -> str | None:
    try:
        row = src.execute(f'SELECT version_num FROM {ALEMBIC_TABLE}').fetchone()
    except sqlite3.OperationalError:
        return None
    return row[0] if row else None


def alembic_revision_pg(conn: Connection) -> str | None:
    if not sa.inspect(conn).has_table(ALEMBIC_TABLE):
        return None
    return conn.execute(sa.text(f'SELECT version_num FROM {ALEMBIC_TABLE}')).scalar()


def build_plan(src_tables: dict[str, list[str]], target: sa.MetaData) -> tuple[list[sa.Table], list[str], list[str]]:
    """Return (tables to copy in FK order, tables only in SQLite, problems)."""
    problems: list[str] = []
    ordered = [t for t in target.sorted_tables if t.name in src_tables and t.name != ALEMBIC_TABLE]
    only_in_sqlite = sorted(set(src_tables) - {t.name for t in target.sorted_tables} - {ALEMBIC_TABLE})
    for table in ordered:
        missing = sorted(set(src_tables[table.name]) - set(table.columns.keys()))
        if missing:
            problems.append(f'{table.name}: columns missing in Postgres: {", ".join(missing)}')
    return ordered, only_in_sqlite, problems


def copy_table(src: sqlite3.Connection, conn: Connection, table: sa.Table, batch_size: int) -> int:
    columns = [c for c in table.columns if c.name in {r[1] for r in src.execute(f'PRAGMA table_info("{table.name}")')}]
    names = [c.name for c in columns]
    select = 'SELECT ' + ', '.join(f'"{n}"' for n in names) + f' FROM "{table.name}"'
    cursor = src.execute(select)
    copied = 0
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        batch = []
        for row in rows:
            record = {}
            for column, value in zip(columns, row):
                try:
                    record[column.name] = convert_value(value, column.type)
                except (ValueError, TypeError) as exc:
                    raise MigrationError(f'{table.name}.{column.name}: cannot convert value ({exc})') from exc
            batch.append(record)
        conn.execute(table.insert(), batch)
        copied += len(batch)
    return copied


def reset_sequences(conn: Connection, table: sa.Table) -> None:
    for column in table.columns:
        if not isinstance(column.type, sa.Integer):
            continue
        sequence = conn.execute(
            sa.text('SELECT pg_get_serial_sequence(:t, :c)'),
            {'t': f'"{table.name}"', 'c': column.name},
        ).scalar()
        if sequence:
            conn.execute(
                sa.text(
                    f'SELECT setval(:s, COALESCE((SELECT MAX("{column.name}") FROM "{table.name}"), 0) + 1, false)'
                ),
                {'s': sequence},
            )


def count_sqlite(src: sqlite3.Connection, name: str) -> int:
    return src.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]


def count_pg(conn: Connection, name: str) -> int:
    return conn.execute(sa.text(f'SELECT COUNT(*) FROM "{name}"')).scalar()


def migrate(sqlite_path: Path, target_url: str, dry_run: bool, overwrite: bool, batch_size: int) -> None:
    if not sqlite_path.is_file():
        raise MigrationError(f'SQLite file not found: {sqlite_path}')
    url = make_url(target_url)
    if not url.drivername.startswith('postgresql'):
        raise MigrationError(f'target must be a postgresql:// URL, got {url.drivername}://')
    if url.drivername == 'postgresql+psycopg':
        url = url.set(drivername='postgresql+psycopg2')

    print(f'Source: {sqlite_path}')
    print(f'Target: {redact(target_url)}')

    src = sqlite3.connect(str(sqlite_path))
    engine = sa.create_engine(url)
    try:
        src_tables = sqlite_tables(src)
        with engine.connect() as conn:
            src_rev = alembic_revision_sqlite(src)
            dst_rev = alembic_revision_pg(conn)
            print(f'Alembic revision: SQLite {src_rev}, Postgres {dst_rev}')
            if dst_rev is None:
                raise MigrationError('Postgres has no schema yet. Start Open WebUI once with DATABASE_URL set, then stop it.')
            if src_rev != dst_rev:
                raise MigrationError('Alembic revisions differ. Run both databases on the same Open WebUI version.')

            target = sa.MetaData()
            target.reflect(bind=conn)
            ordered, only_in_sqlite, problems = build_plan(src_tables, target)
            if problems:
                raise MigrationError('schema mismatch:\n  ' + '\n  '.join(problems))

            existing_users = count_pg(conn, 'user') if 'user' in target.tables else 0
            if existing_users and not overwrite and not dry_run:
                raise MigrationError(
                    f'Postgres already has {existing_users} user(s). Pass --overwrite to replace its data.'
                )

            print(f'\n{"table":32} {"rows":>8}')
            for table in ordered:
                print(f'{table.name:32} {count_sqlite(src, table.name):>8}')
            for name in only_in_sqlite:
                rows = count_sqlite(src, name)
                note = SKIP_NOTES.get(name, 'not in the Postgres schema')
                print(f'{name:32} {rows:>8}  SKIPPED ({note})' + ('  <-- rows will NOT be copied' if rows else ''))

            if dry_run:
                print('\nDry run: nothing was written.')
                return

        with engine.begin() as conn:
            # Keep triggers (the OWRF sync capture) from turning every copied row into a new event.
            try:
                with conn.begin_nested():
                    conn.execute(sa.text('SET LOCAL session_replication_role = replica'))
                print('Triggers disabled for the copy.')
            except sa.exc.DBAPIError:
                print('WARNING: no permission to disable triggers; OWRF sync events may be queued for copied rows.')
            names = ', '.join(f'"{t.name}"' for t in ordered)
            conn.execute(sa.text(f'TRUNCATE {names} RESTART IDENTITY CASCADE'))
            for table in ordered:
                copy_table(src, conn, table, batch_size)
                reset_sequences(conn, table)

            mismatches = []
            for table in ordered:
                expected, actual = count_sqlite(src, table.name), count_pg(conn, table.name)
                if expected != actual:
                    mismatches.append(f'{table.name}: SQLite {expected}, Postgres {actual}')
            if mismatches:
                raise MigrationError('row counts differ, rolled back:\n  ' + '\n  '.join(mismatches))

        print(f'\nCopied {len(ordered)} tables; row counts match.')
    finally:
        src.close()
        engine.dispose()


def main() -> int:
    backend_dir = Path(__file__).resolve().parent.parent
    try:
        from dotenv import load_dotenv

        # Same .env the backend reads when it runs from source; real environment variables win.
        load_dotenv(backend_dir.parent / '.env')
    except ImportError:
        pass
    data_dir = Path(os.getenv('DATA_DIR', backend_dir / 'data'))
    parser = argparse.ArgumentParser(description='Copy Open WebUI data from SQLite to PostgreSQL.')
    parser.add_argument('--sqlite', type=Path, default=data_dir / 'webui.db', help='source webui.db')
    parser.add_argument('--target', default=os.getenv('DATABASE_URL'), help='Postgres URL (default: DATABASE_URL)')
    parser.add_argument('--dry-run', action='store_true', help='check and list tables without writing')
    parser.add_argument('--overwrite', action='store_true', help='replace data in a Postgres DB that has users')
    parser.add_argument('--batch-size', type=int, default=500)
    args = parser.parse_args()

    if not args.target:
        parser.error('set DATABASE_URL or pass --target')
    try:
        migrate(args.sqlite, args.target, args.dry_run, args.overwrite, args.batch_size)
    except MigrationError as exc:
        print(f'\nERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
