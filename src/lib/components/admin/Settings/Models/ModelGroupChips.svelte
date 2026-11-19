<script lang="ts">
	// CUSTOM: model group labels on an admin model row.
	import type { ModelGroup } from '$lib/apis/modelGroups';

	export let modelId: string;
	export let groups: ModelGroup[] = [];
	export let members: Map<string, Set<string>> = new Map();

	$: own = groups.filter((g) => members.get(g.id)?.has(modelId));
</script>

{#each own as group (group.id)}
	<span
		class="inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 text-[0.6875rem] font-normal leading-4 text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-850"
	>
		<span class="size-1.5 rounded-full" style="background-color: {group.color}"></span>
		{group.name}
	</span>
{/each}
