<script lang="ts">
	// CUSTOM: connection Name + model Group fields for the admin Add/Edit Connection modal.
	import { getContext, onMount } from 'svelte';
	import { loadModelGroups, modelGroups } from '$lib/apis/modelGroups';

	const i18n = getContext<typeof import('$lib/i18n').default>('i18n');

	export let name = '';
	export let groupId = '';

	const inputClass =
		'bg-transparent outline-hidden placeholder:text-gray-300 dark:placeholder:text-gray-700';

	onMount(() => {
		loadModelGroups(localStorage.token);
	});

	// A deleted group drops back to "None" instead of showing a blank select.
	$: if (groupId && $modelGroups.length > 0 && !$modelGroups.some((g) => g.id === groupId)) {
		groupId = '';
	}
</script>

<div class="flex gap-2 mt-1.5">
	<div class="flex flex-col w-full">
		<label for="connection-name-input" class="mb-0.5 text-xs text-gray-500">{$i18n.t('Name')}</label
		>
		<input
			id="connection-name-input"
			class={`w-full text-sm ${inputClass}`}
			type="text"
			bind:value={name}
			placeholder={$i18n.t('e.g. Qwen on SageMaker')}
			maxlength="80"
			autocomplete="off"
		/>
	</div>

	<div class="flex flex-col w-1/2 shrink-0">
		<label for="connection-group-select" class="mb-0.5 text-xs text-gray-500"
			>{$i18n.t('Model Group')}</label
		>
		<select
			id="connection-group-select"
			class="w-full text-sm bg-transparent outline-hidden dark:bg-gray-900"
			bind:value={groupId}
		>
			<option value="">{$i18n.t('None')}</option>
			{#each $modelGroups as group (group.id)}
				<option value={group.id}>{group.name}</option>
			{/each}
		</select>
	</div>
</div>
