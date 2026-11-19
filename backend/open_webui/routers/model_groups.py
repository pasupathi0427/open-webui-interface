"""CUSTOM: admin-only model groups (Admin › Settings › Models › Manage Groups).

A group is a named, coloured bucket for organising models in the admin Models list. Stored as one
list under the `models.groups` config key — no table, no migration. A model belongs to a group when
its id is in the group's `model_ids`, or when it comes from a connection whose config carries that
group's id as `group_id` (Admin › Settings › Connections › Edit Connection › Group). Groups have no
effect on access control or on the chat model picker.
"""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from open_webui.models.config import Config
from open_webui.utils.auth import get_admin_user
from open_webui.utils.models import get_all_models
from pydantic import BaseModel, Field, field_validator

router = APIRouter()

GROUPS_KEY = 'models.groups'
CONNECTION_KEYS = {'openai': 'openai.api_configs', 'ollama': 'ollama.api_configs'}
URL_KEYS = {'openai': 'openai.api_base_urls', 'ollama': 'ollama.base_urls'}
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


class ModelGroupForm(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(default='', max_length=500)
    color: str = '#6b7280'
    model_ids: list[str] = []

    @field_validator('name', 'description')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator('color')
    @classmethod
    def check_color(cls, value: str) -> str:
        if not COLOR_PATTERN.match(value):
            raise ValueError('color must be a #rrggbb hex value')
        return value.lower()

    @field_validator('model_ids')
    @classmethod
    def dedupe_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(i for i in value if i))


async def _stored_groups() -> list[dict]:
    groups = await Config.get(GROUPS_KEY) or []
    return [g for g in groups if isinstance(g, dict) and g.get('id')]


def _check_name(groups: list[dict], name: str, exclude_id: str | None = None) -> None:
    if not name:
        raise HTTPException(status_code=400, detail='Group name is required')
    if any(g['id'] != exclude_id and g.get('name', '').lower() == name.lower() for g in groups):
        raise HTTPException(status_code=400, detail='A model group with this name already exists')


async def _connections_by_group() -> dict[str, list[dict]]:
    """{group_id: [{type, idx, name, url}]} from the OpenAI and Ollama connection configs."""
    values = await Config.get_many(*CONNECTION_KEYS.values(), *URL_KEYS.values())
    out: dict[str, list[dict]] = {}
    for kind, key in CONNECTION_KEYS.items():
        urls = values.get(URL_KEYS[kind]) or []
        configs = values.get(key) or {}
        for idx, url in enumerate(urls):
            config = configs.get(str(idx), configs.get(url, {})) or {}
            group_id = config.get('group_id')
            if group_id:
                out.setdefault(group_id, []).append(
                    {'type': kind, 'idx': idx, 'name': config.get('name') or '', 'url': url}
                )
    return out


async def _connection_model_ids(request: Request, user, connections: dict[str, list[dict]]) -> dict[str, list[str]]:
    """{group_id: model ids served by that group's connections}, from the live model list."""
    if not connections:
        return {}
    if not request.app.state.MODELS:
        await get_all_models(request, user=user)
    owner = {(c['type'], c['idx']): gid for gid, items in connections.items() for c in items}
    out: dict[str, list[str]] = {}
    for model in request.app.state.MODELS.values():
        if model.get('owned_by') == 'openai' and 'urlIdx' in model:
            indexes = [model['urlIdx']]
            kind = 'openai'
        elif model.get('owned_by') == 'ollama':
            indexes = (model.get('ollama') or {}).get('urls') or []
            kind = 'ollama'
        else:
            continue
        for idx in indexes:
            gid = owner.get((kind, idx))
            if gid and model['id'] not in out.setdefault(gid, []):
                out[gid].append(model['id'])
    return out


@router.get('/')
async def get_model_groups(request: Request, user=Depends(get_admin_user)) -> list[dict]:
    groups = await _stored_groups()
    connections = await _connections_by_group()
    connection_models = await _connection_model_ids(request, user, connections)
    return [
        {
            **g,
            'connections': connections.get(g['id'], []),
            'connection_model_ids': connection_models.get(g['id'], []),
        }
        for g in groups
    ]


@router.post('/create')
async def create_model_group(form: ModelGroupForm, user=Depends(get_admin_user)) -> dict:
    groups = await _stored_groups()
    _check_name(groups, form.name)
    group = {'id': str(uuid.uuid4()), **form.model_dump()}
    await Config.upsert({GROUPS_KEY: [*groups, group]})
    return group


@router.post('/id/{group_id}/update')
async def update_model_group(group_id: str, form: ModelGroupForm, user=Depends(get_admin_user)) -> dict:
    groups = await _stored_groups()
    if not any(g['id'] == group_id for g in groups):
        raise HTTPException(status_code=404, detail='Model group not found')
    _check_name(groups, form.name, exclude_id=group_id)
    group = {'id': group_id, **form.model_dump()}
    await Config.upsert({GROUPS_KEY: [group if g['id'] == group_id else g for g in groups]})
    return group


@router.delete('/id/{group_id}/delete')
async def delete_model_group(group_id: str, user=Depends(get_admin_user)) -> bool:
    groups = await _stored_groups()
    if not any(g['id'] == group_id for g in groups):
        raise HTTPException(status_code=404, detail='Model group not found')
    updates: dict = {GROUPS_KEY: [g for g in groups if g['id'] != group_id]}
    # Unassign the group from connections so no connection points at a missing group.
    for key in CONNECTION_KEYS.values():
        configs = await Config.get(key) or {}
        if any((c or {}).get('group_id') == group_id for c in configs.values()):
            updates[key] = {
                k: ({kk: vv for kk, vv in c.items() if kk != 'group_id'} if (c or {}).get('group_id') == group_id else c)
                for k, c in configs.items()
            }
    await Config.upsert(updates)
    return True
