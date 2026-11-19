// CUSTOM: admin-only model groups API (backend/open_webui/routers/model_groups.py)
import { writable } from 'svelte/store';
import { WEBUI_API_BASE_URL } from '$lib/constants';

export type ModelGroupConnection = {
	type: 'openai' | 'ollama';
	idx: number;
	name: string;
	url: string;
};

export type ModelGroup = {
	id: string;
	name: string;
	description: string;
	color: string;
	model_ids: string[];
	connections?: ModelGroupConnection[];
	connection_model_ids?: string[];
};

export type ModelGroupForm = Pick<ModelGroup, 'name' | 'description' | 'color' | 'model_ids'>;

const request = async (path: string, token: string, method = 'GET', body?: object) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/model-groups${path}`, {
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
			if (Array.isArray(error)) error = error.map((e) => e?.msg ?? `${e}`).join(', ');
			console.error(err);
			return null;
		});
	if (error) throw error;
	return res;
};

export const getModelGroups = (token: string): Promise<ModelGroup[]> => request('/', token);
export const createModelGroup = (token: string, form: ModelGroupForm): Promise<ModelGroup> =>
	request('/create', token, 'POST', form);
export const updateModelGroup = (
	token: string,
	id: string,
	form: ModelGroupForm
): Promise<ModelGroup> => request(`/id/${encodeURIComponent(id)}/update`, token, 'POST', form);
export const deleteModelGroup = (token: string, id: string): Promise<boolean> =>
	request(`/id/${encodeURIComponent(id)}/delete`, token, 'DELETE');

/** Admin views share one copy so a rename in Manage Groups shows everywhere at once. */
export const modelGroups = writable<ModelGroup[]>([]);

let inFlight: Promise<ModelGroup[]> | null = null;

/** Refreshes the store; concurrent callers (e.g. every connection row) share one request. */
export const loadModelGroups = (token: string): Promise<ModelGroup[]> => {
	inFlight ??= getModelGroups(token)
		.catch(() => null)
		.then((groups) => {
			if (groups) modelGroups.set(groups);
			return groups ?? [];
		})
		.finally(() => {
			inFlight = null;
		});
	return inFlight;
};

export const GROUP_COLORS = [
	'#6b7280',
	'#ef4444',
	'#f97316',
	'#eab308',
	'#22c55e',
	'#14b8a6',
	'#3b82f6',
	'#8b5cf6',
	'#ec4899'
];

/** {groupId: Set of member model ids} — manual members plus models served by the group's connections. */
export const groupMembers = (groups: ModelGroup[]) =>
	new Map(
		groups.map((g) => [g.id, new Set([...(g.model_ids ?? []), ...(g.connection_model_ids ?? [])])])
	);

/** True when an admin connection has a name or group, so its row shows those instead of the URL. */
export const hasConnectionLabel = (config: unknown) => {
	const c = (config ?? {}) as { name?: string; group_id?: string };
	return !!(c.name || c.group_id);
};
