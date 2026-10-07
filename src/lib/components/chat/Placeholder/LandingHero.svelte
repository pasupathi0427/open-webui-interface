<script lang="ts">
	// Landing greeting: "Good morning/afternoon/evening, <First name>" with a soft welcome line.
	// Owner: no model tile / model name / description above the chat input; warm and visible.
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import { user } from '$lib/stores';

	const i18n: Writable<i18nType> = getContext('i18n');

	const hour = new Date().getHours();
	$: first = ($user?.name ?? '').trim().split(/\s+/)[0] ?? '';
	$: name = first.charAt(0).toUpperCase() + first.slice(1);
	// greeting with the name wrapped so it can be tinted; falls back to plain text if the
	// translation drops the {{name}} placeholder
	$: [before, after] = (
		hour < 12
			? $i18n.t('Good morning, {{name}}', { name: '\u0000' })
			: hour < 17
				? $i18n.t('Good afternoon, {{name}}', { name: '\u0000' })
				: $i18n.t('Good evening, {{name}}', { name: '\u0000' })
	).split('\u0000');
</script>

<div class="landing-greet w-full @md:max-w-3xl px-2.5 text-left">
	<h1
		class="text-[1.75rem] @sm:text-[1.5rem] leading-tight font-medium tracking-tight text-(--theme-ink)"
	>
		{before}{#if after !== undefined}<span class="greet-name">{name}</span>{after}{/if}
	</h1>
	<p class="mt-1 text-[0.9375rem] text-(--theme-ink-3)">
		{$i18n.t("It's good to see you. What shall we work on today?")}
	</p>
</div>

<style>
	.landing-greet {
		animation: greet-rise 0.5s var(--theme-ease) both;
	}
	/* the name carries the accent, like the reference `.lp-wm` */
	.greet-name {
		color: var(--theme-accent);
	}
	@keyframes greet-rise {
		from {
			opacity: 0;
			translate: 0 6px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.landing-greet {
			animation: none;
		}
	}
</style>
