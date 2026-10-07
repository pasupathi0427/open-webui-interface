<script lang="ts">
	// CUSTOM: "Chat space at a glance" strip (reference `.qc` quick-answers strip) on the landing page.
	// Admin toggle: Admin Settings › General › "Chat space at a glance" (features.enable_chat_glance, default off).
	// Data comes only from existing endpoints: /users/usage (last 14 days) and /usage/me (allowance).
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import { models } from '$lib/stores';
	import { getUserUsage } from '$lib/apis/users';
	import { usageStatus, refreshUsageStatus, formatTokens, timeUntil } from '$lib/stores/usage';
	import { resolveLocalizedModelName } from '$lib/utils/localizedContent';

	import ChartBar from '$lib/components/icons/ChartBar.svelte';
	import ChatBubbles from '$lib/components/icons/ChatBubbles.svelte';
	import Calendar from '$lib/components/icons/Calendar.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	type Day = { date: string; messages: number; tokens: number };
	let days: Day[] = [];
	let streak = 0;
	let longest = 0;
	let topModelId: string | null = null;
	let modelsUsed = 0;
	let loaded = false;

	onMount(async () => {
		refreshUsageStatus();
		const res: any = await getUserUsage(localStorage.token, { days: 14 }).catch(() => null);
		if (res) {
			days = (res.heatmap ?? []).slice(-14);
			streak = res.totals?.current_streak ?? 0;
			longest = res.totals?.longest_streak ?? 0;
			topModelId = res.insights?.most_used_model ?? null;
			modelsUsed = res.totals?.models_used ?? 0;
		}
		loaded = true;
	});

	$: week = days.slice(-7);
	$: lastWeek = days.slice(-14, -7);
	$: msgsWeek = week.reduce((a, d) => a + d.messages, 0);
	$: msgsDelta = msgsWeek - lastWeek.reduce((a, d) => a + d.messages, 0);
	$: activeDays = week.filter((d) => d.messages > 0).length;

	// sparkline for messages per day this week
	$: spark = (() => {
		const max = Math.max(1, ...week.map((d) => d.messages));
		const pts = week.map((d, i) => [
			(i / Math.max(1, week.length - 1)) * 72,
			24 - (d.messages / max) * 20 - 2
		]);
		const line = pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
		return { line, area: pts.length ? `0,24 ${line} 72,24` : '', last: pts.at(-1) };
	})();

	$: s = $usageStatus;
	$: pctLeft = s ? Math.max(0, Math.round((s.remaining / Math.max(s.allowance, 1)) * 100)) : 0;
	$: topModel = topModelId ? $models.find((m) => m.id === topModelId) : null;
	$: topModelName = topModel ? resolveLocalizedModelName(topModel, $i18n.language) : topModelId;

	const RING = 2 * Math.PI * 15;
</script>

{#if loaded}
	<section class="glance w-full" aria-label={$i18n.t('Chat space at a glance')}>
		<div class="glance-h">
			<b>{$i18n.t('At a glance')}</b>
			<span>{$i18n.t('Your last 7 days')}</span>
		</div>
		<div class="glance-track scrollbar-none">
			{#if s}
				<div class="qcc" style="--tc: var(--theme-accent); --i: 0">
					<div class="qcc-top">
						<span class="qcc-ic"><ChartBar className="size-4" strokeWidth="2" /></span>
						<span class="qcc-l">{$i18n.t('Token allowance')}</span>
					</div>
					<div class="qcc-mid">
						<div class="qcc-val">
							<span class="qcc-v">{pctLeft}%</span><span class="qcc-u">{$i18n.t('left')}</span>
						</div>
						<svg class="qcc-viz" width="38" height="38" viewBox="0 0 38 38" aria-hidden="true">
							<circle class="rg-b" cx="19" cy="19" r="15" />
							<circle
								class="rg-f"
								cx="19"
								cy="19"
								r="15"
								stroke-dasharray={RING}
								stroke-dashoffset={RING * (1 - pctLeft / 100)}
								transform="rotate(-90 19 19)"
							/>
						</svg>
					</div>
					<div class="qcc-s">
						{formatTokens(Math.min(s.used, s.allowance))} / {formatTokens(s.allowance)} · {$i18n.t(
							'resets in {{time}}',
							{ time: timeUntil(s.period_end) }
						)}
					</div>
				</div>
			{/if}

			<div class="qcc" style="--tc: var(--theme-tone-blue); --i: 1">
				<div class="qcc-top">
					<span class="qcc-ic"><ChatBubbles className="size-4" strokeWidth="2" /></span>
					<span class="qcc-l">{$i18n.t('Messages this week')}</span>
				</div>
				<div class="qcc-mid">
					<div class="qcc-val"><span class="qcc-v">{msgsWeek}</span></div>
					<svg class="qcc-viz" width="72" height="26" viewBox="0 0 72 26" aria-hidden="true">
						{#if spark.area}<polygon class="spk-a" points={spark.area} />{/if}
						<polyline class="spk-l" points={spark.line} />
						{#if spark.last}<circle
								class="spk-d"
								cx={spark.last[0]}
								cy={spark.last[1]}
								r="2.5"
							/>{/if}
					</svg>
				</div>
				<div class="qcc-s">
					{msgsDelta >= 0 ? '+' : '−'}{Math.abs(msgsDelta)}
					{$i18n.t('vs last week')}
				</div>
			</div>

			<div class="qcc" style="--tc: var(--theme-tone-green); --i: 2">
				<div class="qcc-top">
					<span class="qcc-ic"><Calendar className="size-4" strokeWidth="2" /></span>
					<span class="qcc-l">{$i18n.t('Active streak')}</span>
				</div>
				<div class="qcc-mid">
					<div class="qcc-val">
						<span class="qcc-v">{streak}</span><span class="qcc-u"
							>{streak === 1 ? $i18n.t('day') : $i18n.t('days')}</span
						>
					</div>
					<div class="viz-week" aria-hidden="true">
						{#each week as d}<i class:on={d.messages > 0}></i>{/each}
					</div>
				</div>
				<div class="qcc-s">
					{$i18n.t('{{count}} of 7 days active · best {{best}}', {
						count: activeDays,
						best: longest
					})}
				</div>
			</div>

			{#if topModelName}
				<div class="qcc" style="--tc: var(--theme-tone-violet); --i: 3">
					<div class="qcc-top">
						<span class="qcc-ic"><Sparkles className="size-4" strokeWidth="2" /></span>
						<span class="qcc-l">{$i18n.t('Top model')}</span>
					</div>
					<div class="qcc-mid">
						<div class="qcc-val min-w-0">
							<span class="qcc-v qcc-v-sm truncate">{topModelName}</span>
						</div>
					</div>
					<div class="qcc-s">{$i18n.t('{{count}} models used', { count: modelsUsed })}</div>
				</div>
			{/if}
		</div>
	</section>
{/if}

<style>
	/* reference `.qc` / `.qcc` — colours from theme tokens */
	.glance {
		container-type: inline-size;
		display: flex;
		flex-direction: column;
		gap: 8px;
		text-align: left;
	}
	.glance-h {
		display: flex;
		align-items: baseline;
		gap: 8px;
		padding: 0 2px;
		font-size: 12.5px;
		color: var(--theme-ink-3);
	}
	.glance-h b {
		font-size: 13px;
		font-weight: 600;
		color: var(--theme-ink);
	}
	.glance-track {
		display: flex;
		gap: 10px;
		overflow-x: auto;
		scroll-snap-type: x mandatory;
		overscroll-behavior-x: contain;
		padding: 4px 2px 10px;
	}
	.qcc {
		--tcs: color-mix(in srgb, var(--tc) 11%, var(--theme-surface));
		--tcl: color-mix(in srgb, var(--tc) 30%, var(--theme-surface));
		flex: 0 0 236px;
		min-width: 0;
		scroll-snap-align: start;
		display: flex;
		flex-direction: column;
		gap: 10px;
		padding: 13px 14px 12px;
		border-radius: 16px;
		background: var(--theme-surface);
		border: 1px solid var(--theme-line);
		animation: g-rise 0.5s var(--theme-ease) both;
		animation-delay: calc(var(--i) * 60ms);
		transition:
			transform 0.25s var(--theme-ease),
			box-shadow 0.25s,
			border-color 0.2s;
	}
	.qcc:hover {
		transform: translateY(-3px);
		box-shadow: var(--theme-sh-2);
		border-color: var(--tcl);
	}
	/* phones / narrow panels: exactly two cards in view, the rest swipe in (reference mobile) */
	@container (max-width: 559px) {
		.qcc {
			flex-basis: calc((100% - 10px) / 2);
			padding: 12px;
			gap: 8px;
		}
		.qcc-ic {
			width: 28px;
			height: 28px;
		}
		.qcc-v {
			font-size: 24px;
		}
		.qcc-viz {
			display: none;
		}
	}
	.qcc-top {
		display: flex;
		align-items: center;
		gap: 9px;
		min-width: 0;
	}
	.qcc-ic {
		flex: none;
		width: 32px;
		height: 32px;
		display: grid;
		place-items: center;
		border-radius: 10px;
		background: var(--tcs);
		color: var(--tc);
		transition: transform 0.3s var(--theme-spring);
	}
	.qcc:hover .qcc-ic {
		transform: rotate(-8deg) scale(1.06);
	}
	.qcc-l {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
		font-size: 12.5px;
		font-weight: 500;
		color: var(--theme-ink-2);
	}
	.qcc-mid {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 8px;
		min-height: 38px;
	}
	.qcc-val {
		display: flex;
		align-items: baseline;
		gap: 5px;
		min-width: 0;
	}
	.qcc-v {
		font-size: 26px;
		font-weight: 600;
		line-height: 1;
		letter-spacing: -0.035em;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
		color: var(--theme-ink);
	}
	.qcc-v-sm {
		font-size: 19px;
		letter-spacing: -0.02em;
	}
	.qcc-u {
		font-size: 12.5px;
		font-weight: 500;
		color: var(--theme-ink-3);
		white-space: nowrap;
	}
	.qcc-viz {
		flex: none;
		overflow: visible;
	}
	.qcc-s {
		padding-top: 8px;
		border-top: 1px dashed var(--theme-line);
		font-size: 12px;
		color: var(--theme-ink-3);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.rg-b {
		fill: none;
		stroke: var(--tcl);
		stroke-width: 4;
	}
	.rg-f {
		fill: none;
		stroke: var(--tc);
		stroke-width: 4;
		stroke-linecap: round;
		transition: stroke-dashoffset 0.9s var(--theme-ease);
	}
	.spk-a {
		fill: var(--tcs);
	}
	.spk-l {
		fill: none;
		stroke: var(--tc);
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
	.spk-d {
		fill: var(--tc);
	}
	.viz-week {
		display: flex;
		align-items: flex-end;
		gap: 3px;
	}
	.viz-week i {
		display: block;
		width: 9px;
		height: 20px;
		border-radius: 3px;
		background: var(--tcl);
	}
	.viz-week i.on {
		background: var(--tc);
	}
	@keyframes g-rise {
		from {
			opacity: 0;
			translate: 0 8px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.qcc,
		.qcc-ic,
		.rg-f {
			animation: none;
			transition: none;
		}
	}
</style>
