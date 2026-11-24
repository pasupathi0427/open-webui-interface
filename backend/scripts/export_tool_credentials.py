"""Fill integration.user_tool_credentials from the valves users have already saved.

CUSTOM (MASS-GPT): run once after turning on TOOL_CREDENTIALS_EXPORT. New saves are exported
automatically; this covers credentials saved before. It must run where Open WebUI runs (same
.env / environment), because only Open WebUI can decrypt the stored valves.

  python scripts/export_tool_credentials.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> int:
    from sqlalchemy import text

    from open_webui.internal.db import async_engine
    from open_webui.tool_credentials_export import _exporter, export_user_valves, install
    from open_webui.utils.valves import decrypt_valves

    if not _exporter.configured:
        print('TOOL_CREDENTIALS_EXPORT / TOOL_CREDENTIALS_EXPORT_KEY are not set; nothing to do.')
        return 1
    await install(async_engine)
    if not _exporter.ready:
        print('Export is not active (PostgreSQL required).')
        return 1

    async with async_engine.connect() as conn:
        rows = (await conn.execute(text('SELECT id, email, settings FROM "user"'))).all()

    exported = {tool_id: 0 for tool_id in _exporter.specs}
    for user_id, email, settings in rows:
        valves_by_tool = ((settings or {}).get('tools') or {}).get('valves') or {}
        for tool_id in _exporter.specs:
            if tool_id not in valves_by_tool:
                continue
            valves = decrypt_valves(valves_by_tool[tool_id])
            await export_user_valves(user_id, email, tool_id, valves)
            exported[tool_id] += 1

    async with async_engine.connect() as conn:
        for tool_id in _exporter.specs:
            count = (
                await conn.execute(
                    text('SELECT COUNT(*) FROM integration.user_tool_credentials WHERE tool_id = :t'), {'t': tool_id}
                )
            ).scalar()
            print(f'{tool_id}: {exported[tool_id]} user(s) with saved valves, {count} row(s) with credentials')
    await async_engine.dispose()
    return 0


if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.exit(asyncio.run(main()))
