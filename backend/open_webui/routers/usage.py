"""CUSTOM: token usage governance API (department = group). See models/usage.py."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.models.groups import Groups
from open_webui.models.usage import PERIOD_SECONDS, Usage, current_period_start
from open_webui.utils.auth import get_admin_user, get_verified_user
from pydantic import BaseModel, Field

router = APIRouter()


@router.get('/me')
async def get_my_usage(user=Depends(get_verified_user)):
    return await Usage.get_status(user)


@router.post('/requests')
async def create_reset_request(user=Depends(get_verified_user)):
    req, error = await Usage.create_request(user)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return req


@router.get('/requests/count')
async def get_pending_count(user=Depends(get_admin_user)):
    return {'pending': await Usage.count_pending()}


@router.get('/requests')
async def list_reset_requests(
    status_filter: Optional[str] = 'pending', group_id: Optional[str] = None, user=Depends(get_admin_user)
):
    return await Usage.list_requests(status=status_filter or None, group_id=group_id)


class DecideForm(BaseModel):
    action: str
    tokens: Optional[int] = Field(default=None, ge=1)


@router.post('/requests/{request_id}/decide')
async def decide_reset_request(request_id: str, form_data: DecideForm, user=Depends(get_admin_user)):
    req, error = await Usage.decide(request_id, form_data.action, form_data.tokens, user.id)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return req


async def _group_usage(group_id: str) -> dict:
    cfg = await Usage.get_config(group_id)
    start = current_period_start(cfg['period_anchor'])
    return {
        'group_id': group_id,
        'token_limit': cfg['token_limit'],
        'resets_per_period': cfg['resets_per_period'],
        'configured': cfg['configured'],
        'overrides': cfg['overrides'],
        'period_start': start,
        'period_end': start + PERIOD_SECONDS,
        'members': await Usage.group_members_usage(group_id),
    }


@router.get('/groups/{group_id}')
async def get_group_usage(group_id: str, user=Depends(get_admin_user)):
    if not await Groups.get_group_by_id(group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Group not found.')
    return await _group_usage(group_id)


class GroupUsageForm(BaseModel):
    token_limit: int = Field(ge=1)
    resets_per_period: int = Field(ge=0, le=100)


@router.post('/groups/{group_id}')
async def update_group_usage(group_id: str, form_data: GroupUsageForm, user=Depends(get_admin_user)):
    if not await Groups.get_group_by_id(group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Group not found.')
    await Usage.set_config(group_id, form_data.token_limit, form_data.resets_per_period)
    return await _group_usage(group_id)
