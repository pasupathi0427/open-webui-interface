<script lang="ts">
	// CUSTOM: pending token reset requests. Admin picks an action per row:
	// Top-up (adds N this period) · Reset (restore full allowance this period) ·
	// Raise limit (permanent per-user limit) · Deny (keeps the block).
	// Top-up / Raise need a token amount → "Update"; Reset / Deny → "Confirm".
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { toast } from 'svelte-sonner';

	import { decideResetRequest, getResetRequests } from '$lib/apis/usage';
	import { formatTokens, refreshPendingResetCount } from '$lib/stores/usage';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Check from '$lib/components/icons/Check.svelte';
	import ArrowPath from '$lib/components/icons/ArrowPath.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	/** limit to one department; omit for all */
	export let groupId: string | undefined = undefined;
	export let onChange: () => void = () => {};

	type Row = {
		id: string;
		user: { name: string; email?: string };
		group_name: string | null;
		department_limit: number;
		user_limit: number | null;
		created_at: number;
		action: string;
		tokens: number | null;
		busy?: boolean;
	};

	let rows: Row[] = [];
	let loading = true;

	const ACTIONS: [string, string][] = [
		['reset', 'Reset'],
		['topup', 'Top-up'],
		['raise', 'Raise limit'],
		['deny', 'Deny']
	];
	const needsTokens = (a: string) => a === 'topup' || a === 'raise';

	const load = async () => {
		loading = true;
		const res = await getResetRequests(localStorage.token, groupId).catch((e) => {
			toast.error(`${e}`);
			return [];
		});
		rows = (res ?? []).map((r: Row) => ({ ...r, action: 'reset', tokens: null }));
		loading = false;
	};

	const apply = async (row: Row) => {
		if (needsTokens(row.action) && !(Number(row.tokens) > 0)) {
			toast.error($i18n.t('Enter a token amount'));
			return;
		}
		row.busy = true;
		rows = rows;
		try {
			await decideResetRequest(
				localStorage.token,
				row.id,
				row.action,
				needsTokens(row.action) ? Number(row.tokens) : null
			);
			toast.success($i18n.t('Request updated'));
			rows = rows.filter((r) => r.id !== row.id);
			refreshPendingResetCount();
			onChange();
		} catch (e) {
			toast.error(`${e}`);
			row.busy = false;
			rows = rows;
		}
	};

	onMount(load);
</script>

{#if loading}
	<div class="flex justify-center py-6"><Spinner className="size-5" /></div>
{:else if rows.length === 0}
	<div class="py-6 text-center text-sm text-(--theme-ink-3)">
		{$i18n.t('No pending reset requests')}
	</div>
{:else}
	<!-- w-0 + min-w-full: scrolls inside the parent instead of widening it (dialogs, narrow screens) -->
	<div class="w-0 min-w-full overflow-x-auto">
		<table class="w-full min-w-[46rem] text-sm text-left">
			<thead class="text-xs text-(--theme-ink-3)">
				<tr class="border-b border-(--theme-line)">
					<th class="py-2 pr-3 font-medium">{$i18n.t('User')}</th>
					<th class="py-2 pr-3 font-medium">{$i18n.t('Department')}</th>
					<th class="py-2 pr-3 font-medium">{$i18n.t('Department limit')}</th>
					<th class="py-2 pr-3 font-medium">{$i18n.t('Action')}</th>
					<th class="py-2 pr-3 font-medium">{$i18n.t('Tokens')}</th>
					<th class="py-2 pr-3 font-medium">{$i18n.t('Requested')}</th>
					<th class="py-2 font-medium sr-only">{$i18n.t('Apply')}</th>
				</tr>
			</thead>
			<tbody>
				{#each rows as row (row.id)}
					<tr class="border-b border-(--theme-line) last:border-0 align-middle">
						<td class="py-2 pr-3">
							<div class="font-medium text-(--theme-ink) truncate max-w-[12rem]">
								{row.user.name}
							</div>
							{#if row.user.email}
								<div class="text-xs text-(--theme-ink-3) truncate max-w-[12rem]">
									{row.user.email}
								</div>
							{/if}
						</td>
						<td class="py-2 pr-3 text-(--theme-ink-2)">{row.group_name ?? $i18n.t('Default')}</td>
						<td class="py-2 pr-3 text-(--theme-ink-2) tabular-nums">
							{formatTokens(row.department_limit)}
							{#if row.user_limit}
								<div class="text-xs text-(--theme-ink-3)">
									{$i18n.t('User limit')}: {formatTokens(row.user_limit)}
								</div>
							{/if}
						</td>
						<td class="py-2 pr-3">
							<select
								class="rounded-lg border border-(--theme-line-2) bg-(--theme-surface) px-2 py-1 text-sm outline-hidden"
								aria-label={$i18n.t('Action')}
								bind:value={row.action}
							>
								{#each ACTIONS as [value, label]}
									<option {value}>{$i18n.t(label)}</option>
								{/each}
							</select>
						</td>
						<td class="py-2 pr-3">
							<input
								type="number"
								min="1"
								step="1000"
								inputmode="numeric"
								class="w-32 rounded-lg border border-(--theme-line-2) bg-(--theme-surface) px-2 py-1 text-sm outline-hidden disabled:opacity-40"
								placeholder={needsTokens(row.action) ? '500000' : '—'}
								aria-label={$i18n.t('Tokens')}
								disabled={!needsTokens(row.action)}
								bind:value={row.tokens}
							/>
						</td>
						<td class="py-2 pr-3 text-xs text-(--theme-ink-3) whitespace-nowrap">
							{new Date(row.created_at * 1000).toLocaleString()}
						</td>
						<td class="py-2">
							<Tooltip content={needsTokens(row.action) ? $i18n.t('Update') : $i18n.t('Confirm')}>
								<button
									type="button"
									class="flex size-8 items-center justify-center rounded-lg border border-(--theme-line-2) text-(--theme-ink-2) transition hover:border-(--theme-accent) hover:text-(--theme-accent) disabled:opacity-40"
									aria-label={needsTokens(row.action) ? $i18n.t('Update') : $i18n.t('Confirm')}
									disabled={row.busy}
									on:click={() => apply(row)}
								>
									{#if needsTokens(row.action)}
										<ArrowPath className="size-4" strokeWidth="2" />
									{:else}
										<Check className="size-4" strokeWidth="2.5" />
									{/if}
								</button>
							</Tooltip>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}
