<script lang="ts">
	// Suggested prompts as cards (thumbnail + title + subtitle), per the reference workspace.
	// Thumbnails are decorative; the prompt text is the only content.
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ArrowRight from '$lib/components/icons/ArrowRight.svelte';
	import Check from '$lib/components/icons/Check.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let prompts: { id?: string; content: string; title?: string[] }[] = [];
	export let onSelect: (e: { type: string; data: string }) => void = () => {};

	const THUMBS = ['chat', 'doc', 'bars'];
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
					{#if THUMBS[idx % THUMBS.length] === 'chat'}
						<div class="t-chat">
							<div class="b"><i class="h"></i><i></i><i style="width:70%"></i></div>
							<div class="b me"><i></i></div>
						</div>
					{:else if THUMBS[idx % THUMBS.length] === 'doc'}
						<div class="t-doc">
							<div class="paper">
								<i style="width:56%"></i><i style="width:82%"></i><i style="width:68%"></i>
								<span class="tot"><i></i><b></b></span>
							</div>
							<span class="stamp"><Check className="size-3.5" strokeWidth="3" /></span>
						</div>
					{:else}
						<div class="t-bars">
							{#each [42, 64, 50, 86, 58, 72] as h, k}
								<i class:on={k === 3 || k === 5} style="height:{h}%; animation-delay:{k * 40}ms"
								></i>
							{/each}
						</div>
					{/if}
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
			</button>
		{/each}
	</div>
</div>

<style>
	/* All colours come from theme tokens (src/lib/styles/theme-tokens.css). */
	/* Layout follows the space the cards actually get (container query), as in the reference:
	 * narrow (phone, or a squeezed panel) → 72%-wide cards in a snap-scrolling row with the next card peeking;
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
		padding: 12px 14px;
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

	/* thumb: chat bubbles */
	.t-chat {
		display: flex;
		flex-direction: column;
		gap: 6px;
		height: 100%;
	}
	.t-chat .b {
		display: flex;
		flex-direction: column;
		gap: 4px;
		width: 66%;
		padding: 7px 8px;
		border-radius: 3px 8px 8px 8px;
		background: var(--theme-surface);
		box-shadow: inset 0 0 0 1px var(--theme-line);
	}
	.t-chat .b.me {
		align-self: flex-end;
		width: 38%;
		border-radius: 8px 3px 8px 8px;
		background: var(--tcs);
		box-shadow: none;
	}
	.t-chat i {
		display: block;
		height: 5px;
		border-radius: 3px;
		background: var(--theme-line-2);
	}
	.t-chat i.h {
		width: 55%;
		background: var(--theme-ink-4);
	}
	.t-chat .me i {
		background: var(--tcl);
	}

	/* thumb: document with check stamp */
	.t-doc {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
	}
	.t-doc .paper {
		display: flex;
		flex-direction: column;
		gap: 5px;
		width: 58%;
		height: 100%;
		padding: 8px 10px;
		border-radius: 6px;
		background: var(--theme-surface);
		box-shadow:
			var(--theme-sh-1),
			inset 0 0 0 1px var(--theme-line);
	}
	.t-doc .paper > i {
		display: block;
		height: 5px;
		border-radius: 3px;
		background: var(--theme-line-2);
	}
	.t-doc .tot {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: auto;
		padding-top: 5px;
		border-top: 1px dashed var(--theme-line-2);
	}
	.t-doc .tot i {
		width: 30%;
		height: 5px;
		border-radius: 3px;
		background: var(--theme-line-2);
	}
	.t-doc .tot b {
		width: 22%;
		height: 6px;
		border-radius: 3px;
		background: var(--tc);
	}
	.t-doc .stamp {
		position: absolute;
		right: 14%;
		top: 4px;
		width: 26px;
		height: 26px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		color: var(--theme-on-accent);
		background: var(--tc);
		box-shadow: 0 0 0 3px var(--theme-bg-2);
		transform: rotate(-12deg);
	}

	/* thumb: bar chart */
	.t-bars {
		display: flex;
		align-items: flex-end;
		gap: 8px;
		height: 100%;
		padding: 0 4px;
		border-bottom: 1px solid var(--theme-line-2);
	}
	.t-bars i {
		flex: 1;
		display: block;
		border-radius: 4px 4px 1px 1px;
		background: var(--tcl);
		transform-origin: bottom;
		animation: sc-grow 0.6s var(--theme-ease) both;
	}
	.t-bars i.on {
		background: var(--tc);
	}

	/* `translate` (not `transform`) so the filled animation does not cancel the hover lift */
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
	@keyframes sc-grow {
		from {
			transform: scaleY(0);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.sc,
		.t-bars i {
			animation: none;
			opacity: 1;
		}
	}
</style>
