"""CUSTOM: token usage governance (department = group).

- UsageConfig: per-group monthly token limit, resets allowed per period, period anchor, per-user overrides.
- UsageLedger: one row per completed chat completion (tokens counted), so deleting chats never refunds usage.
- UsageRequest: a user's reset request and the admin's decision. Approved top-up / reset rows are the
  period's grants; they expire with the department period they were made in.

Periods are lazy (no cron): a department's period is 30 days from `period_start`, rolled forward on read.
"""

import os
import time
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from open_webui.models.groups import Groups
from open_webui.models.users import Users
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, Index, Integer, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession

USAGE_DEFAULT_TOKEN_LIMIT = int(os.environ.get('USAGE_DEFAULT_TOKEN_LIMIT', 10_000_000))
USAGE_DEFAULT_RESETS = int(os.environ.get('USAGE_DEFAULT_RESETS', 2))
PERIOD_SECONDS = 30 * 24 * 3600

ACTIONS = ('topup', 'reset', 'raise', 'deny')


class UsageConfig(Base):
    __tablename__ = 'usage_config'

    group_id = Column(Text, primary_key=True)
    token_limit = Column(BigInteger, nullable=False)
    resets_per_period = Column(Integer, nullable=False)
    period_start = Column(BigInteger, nullable=False)
    overrides = Column(JSON, nullable=True)  # {user_id: token_limit}
    updated_at = Column(BigInteger, nullable=False)


class UsageLedger(Base):
    __tablename__ = 'usage_ledger'

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False)
    tokens = Column(BigInteger, nullable=False)
    created_at = Column(BigInteger, nullable=False)

    __table_args__ = (Index('usage_ledger_user_created_idx', 'user_id', 'created_at'),)


class UsageRequest(Base):
    __tablename__ = 'usage_request'

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False, index=True)
    group_id = Column(Text, nullable=True)  # None = default department (no group)
    period_start = Column(BigInteger, nullable=False)
    status = Column(Text, nullable=False)  # pending | approved | denied
    action = Column(Text, nullable=True)  # topup | reset | raise | deny
    tokens = Column(BigInteger, nullable=True)  # granted (topup/reset) or new limit (raise)
    created_at = Column(BigInteger, nullable=False)
    decided_at = Column(BigInteger, nullable=True)
    decided_by = Column(Text, nullable=True)


class UsageRequestModel(BaseModel):
    id: str
    user_id: str
    group_id: Optional[str] = None
    period_start: int
    status: str
    action: Optional[str] = None
    tokens: Optional[int] = None
    created_at: int
    decided_at: Optional[int] = None
    decided_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


def current_period_start(anchor: int, now: Optional[int] = None) -> int:
    """Start of the 30-day period containing `now`, counting from `anchor`."""
    now = now or int(time.time())
    if now <= anchor:
        return anchor
    return anchor + ((now - anchor) // PERIOD_SECONDS) * PERIOD_SECONDS


class UsageTable:
    # ---------- department config ----------

    async def get_config(self, group_id: str, db: Optional[AsyncSession] = None) -> dict:
        """Effective config for a group (defaults when never configured)."""
        async with get_async_db_context(db) as db:
            row = await db.get(UsageConfig, group_id)
            if row:
                return {
                    'token_limit': row.token_limit,
                    'resets_per_period': row.resets_per_period,
                    'period_anchor': row.period_start,
                    'overrides': row.overrides or {},
                    'configured': True,
                }
            group = await Groups.get_group_by_id(group_id, db=db)
            return {
                'token_limit': USAGE_DEFAULT_TOKEN_LIMIT,
                'resets_per_period': USAGE_DEFAULT_RESETS,
                'period_anchor': group.created_at if group else int(time.time()),
                'overrides': {},
                'configured': False,
            }

    async def set_config(
        self,
        group_id: str,
        token_limit: int,
        resets_per_period: int,
        overrides: Optional[dict] = None,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Save config. A changed token limit starts a new 30-day period today."""
        now = int(time.time())
        async with get_async_db_context(db) as db:
            row = await db.get(UsageConfig, group_id)
            if row is None:
                row = UsageConfig(
                    group_id=group_id,
                    token_limit=token_limit,
                    resets_per_period=resets_per_period,
                    period_start=now,
                    overrides=overrides or {},
                    updated_at=now,
                )
                db.add(row)
            else:
                if row.token_limit != token_limit:
                    row.period_start = now
                row.token_limit = token_limit
                row.resets_per_period = resets_per_period
                if overrides is not None:
                    row.overrides = overrides
                row.updated_at = now
            await db.commit()
        return await self.get_config(group_id)

    async def set_override(self, group_id: Optional[str], user_id: str, tokens: int, db=None):
        if not group_id:
            return
        cfg = await self.get_config(group_id, db=db)
        overrides = {**cfg['overrides'], user_id: int(tokens)}
        async with get_async_db_context(db) as db:
            row = await db.get(UsageConfig, group_id)
            if row is None:
                await self.set_config(group_id, cfg['token_limit'], cfg['resets_per_period'], overrides, db=db)
                return
            row.overrides = overrides
            row.updated_at = int(time.time())
            await db.commit()

    # ---------- per-user status ----------

    async def get_department(self, user, db: Optional[AsyncSession] = None) -> dict:
        """User's department = their group with the highest effective limit; no group = default."""
        groups = await Groups.get_groups_by_member_id(user.id, db=db)
        best = None
        for g in groups:
            cfg = await self.get_config(g.id, db=db)
            limit = int(cfg['overrides'].get(user.id) or cfg['token_limit'])
            if best is None or limit > best['limit']:
                best = {'group_id': g.id, 'group_name': g.name, 'limit': limit, **cfg}
        if best:
            return best
        return {
            'group_id': None,
            'group_name': None,
            'limit': USAGE_DEFAULT_TOKEN_LIMIT,
            'token_limit': USAGE_DEFAULT_TOKEN_LIMIT,
            'resets_per_period': USAGE_DEFAULT_RESETS,
            'period_anchor': user.created_at,
            'overrides': {},
            'configured': False,
        }

    async def get_used(self, user_id: str, since: int, db: Optional[AsyncSession] = None) -> int:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(func.coalesce(func.sum(UsageLedger.tokens), 0)).where(
                    UsageLedger.user_id == user_id, UsageLedger.created_at >= since
                )
            )
            return int(result.scalar() or 0)

    async def get_status(self, user, db: Optional[AsyncSession] = None) -> dict:
        dept = await self.get_department(user, db=db)
        start = current_period_start(dept['period_anchor'])
        async with get_async_db_context(db) as db:
            rows = (
                (
                    await db.execute(
                        select(UsageRequest).where(
                            UsageRequest.user_id == user.id, UsageRequest.period_start == start
                        )
                    )
                )
                .scalars()
                .all()
            )
        granted = sum(
            int(r.tokens or 0) for r in rows if r.status == 'approved' and r.action in ('topup', 'reset')
        )
        used = await self.get_used(user.id, start, db=db)
        allowance = dept['limit'] + granted
        latest = max(rows, key=lambda r: r.created_at, default=None)
        requests_used = sum(1 for r in rows if r.status != 'denied')
        return {
            'group_id': dept['group_id'],
            'group_name': dept['group_name'],
            'department_limit': dept['token_limit'],
            'limit': dept['limit'],
            'granted': granted,
            'allowance': allowance,
            'used': used,
            'remaining': max(allowance - used, 0),
            'period_start': start,
            'period_end': start + PERIOD_SECONDS,
            'blocked': used >= allowance,
            'resets_per_period': dept['resets_per_period'],
            'resets_left': max(dept['resets_per_period'] - requests_used, 0),
            'latest_request': UsageRequestModel.model_validate(latest).model_dump() if latest else None,
        }

    async def record(self, user_id: str, tokens: int, db: Optional[AsyncSession] = None):
        if tokens <= 0:
            return
        async with get_async_db_context(db) as db:
            db.add(UsageLedger(id=str(uuid.uuid4()), user_id=user_id, tokens=int(tokens), created_at=int(time.time())))
            await db.commit()

    # ---------- reset requests ----------

    async def create_request(self, user, db: Optional[AsyncSession] = None) -> tuple[Optional[dict], Optional[str]]:
        """Returns (request, error). Rejected when one is pending or the period's resets are used up."""
        status = await self.get_status(user, db=db)
        latest = status['latest_request']
        if latest and latest['status'] == 'pending':
            return None, 'You already have a pending reset request.'
        if status['resets_left'] <= 0:
            return None, 'No reset requests left for this period.'
        async with get_async_db_context(db) as db:
            row = UsageRequest(
                id=str(uuid.uuid4()),
                user_id=user.id,
                group_id=status['group_id'],
                period_start=status['period_start'],
                status='pending',
                created_at=int(time.time()),
            )
            db.add(row)
            await db.commit()
            return UsageRequestModel.model_validate(row).model_dump(), None

    async def count_pending(self, db: Optional[AsyncSession] = None) -> int:
        async with get_async_db_context(db) as db:
            result = await db.execute(select(func.count(UsageRequest.id)).where(UsageRequest.status == 'pending'))
            return int(result.scalar() or 0)

    async def list_requests(
        self, status: Optional[str] = 'pending', group_id: Optional[str] = None, db: Optional[AsyncSession] = None
    ) -> list[dict]:
        async with get_async_db_context(db) as db:
            q = select(UsageRequest).order_by(UsageRequest.created_at.asc())
            if status:
                q = q.where(UsageRequest.status == status)
            if group_id:
                q = q.where(UsageRequest.group_id == group_id)
            rows = (await db.execute(q)).scalars().all()

            user_ids = list({r.user_id for r in rows})
            users = {u.id: u for u in (await Users.get_users_by_user_ids(user_ids, db=db) if user_ids else [])}
            out = []
            for r in rows:
                cfg = await self.get_config(r.group_id, db=db) if r.group_id else None
                group = await Groups.get_group_by_id(r.group_id, db=db) if r.group_id else None
                u = users.get(r.user_id)
                out.append(
                    {
                        **UsageRequestModel.model_validate(r).model_dump(),
                        'user': {'id': r.user_id, 'name': u.name if u else r.user_id, 'email': getattr(u, 'email', None)},
                        'group_name': group.name if group else None,
                        'department_limit': cfg['token_limit'] if cfg else USAGE_DEFAULT_TOKEN_LIMIT,
                        'user_limit': int((cfg or {}).get('overrides', {}).get(r.user_id) or 0) or None,
                    }
                )
            return out

    async def decide(
        self, request_id: str, action: str, tokens: Optional[int], admin_id: str, db: Optional[AsyncSession] = None
    ) -> tuple[Optional[dict], Optional[str]]:
        if action not in ACTIONS:
            return None, 'Unknown action.'
        if action in ('topup', 'raise') and (not tokens or tokens <= 0):
            return None, 'Enter a token amount.'
        async with get_async_db_context(db) as db:
            row = await db.get(UsageRequest, request_id)
            if row is None:
                return None, 'Request not found.'
            if row.status != 'pending':
                return None, 'Request already decided.'
            user = await Users.get_user_by_id(row.user_id, db=db)
            if user is None:
                return None, 'User not found.'

            # a grant belongs to the department period it is approved in (the request may predate a
            # period restart, e.g. the admin changed the limit after the user asked)
            status = await self.get_status(user, db=db)
            row.period_start = status['period_start']

            granted = None
            if action == 'topup':
                granted = int(tokens)
            elif action == 'reset':
                # grant what was used beyond earlier grants → remaining back to the full allowance
                granted = max(status['used'] - status['granted'], 0)
            elif action == 'raise':
                await self.set_override(row.group_id, row.user_id, int(tokens), db=db)
                granted = int(tokens)

            row.status = 'denied' if action == 'deny' else 'approved'
            row.action = action
            row.tokens = granted
            row.decided_at = int(time.time())
            row.decided_by = admin_id
            await db.commit()
            return UsageRequestModel.model_validate(row).model_dump(), None

    async def group_members_usage(self, group_id: str, db: Optional[AsyncSession] = None) -> list[dict]:
        user_ids = await Groups.get_group_user_ids_by_id(group_id, db=db)
        out = []
        for uid in user_ids:
            user = await Users.get_user_by_id(uid, db=db)
            if not user:
                continue
            s = await self.get_status(user, db=db)
            out.append(
                {
                    'user': {'id': user.id, 'name': user.name, 'email': user.email},
                    'department': s['group_name'],
                    'used': s['used'],
                    'allowance': s['allowance'],
                    'blocked': s['blocked'],
                }
            )
        return out


Usage = UsageTable()
