// CUSTOM: token usage governance API (backend/open_webui/routers/usage.py)
import { WEBUI_API_BASE_URL } from '$lib/constants';

const request = async (path: string, token: string, method = 'GET', body?: object) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/usage${path}`, {
		method,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		...(body ? { body: JSON.stringify(body) } : {})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err?.detail ?? `${err}`;
			console.error(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const getMyUsage = (token: string) => request('/me', token);
export const createResetRequest = (token: string) => request('/requests', token, 'POST');
export const getPendingRequestCount = (token: string) => request('/requests/count', token);
export const getResetRequests = (token: string, groupId?: string) =>
	request(`/requests${groupId ? `?group_id=${encodeURIComponent(groupId)}` : ''}`, token);
export const decideResetRequest = (
	token: string,
	id: string,
	action: string,
	tokens?: number | null
) => request(`/requests/${id}/decide`, token, 'POST', { action, tokens: tokens || null });
export const getGroupUsage = (token: string, groupId: string) =>
	request(`/groups/${groupId}`, token);
export const updateGroupUsage = (
	token: string,
	groupId: string,
	form: { token_limit: number; resets_per_period: number }
) => request(`/groups/${groupId}`, token, 'POST', form);
