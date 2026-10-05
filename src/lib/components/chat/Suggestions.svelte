<script lang="ts">
	import Fuse from 'fuse.js';
	import Bolt from '$lib/components/icons/Bolt.svelte';
	import SuggestionCards from './SuggestionCards.svelte'; // CUSTOM
	import { getContext } from 'svelte';
	import { settings, WEBUI_NAME } from '$lib/stores';
	import { WEBUI_VERSION } from '$lib/constants';

	const i18n = getContext('i18n');

	export let suggestionPrompts = [];
	export let className = '';
	export let inputValue = '';
	export let onSelect = () => {};

	let sortedPrompts = [];

	const fuseOptions = {
		keys: ['content', 'title'],
		threshold: 0.5
	};

	let fuse;
	let filteredPrompts = [];

	// Initialize Fuse
	$: fuse = new Fuse(sortedPrompts, fuseOptions);

	// Update the filteredPrompts if inputValue changes
	// Only increase version if something wirklich geändert hat
	$: if (fuse) getFilteredPrompts(inputValue);

	// Compare objects so translated text refreshes even when IDs stay the same.
	function arraysEqual(a, b) {
		if (a.length !== b.length) return false;
		for (let i = 0; i < a.length; i++) {
			if (a[i] !== b[i]) {
				return false;
			}
		}
		return true;
	}

	const getFilteredPrompts = (inputValue) => {
		if (inputValue.length > 500) {
			filteredPrompts = [];
		} else {
			const newFilteredPrompts =
				inputValue.trim() && fuse
					? fuse.search(inputValue.trim()).map((result) => result.item)
					: sortedPrompts;

			// Compare with the oldFilteredPrompts
			// If there's a difference, update array + version
			if (!arraysEqual(filteredPrompts, newFilteredPrompts)) {
				filteredPrompts = newFilteredPrompts;
			}
		}
	};

	$: if (suggestionPrompts) {
		sortedPrompts = [...(suggestionPrompts ?? [])].sort(() => Math.random() - 0.5);
	}
</script>

<div class="mb-1 flex gap-1 text-xs font-normal items-center text-gray-600 dark:text-gray-400">
	{#if filteredPrompts.length > 0}
		<Bolt />
		{$i18n.t('Suggested')}
	{:else}
		<!-- Keine Vorschläge -->

		<div
			class="flex w-full {$settings?.landingPageMode === 'chat'
				? ' -mt-1'
				: 'text-center items-center justify-center'}  self-start text-gray-600 dark:text-gray-400"
		>
			<!-- LICENSE covers this Open WebUI footer identifier.
			Do not alter, remove, obscure, or replace it except as LICENSE permits:
			https://docs.openwebui.com/license. -->
			{$WEBUI_NAME} ‧ v{WEBUI_VERSION}
		</div>
	{/if}
</div>

<!-- CUSTOM: suggestions shown as cards (SuggestionCards); filtering above is unchanged -->
<div class="min-h-36 w-full">
	{#if filteredPrompts.length > 0}
		<SuggestionCards prompts={filteredPrompts} {onSelect} />
	{/if}
</div>
