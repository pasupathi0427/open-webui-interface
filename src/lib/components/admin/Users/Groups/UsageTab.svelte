<script lang="ts">
	// CUSTOM: department (group) token governance — monthly limit, resets per period,
	// current period dates, members' usage and this department's pending reset requests.
	// Saves on its own (not via the group's Save), like the Users tab.
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { toast } from 'svelte-sonner';

	import { getGroupUsage, updateGroupUsage } from '$lib/apis/usage';
	import { formatTokens } from '$lib/stores/usage';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ResetRequestsTable from '$lib/components/chat/Usage/ResetRequestsTable.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let groupId: string;

	let info: any = null;
	let tokenLimit = 10_000_000;
	let resets = 2;
	let saving = false;

	const load = async () => {
		info = await getGroupUsage(localStorage.token, groupId).catch((e) => {
			toast.error(`${e}`);
			return null;
		});
		if (info) {
			tokenLimit = info.token_limit;
			resets = info.resets_per_period;
		}
	};

	const save = async () => {
		if (!(tokenLimit >= 1) || !(resets >= 0)) {
			toast.error($i18n.t('Enter valid numbers'));
			return;
		}
		saving = true;
		const res = await updateGroupUsage(localStorage.token, groupId, {
			token_limit: Math.round(tokenLimit),
			resets_per_period: Math.round(resets)
		}).catch((e) => {
			toast.error(`${e}`);
			return null;
		});
		if (res) {
			info = res;
			toast.success($i18n.t('Usage settings saved'));
		}
		saving = false;
	};

	const date = (s: number) =>
		new Date(s * 1000).toLocaleDateString(undefined, {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	$: limitChanged = info && Math.round(tokenLimit) !== info.token_limit;

	onMount(load);
</script>

{#if !info}
	<div class="flex justify-center py-8"><Spinner className="size-5" /></div>
{:else}
	<div class="flex flex-col gap-5 text-sm min-w-0">
		<div class="grid gap-4 sm:grid-cols-2">
			<label class="flex flex-col gap-1">
				<span class="text-xs text-gray-500">{$i18n.t('Monthly token limit per user')}</span>
				<input
					type="number"
					min="1"
					step="100000"
					inputmode="numeric"
					class="w-full rounded-lg bg-transparent border border-gray-100 dark:border-gray-850 px-3 py-2 outline-hidden"
					bind:value={tokenLimit}
				/>
				<span class="text-xs text-gray-500">≈ {formatTokens(Number(tokenLimit) || 0)}</span>
			</label>
			<label class="flex flex-col gap-1">
				<span class="text-xs text-gray-500">{$i18n.t('Reset requests allowed per period')}</span>
				<input
					type="number"
					min="0"
					max="100"
					inputmode="numeric"
					class="w-full rounded-lg bg-transparent border border-gray-100 dark:border-gray-850 px-3 py-2 outline-hidden"
					bind:value={resets}
				/>
			</label>
		</div>

		<div
			class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-100 dark:border-gray-850 px-3 py-2.5"
		>
			<div class="flex flex-wrap gap-x-6 gap-y-1">
				<div>
					<div class="text-xs text-gray-500">{$i18n.t('Period started')}</div>
					<div class="font-medium">{date(info.period_start)}</div>
				</div>
				<div>
					<div class="text-xs text-gray-500">{$i18n.t('Expires at')}</div>
					<div class="font-medium">{date(info.period_end)}</div>
				</div>
			</div>
			<button
				class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full disabled:opacity-50"
				disabled={saving}
				on:click={save}
			>
				{$i18n.t('Save')}
			</button>
		</div>
		{#if limitChanged}
			<p class="-mt-3 text-xs text-gray-500">
				{$i18n.t('Saving a new limit starts a new 30-day period today for everyone in this group.')}
			</p>
		{/if}

		<section class="flex flex-col gap-2">
			<h3 class="text-xs font-medium text-gray-500">{$i18n.t('Pending reset requests')}</h3>
			<ResetRequestsTable {groupId} onChange={load} />
		</section>

		<section class="flex flex-col gap-2">
			<h3 class="text-xs font-medium text-gray-500">{$i18n.t('Members this period')}</h3>
			{#if info.members.length === 0}
				<div class="text-xs text-gray-500">{$i18n.t('No members')}</div>
			{:else}
				<div class="flex flex-col divide-y divide-gray-100 dark:divide-gray-850">
					{#each info.members as m}
						{@const pct = Math.min(100, Math.round((m.used / Math.max(m.allowance, 1)) * 100))}
						<div class="flex items-center gap-3 py-2">
							<div class="min-w-0 flex-1">
								<div class="truncate">{m.user.name}</div>
								{#if m.department && m.department !== null}
									<div class="truncate text-xs text-gray-500">{m.department}</div>
								{/if}
							</div>
							<div class="w-28 sm:w-40">
								<div class="h-1.5 rounded-full bg-gray-100 dark:bg-gray-850 overflow-hidden">
									<div
										class="h-full rounded-full {m.blocked ? 'bg-red-500' : 'bg-(--theme-accent)'}"
										style="width: {pct}%"
									></div>
								</div>
							</div>
							<div class="w-24 text-right text-xs tabular-nums text-gray-500">
								{formatTokens(Math.min(m.used, m.allowance))} / {formatTokens(m.allowance)}
							</div>
						</div>
					{/each}
				</div>
			{/if}
			<p class="pt-22 text-right text-[0.6875rem] text-gray-400 dark:text-gray-500">
				{$i18n.t('Token counts are estimates and may not reflect actual API usage')}
			</p>
		</section>
	</div>
{/if}
