// CUSTOM: group access in one place (backend/open_webui/routers/group_access.py)
import { WEBUI_API_BASE_URL } from '$lib/constants';

export type AccessItem = {
	id: string;
	name: string;
	description: string;
	granted: boolean;
	everyone: boolean;
	tool_ids?: string[];
	skill_ids?: string[];
	knowledge_ids?: string[];
};
export type GroupAccess = Record<'model' | 'tool' | 'skill' | 'prompt' | 'knowledge', AccessItem[]>;

const call = async (token: string, groupId: string, body?: object) => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/group-access/${groupId}`, {
		method: body ? 'POST' : 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		...(body ? { body: JSON.stringify(body) } : {})
	});
	const data = await res.json().catch(() => ({}));
	if (!res.ok) throw data?.detail ?? `${res.status}`;
	return data;
};

export const getGroupAccess = (token: string, groupId: string): Promise<GroupAccess> =>
	call(token, groupId);
export const updateGroupAccess = (
	token: string,
	groupId: string,
	ids: Record<'model' | 'tool' | 'skill' | 'prompt' | 'knowledge', string[]>
) => call(token, groupId, ids);
