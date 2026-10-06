<script lang="ts">
	// CUSTOM: admin queue of pending token reset requests (opened from the navbar badge)
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import ResetRequestsTable from './ResetRequestsTable.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let show = false;
</script>

<Modal bind:show size="lg" className="bg-(--theme-surface) text-(--theme-ink) rounded-[20px]">
	<div class="flex items-start justify-between gap-4 px-5 pt-5 pb-2">
		<div>
			<h2 class="text-lg font-semibold">{$i18n.t('Token reset requests')}</h2>
			<p class="text-sm text-(--theme-ink-3)">
				{$i18n.t('Choose an action for each request, then confirm.')}
			</p>
		</div>
		<button
			class="flex size-8 shrink-0 items-center justify-center rounded-full border border-(--theme-line-2) text-(--theme-ink-2)"
			aria-label={$i18n.t('Close')}
			on:click={() => (show = false)}
		>
			<XMark className="size-4" strokeWidth="2" />
		</button>
	</div>
	<div class="px-5 pb-5 max-h-[70dvh] overflow-y-auto">
		{#if show}
			<ResetRequestsTable />
		{/if}
	</div>
</Modal>
