<script lang="ts">
	// Suggested prompts as cards (thumbnail + title + subtitle), per the reference workspace.
	// Thumbnails are decorative; the prompt text is the only content.
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ArrowRight from '$lib/components/icons/ArrowRight.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
	import { SUGGESTION_THUMBS } from '$lib/utils/suggestionThumbs';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let prompts: { id?: string; content: string; title?: string[] }[] = [];
	export let onSelect: (e: { type: string; data: string }) => void = () => {};
</script>

<div class="suggestion-cards-wrap">
	<div role="list" class="suggestion-cards scrollbar-none">
		{#each prompts as prompt, idx (prompt.id || `${prompt.content}-${idx}`)}
			<!-- svelte-ignore a11y-no-interactive-element-to-noninteractive-role -->
			<button
				role="listitem"
				class="sc"
				style="animation-delay: {idx * 60}ms"
				on:click={() => onSelect({ type: 'prompt', data: prompt.content })}
			>
				<div class="sc-thumb" aria-hidden="true">
					{@html SUGGESTION_THUMBS[idx % SUGGESTION_THUMBS.length]}
					<span class="sc-go"><ArrowRight className="size-3.5" strokeWidth="2.2" /></span>
				</div>
				<div class="sc-b">
					<div class="sc-t">
						{prompt.title && prompt.title[0] !== '' ? prompt.title[0] : prompt.content}
					</div>
					<div class="sc-m">
						<span class="dot"></span>
						<span class="sc-d">
							{prompt.title && prompt.title[0] !== '' ? prompt.title[1] : $i18n.t('Prompt')}
						</span>
					</div>
				</div>
				<span class="sc-chev" aria-hidden="true"
					><ChevronRight className="size-4" strokeWidth="2" /></span
				>
			</button>
		{/each}
	</div>
</div>

<style>
	/* All colours come from theme tokens (src/lib/styles/theme-tokens.css). */
	/* Layout follows the space the cards actually get (container query), as in the reference:
	 * narrow (phone, or a squeezed panel) → plain text list (title, subtitle, chevron; no art) — see end of file;
	 * wide (tablet / desktop) → 3 equal columns. `--sc-bleed` (set by the parent to its side padding)
	 * lets the narrow row run to the screen edge instead of being cut off by the padding. */
	.suggestion-cards-wrap {
		container-type: inline-size;
		width: 100%;
	}
	.suggestion-cards {
		--tc: var(--theme-accent);
		--tcs: color-mix(in srgb, var(--tc) 11%, var(--theme-surface));
		--tcl: color-mix(in srgb, var(--tc) 30%, var(--theme-surface));
		display: grid;
		grid-auto-flow: column;
		grid-auto-columns: 72%;
		gap: 10px;
		overflow-x: auto;
		overscroll-behavior-x: contain;
		scroll-snap-type: x mandatory;
		margin-inline: calc(-1 * var(--sc-bleed, 0px));
		padding: 2px var(--sc-bleed, 0px) 6px;
		scroll-padding-inline: var(--sc-bleed, 0px);
	}
	@container (min-width: 560px) {
		.suggestion-cards {
			grid-auto-columns: calc((100% - 20px) / 3);
			margin-inline: 0;
			padding-inline: 2px;
			scroll-padding-inline: 2px;
		}
	}

	.sc {
		display: flex;
		flex-direction: column;
		min-width: 0;
		overflow: hidden;
		text-align: left;
		scroll-snap-align: start;
		border-radius: 14px;
		border: 1px solid var(--theme-line);
		background: var(--theme-surface);
		opacity: 0;
		animation: sc-rise 0.45s var(--theme-ease) forwards;
		transition:
			border-color 0.2s,
			box-shadow 0.2s,
			transform 0.2s var(--theme-ease);
	}
	.sc:hover {
		border-color: var(--tcl);
		box-shadow: var(--theme-sh-2);
		transform: translateY(-2px);
	}
	.sc:active {
		transform: translateY(-1px) scale(0.99);
	}
	.sc:focus-visible {
		outline: 2px solid var(--theme-accent);
		outline-offset: 2px;
	}

	.sc-thumb {
		position: relative;
		height: 92px;
		padding: 0;
		overflow: hidden;
		background: var(--theme-bg-2);
		border-bottom: 1px solid var(--theme-line);
	}
	.sc-go {
		position: absolute;
		top: 10px;
		right: 10px;
		width: 28px;
		height: 28px;
		border-radius: 9px;
		display: grid;
		place-items: center;
		background: var(--theme-surface);
		color: var(--tc);
		box-shadow: var(--theme-sh-1);
		opacity: 0;
		transform: translateY(4px) scale(0.9);
		transition:
			opacity 0.2s,
			transform 0.25s var(--theme-spring);
	}
	.sc:hover .sc-go,
	.sc:focus-visible .sc-go {
		opacity: 1;
		transform: none;
	}
	/* touch devices have no hover: keep the affordance visible */
	@media (hover: none) {
		.sc-go {
			opacity: 1;
			transform: none;
		}
	}

	.sc-b {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
		padding: 10px 12px 12px;
	}
	.sc-t {
		font-size: 13.5px;
		font-weight: 500;
		color: var(--theme-ink);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.sc-m {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		color: var(--theme-ink-3);
		min-width: 0;
	}
	.sc-m .dot {
		flex: none;
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--tc);
	}
	.sc-d {
		min-width: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	/* v2 suggestion art: class names → theme tokens (reference suggSVG mapping) */
	.sc-thumb :global(.sqt) {
		display: block;
		width: 100%;
		height: 100%;
	}
	.sc-thumb {
		--g1: color-mix(in srgb, var(--theme-ink-4) 70%, var(--theme-surface));
	}
	.sc-thumb :global(.cd) {
		fill: var(--theme-surface);
		stroke: var(--theme-line);
	}
	.sc-thumb :global(.sh) {
		fill: #17162c;
		fill-opacity: 0.06;
	}
	.sc-thumb :global(.a) {
		fill: var(--tc);
	}
	.sc-thumb :global(.on) {
		fill: var(--theme-on-accent);
	}
	.sc-thumb :global(.g1) {
		fill: var(--g1);
	}
	.sc-thumb :global(.g2) {
		fill: var(--theme-line-2);
	}
	/* strokes after fills so "cd ka" / "cd col" take the later stroke, as in the reference */
	.sc-thumb :global(.col) {
		fill: var(--theme-surface);
		stroke: var(--g1);
	}
	.sc-thumb :global(.kg1) {
		stroke: var(--g1);
	}
	.sc-thumb :global(.ka) {
		stroke: var(--tc);
	}
	.sc-thumb :global(.kon) {
		stroke: var(--theme-on-accent);
	}

	@keyframes sc-rise {
		from {
			opacity: 0;
			translate: 0 8px;
		}
		to {
			opacity: 1;
			translate: 0 0;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.sc {
			animation: none;
			opacity: 1;
		}
	}

	.sc-chev {
		display: none;
	}
	/* phones / narrow panels: reference mobile "Suggested questions" list (no illustrations) */
	@container (max-width: 559px) {
		.suggestion-cards {
			grid-auto-flow: row;
			grid-auto-columns: auto;
			grid-template-columns: minmax(0, 1fr);
			gap: 0;
			overflow: visible;
			margin-inline: 0;
			padding: 0;
		}
		.sc {
			flex-direction: row;
			align-items: center;
			gap: 12px;
			border: 0;
			border-bottom: 1px solid var(--theme-line);
			border-radius: 0;
			background: transparent;
		}
		/* phones: first 3 prompts only */
		.sc:nth-child(n + 4) {
			display: none;
		}
		.sc:nth-child(3) {
			border-bottom: 0;
		}
		.sc:hover {
			transform: none;
			box-shadow: none;
		}
		.sc-thumb,
		.sc-m .dot {
			display: none;
		}
		.sc-b {
			flex: 1;
			padding: 12px 2px;
		}
		.sc-t {
			white-space: normal;
		}
		.sc-chev {
			display: block;
			flex: none;
			color: var(--theme-ink-4);
		}
	}
</style>
