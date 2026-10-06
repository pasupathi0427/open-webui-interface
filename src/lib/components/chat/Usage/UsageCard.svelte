<script lang="ts">
	// CUSTOM: compact "Monthly usage limit" card for the profile menu
	// (resets countdown, % remaining, bar; style of a plan-limits card).
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import { usageStatus, refreshUsageStatus, timeUntil, formatTokens } from '$lib/stores/usage';

	const i18n: Writable<i18nType> = getContext('i18n');

	onMount(refreshUsageStatus);

	$: s = $usageStatus;
	$: pctLeft = s ? Math.max(0, Math.round((s.remaining / Math.max(s.allowance, 1)) * 100)) : 0;
</script>

{#if s}
	<div
		class="usage-card mx-1 my-1 rounded-xl border px-3 py-2.5"
		role="group"
		aria-label={$i18n.t('Monthly usage limit')}
	>
		<div class="truncate text-[0.8125rem] font-medium text-(--theme-ink)">
			{$i18n.t('Monthly usage limit')}
		</div>
		<div
			class="mt-0.5 flex items-baseline justify-between gap-2 text-[0.6875rem] text-(--theme-ink-3)"
		>
			<span>{$i18n.t('Resets in {{time}}', { time: timeUntil(s.period_end) })}</span>
			<span class={s.blocked ? 'text-red-600 dark:text-red-400 font-medium' : ''}>
				{$i18n.t('{{percent}}% remaining', { percent: pctLeft })}
			</span>
		</div>
		<div
			class="mt-2 h-1.5 overflow-hidden rounded-full bg-(--theme-bg-3)"
			role="progressbar"
			aria-valuemin="0"
			aria-valuemax="100"
			aria-valuenow={pctLeft}
		>
			<div
				class="h-full rounded-full transition-[width] duration-500 {s.blocked
					? 'bg-red-500'
					: pctLeft <= 20
						? 'bg-amber-500'
						: 'bg-(--theme-accent)'}"
				style="width: {pctLeft}%"
			></div>
		</div>
		<!-- shown capped at the allowance; the last reply may run past it -->
		<div class="mt-1 text-right text-[0.6875rem] tabular-nums text-(--theme-ink-3)">
			{formatTokens(Math.min(s.used, s.allowance))} / {formatTokens(s.allowance)}
		</div>
	</div>
{/if}

<style>
	.usage-card {
		background: var(--theme-bg-2);
		border-color: var(--theme-line);
	}
</style>
