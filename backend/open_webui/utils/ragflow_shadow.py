"""Authenticated access to RAGFlow documents represented by metadata-only files."""

from __future__ import annotations

import os

import httpx
from fastapi import HTTPException, status


def binding(meta: dict | None) -> dict | None:
    value = (meta or {}).get('ragflow')
    return value if isinstance(value, dict) else None


def syncer_url(value: dict) -> str:
    base_url = os.getenv('OW_RAGFLOW_SYNC_BASE_URL', '').rstrip('/')
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='OW_RAGFLOW_SYNC_BASE_URL is not configured',
        )
    return (
        f"{base_url}/v1/reverse/{value['dataset_resource_id']}"
        f"/documents/{value['document_id']}"
    )


def syncer_headers(user) -> dict[str, str]:
    token = os.getenv('OW_RAGFLOW_SYNC_SERVICE_AUTH_TOKEN', '')
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='OW_RAGFLOW_SYNC_SERVICE_AUTH_TOKEN is not configured',
        )
    return {
        'Authorization': f'Bearer {token}',
        'X-OpenWebUI-User-Id': user.id,
        'X-OpenWebUI-User-Email': user.email,
        'X-OpenWebUI-User-Name': user.name,
        'X-OpenWebUI-User-Role': user.role,
    }


async def set_document_enabled(value: dict, user, *, enabled: bool) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.put(
            syncer_url(value),
            headers=syncer_headers(user),
            json={'enabled': enabled},
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'RAGFlow document update failed: {response.text[:200]}',
        )