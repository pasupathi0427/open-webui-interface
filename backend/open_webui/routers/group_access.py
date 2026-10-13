"""CUSTOM: group access in one place (Admin › Groups › edit group › Access).

Lists every model, tool, skill, prompt and knowledge base with whether THIS group has read access, and saves the
checked set. Only this group's `read` grants are added/removed — write grants, other groups, users
and public ("everyone") sharing are never touched. Same storage and events as the per-resource
workspace "Access" screens (AccessGrants + *_ACCESS_UPDATED / SKILL_UPDATED).
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from open_webui.events import EVENTS, publish_event
from open_webui.internal.db import get_async_db_context
from open_webui.models.access_grants import (
    PRINCIPAL_TYPE_GROUP,
    PRINCIPAL_TYPE_USER,
    WILDCARD_PRINCIPAL_ID,
    AccessGrant,
    AccessGrants,
)
from open_webui.models.groups import Groups
from open_webui.models.knowledge import Knowledges
from open_webui.models.models import ModelForm, ModelMeta, ModelParams, Models
from open_webui.models.prompts import Prompts
from open_webui.models.skills import Skills
from open_webui.models.tools import Tools
from open_webui.utils.auth import get_admin_user
from open_webui.utils.models import get_all_models
from pydantic import BaseModel
from sqlalchemy import select

router = APIRouter()

TYPES = ('model', 'tool', 'skill', 'prompt', 'knowledge')
EVENT = {
    'model': EVENTS.MODEL_ACCESS_UPDATED,
    'tool': EVENTS.TOOL_ACCESS_UPDATED,
    'skill': EVENTS.SKILL_UPDATED,
    'prompt': EVENTS.PROMPT_ACCESS_UPDATED,
    'knowledge': EVENTS.KNOWLEDGE_ACCESS_UPDATED,
}


async def _grants(group_id: str) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """({type: ids this group can read}, {type: ids shared with all signed-in users})."""
    group = {t: set() for t in TYPES}
    everyone = {t: set() for t in TYPES}
    async with get_async_db_context() as db:
        rows = (
            await db.execute(
                select(AccessGrant.resource_type, AccessGrant.resource_id, AccessGrant.principal_type, AccessGrant.principal_id).filter(
                    AccessGrant.resource_type.in_(TYPES), AccessGrant.permission == 'read'
                )
            )
        ).all()
    for rtype, rid, ptype, pid in rows:
        if ptype == PRINCIPAL_TYPE_GROUP and pid == group_id:
            group[rtype].add(rid)
        elif ptype == PRINCIPAL_TYPE_USER and pid == WILDCARD_PRINCIPAL_ID:
            everyone[rtype].add(rid)
    return group, everyone


async def _models(request: Request, user) -> list[dict]:
    if not request.app.state.MODELS:
        await get_all_models(request, user=user)
    registered = {m.id: m for m in await Models.get_all_models()}
    out = []
    for m in request.app.state.MODELS.values():
        if m.get('arena') or m.get('direct'):
            continue  # arena keeps its own access list; direct models are per-user connections
        row = registered.get(m['id'])
        meta = row.meta.model_dump() if row and row.meta else {}
        out.append(
            {
                'id': m['id'],
                'name': m.get('name') or m['id'],
                'description': meta.get('description') or '',
                'tool_ids': meta.get('toolIds') or [],
                'skill_ids': meta.get('skillIds') or [],
                'knowledge_ids': [
                    k['id']
                    for k in (meta.get('knowledge') or [])
                    if isinstance(k, dict) and k.get('id') and k.get('type', 'collection') == 'collection'
                ],
            }
        )
    return sorted(out, key=lambda x: x['name'].lower())


@router.get('/{group_id}')
async def get_group_access(group_id: str, request: Request, user=Depends(get_admin_user)):
    if not await Groups.get_group_by_id(group_id):
        raise HTTPException(404, 'Group not found.')
    granted, everyone = await _grants(group_id)
    tools = [{'id': t.id, 'name': t.name, 'description': (t.meta.description if t.meta else '') or ''} for t in await Tools.get_tools(defer_content=True)]
    skills = [{'id': s.id, 'name': s.name, 'description': s.description or ''} for s in await Skills.get_skills()]
    prompts = [{'id': p.id, 'name': p.name, 'description': f'/{p.command}'} for p in await Prompts.get_prompts() if p.id]
    knowledge = [{'id': k.id, 'name': k.name, 'description': k.description or ''} for k in await Knowledges.get_knowledge_bases()]
    sections = {'model': await _models(request, user), 'tool': tools, 'skill': skills, 'prompt': prompts, 'knowledge': knowledge}
    return {
        t: [{**item, 'granted': item['id'] in granted[t], 'everyone': item['id'] in everyone[t]} for item in items]
        for t, items in sections.items()
    }


class GroupAccessForm(BaseModel):
    model: list[str] = []
    tool: list[str] = []
    skill: list[str] = []
    prompt: list[str] = []
    knowledge: list[str] = []


@router.post('/{group_id}')
async def update_group_access(group_id: str, form: GroupAccessForm, request: Request, user=Depends(get_admin_user)):
    if not await Groups.get_group_by_id(group_id):
        raise HTTPException(404, 'Group not found.')
    current, _ = await _grants(group_id)
    names = {}
    if form.model:
        names = {m['id']: m['name'] for m in await _models(request, user)}

    changed = {t: set() for t in TYPES}
    for t in TYPES:
        desired = set(getattr(form, t))
        for rid in desired - current[t]:
            if t == 'model' and not await Models.get_model_by_id(rid):
                if rid not in names:
                    continue  # unknown model id
                # provider models have no DB row until shared; non-admins cannot see them without one
                await Models.insert_new_model(
                    ModelForm(id=rid, name=names[rid], meta=ModelMeta(), params=ModelParams()), user.id
                )
            await AccessGrants.grant_access(t, rid, PRINCIPAL_TYPE_GROUP, group_id, 'read')
            changed[t].add(rid)
        for rid in current[t] - desired:
            await AccessGrants.revoke_access(t, rid, PRINCIPAL_TYPE_GROUP, group_id, 'read')
            changed[t].add(rid)

    for t, ids in changed.items():
        for rid in ids:
            if t == 'model':
                await Models.update_model_updated_at_by_id(rid)
            await publish_event(request, EVENT[t], actor=user, subject_id=rid, data={'group_id': group_id})

    return {t: sorted(ids) for t, ids in changed.items()}
