<script lang="ts">
	// Landing heading in the reference layout (`.lp-hero`): greeting eyebrow, model tile + title,
	// model description. Same data and interactions as the block it replaces in Placeholder.svelte
	// (model switch on multi-model, tag tooltip, markdown description tooltip, "By" author line).
	import { getContext } from 'svelte';
	import { fade } from 'svelte/transition';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import { user } from '$lib/stores';
	import { sanitizeResponseContent } from '$lib/utils';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ModelTile from './ModelTile.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let models: any[] = [];
	export let selectedModelIdx = 0;
	export let selectedModelName = '';
	export let selectedModelDescription = '';

	const hour = new Date().getHours();
	$: firstName = ($user?.name ?? '').trim().split(/\s+/)[0];
	$: greeting =
		hour < 12
			? $i18n.t('Good morning, {{name}}', { name: firstName })
			: hour < 17
				? $i18n.t('Good afternoon, {{name}}', { name: firstName })
				: $i18n.t('Good evening, {{name}}', { name: firstName });

	$: descriptionHtml = selectedModelDescription
		? DOMPurify.sanitize(
				marked.parse(sanitizeResponseContent(selectedModelDescription).replaceAll('\n', '<br>'))
			)
		: '';
	$: author = models[selectedModelIdx]?.info?.meta?.user;
</script>

<div
	class="landing-hero w-full @md:max-w-3xl px-2.5 flex flex-col gap-2 text-left"
	in:fade={{ duration: 100 }}
>
	<!-- the title already greets when no model is selected -->
	{#if selectedModelName}
		<div class="flex items-center gap-2 text-xs font-medium text-(--theme-ink-3) tracking-wide">
			<span class="eyebrow-dot size-1.5 rounded-full" aria-hidden="true"></span>
			<span class="line-clamp-1">{greeting}</span>
		</div>
	{/if}

	<div class="flex items-center gap-3 min-w-0">
		<div class="flex shrink-0 -space-x-3">
			{#each models.length ? models : [undefined] as model, modelIdx}
				<Tooltip
					content={(model?.info?.meta?.tags ?? [])
						.map((tag: { name: string }) => tag.name.toUpperCase())
						.join(', ')}
					placement="top"
				>
					<button
						class="tile-btn block rounded-[13px] {models.length > 1 && modelIdx !== selectedModelIdx
							? 'opacity-60 hover:opacity-100'
							: ''}"
						aria-hidden={models.length <= 1}
						tabindex={models.length <= 1 ? -1 : 0}
						aria-label={$i18n.t('Get information on {{name}} in the UI', { name: model?.name })}
						on:click={() => {
							selectedModelIdx = modelIdx;
						}}
					>
						<ModelTile
							{model}
							lang={$i18n.language}
							className="size-10 @sm:size-11 rounded-[13px]"
						/>
					</button>
				</Tooltip>
			{/each}
		</div>

		<h1
			class="min-w-0 text-[1.5625rem] @sm:text-[2rem] leading-tight font-semibold tracking-tight text-(--theme-ink) line-clamp-1"
		>
			{#if selectedModelName}
				<Tooltip content={selectedModelName} placement="top" className="min-w-0">
					<span class="line-clamp-1">
						{selectedModelName}
					</span>
				</Tooltip>
			{:else}
				{$i18n.t('Hello, {{name}}', { name: $user?.name })}
			{/if}
		</h1>
	</div>

	{#if descriptionHtml}
		<Tooltip className="w-fit max-w-full" content={descriptionHtml} placement="top">
			<div
				class="text-[0.9375rem] font-normal text-(--theme-ink-2) line-clamp-2 max-w-[62ch] markdown"
			>
				{@html descriptionHtml}
			</div>
		</Tooltip>
	{/if}

	{#if author}
		<div class="text-sm font-normal text-(--theme-ink-3)">
			{$i18n.t('By')}
			{#if author.community}
				<a href="https://openwebui.com/m/{author.username}"
					>{author.name ? author.name : `@${author.username}`}</a
				>
			{:else}
				{author.name}
			{/if}
		</div>
	{/if}
</div>

<style>
	/* Reference `.lp-eyebrow .dot` (ok tone with a soft halo) */
	.eyebrow-dot {
		background: var(--theme-tone-green);
		box-shadow: 0 0 0 3px color-mix(in srgb, var(--theme-tone-green) 16%, transparent);
	}
	.tile-btn {
		transition: transform 0.35s var(--theme-spring);
	}
	.tile-btn:hover {
		transform: rotate(-6deg);
	}
	.tile-btn:focus-visible {
		outline: 2px solid var(--theme-accent);
		outline-offset: 2px;
	}
	@media (prefers-reduced-motion: reduce) {
		.tile-btn,
		.tile-btn:hover {
			transition: none;
			transform: none;
		}
	}
</style>
