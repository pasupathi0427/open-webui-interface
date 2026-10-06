<script lang="ts">
	// "Choose a model" card (reference `.mp` / `.mcard`). Lists the same models as the chat-input
	// selector ($models minus hidden), same Fuse search, same default-model save (settings.models).
	import Fuse from 'fuse.js';
	import { getContext, tick } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { toast } from 'svelte-sonner';

	import { models, settings, user } from '$lib/stores';
	import { updateUserSettings } from '$lib/apis/users';
	import {
		resolveLocalizedModelDescription,
		resolveLocalizedModelName
	} from '$lib/utils/localizedContent';
	import { modelScene } from '$lib/utils/modelScenes';

	import Modal from '$lib/components/common/Modal.svelte';
	import ModelTile, { modelTone } from './Placeholder/ModelTile.svelte';
	import Check from '$lib/components/icons/Check.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import ArrowRight from '$lib/components/icons/ArrowRight.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let show = false;
	export let selectedModelId = '';
	/** first-login welcome copy */
	export let welcome = false;
	/** chat already has messages → "Use", otherwise "Start with" */
	export let hasChat = false;
	export let onSelect: (id: string) => void = () => {};

	let query = '';
	let pick = '';
	let makeDefault = false;
	let grid: HTMLElement;

	// tags live on the model or its meta depending on the source (same lookup as the selector)
	const modelTags = (m: any): { name: string }[] => m?.tags ?? m?.info?.meta?.tags ?? [];

	$: items = ($models ?? [])
		.filter((m) => !(m?.info?.meta?.hidden ?? false))
		.map((m) => ({
			value: m.id,
			model: m,
			modelName: resolveLocalizedModelName(m, $i18n.language),
			desc: resolveLocalizedModelDescription(m, $i18n.language) ?? '',
			tags: modelTags(m)
				.map((t) => t.name)
				.join(' '),
			tag: modelTags(m)[0]?.name ?? '',
			tone: modelTone(m.id)
		}));
	$: fuse = new Fuse(items, { keys: ['value', 'tags', 'modelName'], threshold: 0.4 });
	$: shown = query.trim() ? fuse.search(query.trim()).map((r) => r.item) : items;

	$: current = items.find((i) => i.value === pick);
	$: isDefault = !!pick && ($settings?.models ?? [])[0] === pick;

	// reset every time the card opens
	let wasOpen = false;
	$: if (show !== wasOpen) {
		wasOpen = show;
		if (show) open();
	}
	const open = async () => {
		query = '';
		makeDefault = false;
		pick = items.some((i) => i.value === selectedModelId)
			? selectedModelId
			: (items[0]?.value ?? '');
		await tick();
		grid?.querySelector<HTMLElement>('[aria-checked="true"]')?.focus({ preventScroll: true });
	};

	const confirm = async () => {
		if (!current) return;
		if (makeDefault && !isDefault) {
			settings.set({ ...$settings, models: [pick] });
			await updateUserSettings(localStorage.token, { ui: { models: [pick] } }).catch((e) =>
				toast.error(`${e}`)
			);
			toast.success($i18n.t('Default model updated'));
		}
		onSelect(pick);
		show = false;
	};

	// WAI-ARIA radio group: arrows move + select, Enter confirms
	const onKeydown = (e: KeyboardEvent, id: string) => {
		const idx = shown.findIndex((i) => i.value === id);
		const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
		if (step) {
			e.preventDefault();
			const next = shown[(idx + step + shown.length) % shown.length];
			pick = next.value;
			tick().then(() =>
				grid?.querySelector<HTMLElement>(`[data-id="${CSS.escape(next.value)}"]`)?.focus()
			);
		} else if (e.key === ' ') {
			e.preventDefault();
			pick = id;
		} else if (e.key === 'Enter') {
			e.preventDefault();
			pick = id;
			confirm();
		}
	};
</script>

<Modal
	bind:show
	size="lg"
	containerClassName="p-0 sm:p-3"
	className="model-picker bg-(--theme-surface) text-(--theme-ink) rounded-[20px] max-sm:rounded-b-none max-sm:mx-0 max-sm:mb-0 max-sm:w-full flex flex-col overflow-hidden"
>
	<div class="mp-h">
		<div class="min-w-0">
			<h2 id="mp-title">{$i18n.t('Choose a model')}</h2>
			<p>
				{welcome
					? $i18n.t(
							'Welcome, {{name}}. Pick the right model for your task. You can switch anytime.',
							{
								name: ($user?.name ?? '').trim().split(/\s+/)[0]
							}
						)
					: $i18n.t('Pick the right model for your task')}
			</p>
		</div>
		<button class="mp-x" aria-label={$i18n.t('Close')} on:click={() => (show = false)}>
			<XMark className="size-4" strokeWidth="2" />
		</button>
	</div>

	<label class="mp-search">
		<Search className="size-4" strokeWidth="2" />
		<input
			bind:value={query}
			placeholder={$i18n.t('Search models')}
			autocomplete="off"
			aria-label={$i18n.t('Search models')}
		/>
	</label>

	<div class="mp-body">
		{#if shown.length}
			<div class="mp-grid" role="radiogroup" aria-labelledby="mp-title" bind:this={grid}>
				{#each shown as item, k (item.value)}
					{@const on = item.value === pick}
					<div
						class="mcard"
						class:on
						role="radio"
						aria-checked={on}
						tabindex={on || (!shown.some((i) => i.value === pick) && k === 0) ? 0 : -1}
						data-id={item.value}
						style="--tc: var(--theme-tone-{item.tone}); --i: {k}"
						aria-label="{item.modelName}. {item.desc}"
						on:click={() => (pick = item.value)}
						on:dblclick={confirm}
						on:keydown={(e) => onKeydown(e, item.value)}
					>
						<span class="mc-art">{@html modelScene(item.tone)}</span>
						{#if on}
							<span class="mc-check" aria-hidden="true"
								><Check className="size-3" strokeWidth="3" /></span
							>
						{/if}
						<span class="mc-b">
							<span class="mc-badge" aria-hidden="true">
								<ModelTile
									model={item.model}
									lang={$i18n.language}
									className="size-full rounded-[inherit]"
								/>
							</span>
							<span class="mc-t">
								<span class="truncate">{item.modelName}</span>
								{#if ($settings?.models ?? [])[0] === item.value}
									<span class="mc-def">{$i18n.t('Default')}</span>
								{/if}
							</span>
							{#if item.desc}<span class="mc-d">{item.desc}</span>{/if}
							{#if item.tag}<span class="mc-tags"><span class="mc-tag">{item.tag}</span></span>{/if}
						</span>
					</div>
				{/each}
			</div>
		{:else}
			<div class="mp-empty">
				<b>{$i18n.t('No model matches "{{query}}"', { query })}</b>
				{$i18n.t('Try a different name or tag.')}
			</div>
		{/if}
	</div>

	<div class="mp-foot">
		{#if current}
			{#if isDefault}
				<span class="mp-note"
					>{$i18n.t('{{name}} is your default', { name: current.modelName })}</span
				>
			{:else}
				<label class="mp-def">
					<input type="checkbox" bind:checked={makeDefault} />
					<span>{$i18n.t('Make {{name}} my default', { name: current.modelName })}</span>
				</label>
			{/if}
		{/if}
		<div class="mp-acts">
			<button class="mp-btn" on:click={() => (show = false)}>{$i18n.t('Cancel')}</button>
			<button class="mp-btn primary" disabled={!current} on:click={confirm}>
				<span class="truncate">
					{hasChat
						? $i18n.t('Use {{name}}', { name: current?.modelName ?? '' })
						: $i18n.t('Start with {{name}}', { name: current?.modelName ?? '' })}
				</span>
				<ArrowRight className="size-4 shrink-0" strokeWidth="2" />
			</button>
		</div>
	</div>
</Modal>

<style>
	/* Reference `.mp` (v3.1 compact) — colours from theme tokens; scene art is an asset. */
	:global(.model-picker) {
		max-height: calc(100dvh - 1.5rem);
	}
	@media (max-width: 639px) {
		:global(.model-picker) {
			max-height: 94dvh;
			margin-top: auto;
		}
	}
	.mp-h {
		flex: none;
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 16px;
		padding: 20px 22px 2px;
	}
	.mp-h h2 {
		margin: 0 0 3px;
		font-size: 22px;
		font-weight: 600;
		line-height: 1.1;
		letter-spacing: -0.025em;
	}
	.mp-h p {
		margin: 0;
		font-size: 13.5px;
		color: var(--theme-ink-3);
	}
	.mp-x {
		flex: none;
		width: 34px;
		height: 34px;
		display: grid;
		place-items: center;
		border-radius: 999px;
		border: 1px solid var(--theme-line-2);
		color: var(--theme-ink-2);
		transition: transform 0.2s var(--theme-ease);
	}
	.mp-x:hover {
		transform: rotate(90deg);
	}
	.mp-search {
		flex: none;
		display: flex;
		align-items: center;
		gap: 10px;
		height: 42px;
		margin: 14px 22px 0;
		padding: 0 14px;
		border: 1px solid var(--theme-line-2);
		border-radius: 999px;
		color: var(--theme-ink-3);
		transition:
			border-color 0.2s,
			box-shadow 0.2s;
	}
	.mp-search:focus-within {
		border-color: var(--theme-accent);
		box-shadow: 0 0 0 4px var(--theme-accent-soft);
	}
	.mp-search input {
		flex: 1;
		min-width: 0;
		border: 0;
		outline: 0;
		background: transparent;
		font-size: 14px;
		color: var(--theme-ink);
	}
	.mp-body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		padding: 14px 22px;
		scrollbar-width: thin;
		container-type: inline-size;
	}
	.mp-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 12px;
	}
	@container (max-width: 640px) {
		.mp-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	.mcard {
		position: relative;
		display: flex;
		flex-direction: column;
		min-width: 0;
		padding: 6px;
		text-align: left;
		cursor: pointer;
		border: 1.5px solid var(--theme-line);
		border-radius: 16px;
		background: var(--theme-surface);
		animation: mp-rise 0.5s var(--theme-ease) both;
		animation-delay: calc(var(--i) * 45ms);
		transition:
			transform 0.3s var(--theme-ease),
			box-shadow 0.3s,
			border-color 0.2s;
	}
	.mcard:hover {
		transform: translateY(-4px);
		box-shadow: var(--theme-sh-2);
		border-color: var(--theme-line-2);
	}
	.mcard.on {
		border-color: var(--theme-accent);
		box-shadow:
			0 0 0 4px var(--theme-accent-soft),
			var(--theme-sh-2);
	}
	.mcard:focus-visible {
		outline: 2px solid var(--theme-accent);
		outline-offset: 3px;
	}
	.mc-art {
		display: block;
		aspect-ratio: 360 / 170;
		border-radius: 11px;
		overflow: hidden;
		background: color-mix(in srgb, var(--tc) 11%, var(--theme-surface));
	}
	.mc-art :global(svg) {
		width: 100%;
		height: 100%;
		display: block;
		transition: transform 0.6s var(--theme-ease);
	}
	.mcard:hover .mc-art :global(svg) {
		transform: scale(1.045);
	}
	:global(.dark) .mc-art :global(svg) {
		filter: brightness(0.92) saturate(0.95);
	}
	/* scene micro-animations on hover (reference .sc-*) */
	.mc-art :global(.sc-sway) {
		transform-box: fill-box;
		transform-origin: 50% 100%;
	}
	.mc-art :global(.sc-spin) {
		transform-box: fill-box;
		transform-origin: center;
	}
	.mc-art :global(.sc-bob),
	.mc-art :global(.sc-grow) {
		transform-box: fill-box;
	}
	.mc-art :global(.sc-grow) {
		transform-origin: 50% 100%;
	}
	.mcard:hover :global(.sc-sway) {
		animation: mp-sway 2.6s ease-in-out infinite;
	}
	.mcard:hover :global(.sc-spin) {
		animation: mp-spin 14s linear infinite;
	}
	.mcard:hover :global(.sc-glow) {
		animation: mp-glow 1.8s ease-in-out infinite;
	}
	.mcard:hover :global(.sc-bob) {
		animation: mp-bob 2.2s ease-in-out infinite;
	}
	.mcard:hover :global(.sc-grow) {
		animation: mp-grow 0.7s var(--theme-ease) both;
	}
	.mcard:hover :global(.sc-steam) {
		animation: mp-steam 2.2s ease-in-out infinite;
	}

	.mc-check {
		position: absolute;
		top: 12px;
		right: 12px;
		z-index: 1;
		width: 22px;
		height: 22px;
		display: grid;
		place-items: center;
		border-radius: 50%;
		background: var(--theme-accent);
		color: var(--theme-on-accent);
		box-shadow: 0 0 0 2px var(--theme-surface);
	}
	.mc-b {
		position: relative;
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
		min-width: 0;
		padding: 24px 10px 10px;
	}
	.mc-badge {
		position: absolute;
		left: 10px;
		top: -19px;
		z-index: 1;
		width: 36px;
		height: 36px;
		border-radius: 12px;
		box-shadow:
			0 0 0 4px var(--theme-surface),
			0 8px 14px -8px color-mix(in srgb, var(--tc) 60%, transparent);
		transition: transform 0.35s var(--theme-spring);
	}
	.mcard:hover .mc-badge {
		transform: translateY(-3px) rotate(-6deg);
	}
	.mc-t {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
		font-size: 14.5px;
		font-weight: 600;
		letter-spacing: -0.015em;
	}
	.mc-def {
		flex: none;
		padding: 2px 6px;
		border-radius: 999px;
		font-size: 9.5px;
		font-weight: 600;
		background: var(--theme-ink);
		color: var(--theme-surface);
	}
	.mc-d {
		font-size: 12px;
		line-height: 1.45;
		color: var(--theme-ink-2);
	}
	.mc-tags {
		display: flex;
		margin-top: auto;
		padding-top: 4px;
	}
	.mc-tag {
		max-width: 100%;
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
		padding: 3px 9px;
		border-radius: 999px;
		font-size: 11px;
		font-weight: 500;
		background: color-mix(in srgb, var(--tc) 11%, var(--theme-surface));
		color: var(--tc);
	}
	.mp-empty {
		padding: 48px 16px;
		text-align: center;
		font-size: 14px;
		color: var(--theme-ink-3);
	}
	.mp-empty b {
		display: block;
		margin-bottom: 4px;
		font-size: 15px;
		color: var(--theme-ink);
	}

	.mp-foot {
		flex: none;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 12px 22px 16px;
		border-top: 1px solid var(--theme-line);
	}
	.mp-def,
	.mp-note {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 13.5px;
		color: var(--theme-ink-2);
		cursor: pointer;
	}
	.mp-def input {
		width: 18px;
		height: 18px;
		accent-color: var(--theme-accent);
	}
	.mp-acts {
		display: flex;
		gap: 8px;
		margin-left: auto;
		min-width: 0;
	}
	.mp-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		min-width: 0;
		height: 40px;
		padding: 0 16px;
		border-radius: 12px;
		border: 1px solid var(--theme-line-2);
		background: var(--theme-surface);
		color: var(--theme-ink);
		font-size: 14px;
		font-weight: 500;
		white-space: nowrap;
	}
	.mp-btn.primary {
		background: var(--theme-accent);
		border-color: var(--theme-accent);
		color: var(--theme-on-accent);
	}
	.mp-btn.primary:hover {
		background: var(--theme-accent-2);
	}
	.mp-btn.primary :global(svg) {
		transition: transform 0.2s var(--theme-ease);
	}
	.mp-btn.primary:hover :global(svg) {
		transform: translateX(3px);
	}
	.mp-btn:disabled {
		opacity: 0.5;
	}

	/* phones: bottom sheet, one horizontal card per row (reference mobile layout) */
	@media (max-width: 639px) {
		.mp-h {
			padding: 18px 18px 2px;
		}
		.mp-h h2 {
			font-size: 19px;
		}
		.mp-search {
			margin: 12px 16px 0;
			height: 44px;
		}
		.mp-body {
			padding: 12px 14px;
		}
		.mp-grid {
			grid-template-columns: 1fr;
			gap: 10px;
		}
		.mcard {
			flex-direction: row;
			align-items: stretch;
			border-radius: 18px;
		}
		.mc-art {
			flex: none;
			width: 116px;
			min-height: 104px;
			aspect-ratio: auto;
			border-radius: 13px;
		}
		.mc-b {
			padding: 6px 8px 6px 30px;
			gap: 3px;
		}
		.mc-badge {
			left: -24px;
			top: auto;
			bottom: 6px;
			width: 38px;
			height: 38px;
		}
		.mc-check {
			top: 12px;
			right: auto;
			left: 90px;
		}
		.mc-t {
			font-size: 15px;
		}
		.mc-d {
			font-size: 12.5px;
			display: -webkit-box;
			-webkit-line-clamp: 2;
			line-clamp: 2;
			-webkit-box-orient: vertical;
			overflow: hidden;
		}
		.mp-foot {
			padding: 12px 16px calc(16px + env(safe-area-inset-bottom, 0px));
		}
		.mp-acts {
			width: 100%;
		}
		.mp-acts .mp-btn {
			flex: 1;
			height: 44px;
		}
	}

	@keyframes mp-rise {
		from {
			opacity: 0;
			translate: 0 8px;
		}
	}
	@keyframes mp-sway {
		50% {
			transform: rotate(5deg);
		}
	}
	@keyframes mp-spin {
		to {
			transform: rotate(360deg);
		}
	}
	@keyframes mp-glow {
		50% {
			opacity: 0.35;
		}
	}
	@keyframes mp-bob {
		50% {
			transform: translateY(-4px);
		}
	}
	@keyframes mp-grow {
		from {
			transform: scaleY(0);
		}
	}
	@keyframes mp-steam {
		0% {
			opacity: 0;
			transform: translateY(4px);
		}
		40% {
			opacity: 0.9;
		}
		100% {
			opacity: 0;
			transform: translateY(-6px);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.mcard,
		.mcard :global(*) {
			animation: none !important;
			transition: none !important;
		}
	}
</style>
