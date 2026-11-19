<script lang="ts">
	// CUSTOM: one-line "Name  Group" for the admin connection list, styled like the tool server rows.
	// Replaces the URL on named/grouped connections; the URL stays in the row tooltip and Edit modal.
	import { onMount } from 'svelte';
	import { loadModelGroups, modelGroups } from '$lib/apis/modelGroups';

	export let config: { name?: string; group_id?: string } | null = {};
	export let url = '';

	onMount(() => {
		if (config?.group_id) loadModelGroups(localStorage.token);
	});

	$: group = config?.group_id ? $modelGroups.find((g) => g.id === config?.group_id) : null;
</script>

<div
	class="flex min-w-0 items-baseline gap-1.5 text-sm text-gray-600 dark:text-gray-400 transition-colors duration-150 group-hover/setting-row:text-gray-900 group-focus-within/setting-row:text-gray-900 dark:group-hover/setting-row:text-white dark:group-focus-within/setting-row:text-white"
>
	<span class="truncate">{config?.name || url}</span>
	{#if group}
		<span class="shrink-0 text-gray-500">{group.name}</span>
	{/if}
</div>
