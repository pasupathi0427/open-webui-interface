// CUSTOM: shared token-usage state (limit banner, user-menu card, admin queue badge)
import { writable } from 'svelte/store';
import { getMyUsage, getPendingRequestCount } from '$lib/apis/usage';

export type UsageStatus = {
	group_name: string | null;
	department_limit: number;
	limit: number;
	granted: number;
	allowance: number;
	used: number;
	remaining: number;
	period_start: number;
	period_end: number;
	blocked: boolean;
	resets_per_period: number;
	resets_left: number;
	latest_request: { status: string; action: string | null; created_at: number } | null;
};

export const usageStatus = writable<UsageStatus | null>(null);
export const pendingResetCount = writable(0);

export const refreshUsageStatus = async () => {
	usageStatus.set(await getMyUsage(localStorage.token).catch(() => null));
};

export const refreshPendingResetCount = async () => {
	const res = await getPendingRequestCount(localStorage.token).catch(() => null);
	pendingResetCount.set(res?.pending ?? 0);
};

/** "12.4M", "850K", "1,200" */
export const formatTokens = (n: number) =>
	n >= 1_000_000
		? `${+(n / 1_000_000).toFixed(1)}M`
		: n >= 10_000
			? `${+(n / 1_000).toFixed(1)}K`
			: n.toLocaleString();

/** "29d 4h", "3h 10m", "5m" until `epochSeconds` */
export const timeUntil = (epochSeconds: number) => {
	const s = Math.max(0, epochSeconds - Date.now() / 1000);
	const d = Math.floor(s / 86400),
		h = Math.floor((s % 86400) / 3600),
		m = Math.floor((s % 3600) / 60);
	return d ? `${d}d ${h}h` : h ? `${h}h ${m}m` : `${m}m`;
};
