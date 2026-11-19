<script lang="ts">
	// CUSTOM: create / edit / delete admin model groups and pick their models.
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	import Modal from '$lib/components/common/Modal.svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import Link from '$lib/components/icons/Link.svelte';
	import {
		GROUP_COLORS,
		createModelGroup,
		deleteModelGroup,
		groupMembers,
		loadModelGroups,
		modelGroups,
		updateModelGroup,
		type ModelGroup
	} from '$lib/apis/modelGroups';

	const i18n = getContext<typeof import('$lib/i18n').default>('i18n');

	export let show = false;
	export let models: { id: string; name?: string }[] = [];
	export let onUpdate: () => void = () => {};

	let editing: ModelGroup | null = null; // null = list view; id '' = new group
	let name = '';
	let description = '';
	let color = GROUP_COLORS[0];
	let selectedIds = new Set<string>();
	let query = '';
	let saving = false;
	let showDeleteConfirm = false;

	$: members = groupMembers($modelGroups);
	$: lockedIds = new Set(editing?.connection_model_ids ?? []);
	$: connectionNames = (editing?.connections ?? []).map((c) => c.name || c.url).join(', ');
	$: sortedModels = [...models].sort((a, b) => (a.name ?? a.id).localeCompare(b.name ?? b.id));
	$: visibleModels = sortedModels.filter((m) => {
		const q = query.trim().toLowerCase();
		return !q || (m.name ?? '').toLowerCase().includes(q) || m.id.toLowerCase().includes(q);
	});
	$: if (!show) {
		editing = null;
	}

	const openEditor = (group: ModelGroup | null) => {
		editing = group ?? {
			id: '',
			name: '',
			description: '',
			color: GROUP_COLORS[0],
			model_ids: []
		};
		name = editing.name;
		description = editing.description ?? '';
		color = editing.color || GROUP_COLORS[0];
		selectedIds = new Set(editing.model_ids ?? []);
		query = '';
	};

	const toggle = (id: string) => {
		if (selectedIds.has(id)) selectedIds.delete(id);
		else selectedIds.add(id);
		selectedIds = selectedIds;
	};

	const save = async () => {
		if (!editing || saving) return;
		if (!name.trim()) {
			toast.error($i18n.t('Group name is required'));
			return;
		}
		saving = true;
		const form = {
			name: name.trim(),
			description: description.trim(),
			color,
			// Connection members follow the connection; only manual picks are stored.
			model_ids: [...selectedIds].filter((id) => !lockedIds.has(id))
		};
		try {
			if (editing.id) {
				await updateModelGroup(localStorage.token, editing.id, form);
			} else {
				await createModelGroup(localStorage.token, form);
			}
			toast.success($i18n.t('Model group saved'));
			await loadModelGroups(localStorage.token);
			editing = null;
			onUpdate();
		} catch (error) {
			toast.error(`${error}`);
		}
		saving = false;
	};

	const remove = async () => {
		if (!editing?.id) return;
		try {
			await deleteModelGroup(localStorage.token, editing.id);
			toast.success($i18n.t('Model group deleted'));
			await loadModelGroups(localStorage.token);
			editing = null;
			onUpdate();
		} catch (error) {
			toast.error(`${error}`);
		}
	};
</script>

<ConfirmDialog
	title={$i18n.t('Delete Model Group')}
	message={$i18n.t(
		'Delete **{{name}}**? Models are not deleted, and connections using this group are set to no group.',
		{ name: editing?.name ?? '' }
	)}
	bind:show={showDeleteConfirm}
	onConfirm={remove}
/>

<Modal ariaLabel={$i18n.t('Model Groups')} size="md" bind:show>
	<div class="flex flex-col dark:text-gray-100">
		<div class="flex items-center justify-between px-5 pt-4 pb-2">
			<div class="flex items-center gap-1.5">
				{#if editing}
					<button
						type="button"
						class="p-1 -ml-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850"
						aria-label={$i18n.t('Back')}
						on:click={() => (editing = null)}
					>
						<ChevronLeft className="size-4" />
					</button>
				{/if}
				<h1 class="text-lg font-medium font-primary">
					{#if !editing}
						{$i18n.t('Model Groups')}
					{:else if editing.id}
						{$i18n.t('Edit Model Group')}
					{:else}
						{$i18n.t('New Model Group')}
					{/if}
				</h1>
			</div>
			<button type="button" aria-label={$i18n.t('Close modal')} on:click={() => (show = false)}>
				<XMark className="size-5" />
			</button>
		</div>

		<div class="px-5 pb-4 text-sm">
			{#if !editing}
				<div class="mb-2 flex items-center justify-between">
					<div class="text-xs text-gray-500">
						{$i18n.t('Organise models by category. Groups are only used in admin settings.')}
					</div>
					<button
						type="button"
						class="flex shrink-0 items-center gap-1 rounded-xl px-2.5 py-1 text-xs font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-850 dark:hover:bg-gray-800 transition"
						on:click={() => openEditor(null)}
					>
						<Plus className="size-3" strokeWidth="2.5" />
						{$i18n.t('New Group')}
					</button>
				</div>

				{#if $modelGroups.length === 0}
					<div class="py-8 text-center text-xs text-gray-500">
						{$i18n.t('No model groups yet.')}
					</div>
				{:else}
					<div class="max-h-[60vh] overflow-y-auto space-y-px">
						{#each $modelGroups as group (group.id)}
							<button
								type="button"
								class="flex w-full items-center gap-2.5 rounded-xl px-2 py-1.5 text-left hover:bg-gray-50 dark:hover:bg-gray-850/50"
								on:click={() => openEditor(group)}
							>
								<span class="size-2.5 shrink-0 rounded-full" style="background-color: {group.color}"
								></span>
								<div class="min-w-0 flex-1">
									<div class="truncate">{group.name}</div>
									{#if group.description}
										<div class="truncate text-xs text-gray-500">{group.description}</div>
									{/if}
								</div>
								{#if (group.connections ?? []).length > 0}
									<Tooltip
										content={(group.connections ?? []).map((c) => c.name || c.url).join(', ')}
									>
										<Link className="size-3.5 text-gray-400" />
									</Tooltip>
								{/if}
								<span class="shrink-0 text-xs text-gray-500">
									{$i18n.t('{{COUNT}} models', { COUNT: members.get(group.id)?.size ?? 0 })}
								</span>
							</button>
						{/each}
					</div>
				{/if}
			{:else}
				<form class="flex flex-col gap-2.5" on:submit|preventDefault={save}>
					<div class="flex gap-3">
						<div class="flex flex-1 flex-col">
							<label for="model-group-name" class="mb-0.5 text-xs text-gray-500"
								>{$i18n.t('Name')}</label
							>
							<input
								id="model-group-name"
								class="w-full bg-transparent outline-hidden placeholder:text-gray-300 dark:placeholder:text-gray-700"
								bind:value={name}
								maxlength="64"
								placeholder={$i18n.t('e.g. Vision models')}
								required
							/>
						</div>
						<div class="flex flex-col">
							<div class="mb-1 text-xs text-gray-500">{$i18n.t('Color')}</div>
							<div class="flex gap-1">
								{#each GROUP_COLORS as swatch}
									<button
										type="button"
										class="size-4 rounded-full transition {color === swatch
											? 'ring-2 ring-offset-1 ring-gray-400 dark:ring-offset-gray-900'
											: ''}"
										style="background-color: {swatch}"
										aria-label={swatch}
										on:click={() => (color = swatch)}
									></button>
								{/each}
							</div>
						</div>
					</div>

					<div class="flex flex-col">
						<label for="model-group-description" class="mb-0.5 text-xs text-gray-500"
							>{$i18n.t('Description')}</label
						>
						<input
							id="model-group-description"
							class="w-full bg-transparent outline-hidden placeholder:text-gray-300 dark:placeholder:text-gray-700"
							bind:value={description}
							maxlength="500"
							placeholder={$i18n.t('Optional')}
						/>
					</div>

					<div class="flex flex-col">
						<div class="mb-1 flex items-center justify-between text-xs text-gray-500">
							<span>{$i18n.t('Models')}</span>
							<span>{new Set([...selectedIds, ...lockedIds]).size}</span>
						</div>
						{#if connectionNames}
							<div class="mb-1 text-xs text-gray-500">
								{$i18n.t('Models from {{connections}} are included through their connection.', {
									connections: connectionNames
								})}
							</div>
						{/if}
						<div
							class="flex items-center gap-2 rounded-xl px-2 py-1 bg-gray-50 dark:bg-gray-850/50"
						>
							<Search className="size-3.5 text-gray-400" />
							<input
								class="w-full bg-transparent text-sm outline-hidden"
								bind:value={query}
								placeholder={$i18n.t('Search Models')}
								aria-label={$i18n.t('Search Models')}
							/>
						</div>
						<div class="mt-1 max-h-[40vh] overflow-y-auto space-y-px">
							{#each visibleModels as model (model.id)}
								{@const locked = lockedIds.has(model.id)}
								<div
									class="flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-850/50"
								>
									<Checkbox
										state={locked || selectedIds.has(model.id) ? 'checked' : 'unchecked'}
										disabled={locked}
										ariaLabel={model.name ?? model.id}
										on:change={() => toggle(model.id)}
									/>
									<button
										type="button"
										class="min-w-0 flex-1 truncate text-left {locked ? 'cursor-default' : ''}"
										on:click={() => !locked && toggle(model.id)}
									>
										{model.name ?? model.id}
									</button>
									{#if locked}
										<span class="shrink-0 text-[0.6875rem] text-gray-500"
											>{$i18n.t('via connection')}</span
										>
									{/if}
								</div>
							{:else}
								<div class="py-4 text-center text-xs text-gray-500">
									{$i18n.t('No models found')}
								</div>
							{/each}
						</div>
					</div>

					<div class="flex items-center justify-between pt-1 text-sm font-medium">
						<div>
							{#if editing.id}
								<button
									type="button"
									class="px-3.5 py-1.5 rounded-full text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 transition"
									on:click={() => (showDeleteConfirm = true)}
								>
									{$i18n.t('Delete')}
								</button>
							{/if}
						</div>
						<button
							type="submit"
							class="px-3.5 py-1.5 rounded-full bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 transition disabled:opacity-50"
							disabled={saving}
						>
							{$i18n.t('Save')}
						</button>
					</div>
				</form>
			{/if}
		</div>
	</div>
</Modal>
