<script lang="ts">
	// CUSTOM: one place to grant this group read access to models, tools, skills, prompts and
	// knowledge bases. Ticking a model also ticks the tools / skills / knowledge it uses, and a
	// warning lists any ticked model whose dependencies are still unticked — so a model never
	// reaches users without what it needs. Saves on its own (not via the group's Save).
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { toast } from 'svelte-sonner';

	import { getGroupAccess, updateGroupAccess, type GroupAccess } from '$lib/apis/groupAccess';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import Check from '$lib/components/icons/Check.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let groupId: string;

	type Kind = 'model' | 'tool' | 'skill' | 'prompt' | 'knowledge';
	type Dep = 'tool' | 'skill' | 'knowledge';
	const KINDS: [Kind, string][] = [
		['model', 'Models'],
		['tool', 'Tools'],
		['skill', 'Skills'],
		['prompt', 'Prompts'],
		['knowledge', 'Knowledge']
	];
	// model field holding the ids of each dependency kind
	const DEPS: [Dep, 'tool_ids' | 'skill_ids' | 'knowledge_ids'][] = [
		['tool', 'tool_ids'],
		['skill', 'skill_ids'],
		['knowledge', 'knowledge_ids']
	];

	const empty = () =>
		Object.fromEntries(KINDS.map(([k]) => [k, new Set<string>()])) as Record<Kind, Set<string>>;

	let data: GroupAccess | null = null;
	let checked = empty();
	let saved = '';
	let tab: Kind = 'model';
	let query = '';
	let saving = false;

	const snapshot = (c: Record<Kind, Set<string>>) =>
		JSON.stringify(Object.fromEntries(KINDS.map(([k]) => [k, [...c[k]].sort()])));

	const load = async () => {
		data = await getGroupAccess(localStorage.token, groupId).catch((e) => {
			toast.error(`${e}`);
			return null;
		});
		if (!data) return;
		const c = empty();
		for (const [k] of KINDS) (data[k] ?? []).forEach((i) => i.granted && c[k].add(i.id));
		checked = c;
		saved = snapshot(checked);
	};

	$: exists = Object.fromEntries(
		DEPS.map(([k]) => [k, new Set((data?.[k] ?? []).map((i) => i.id))])
	) as Record<Dep, Set<string>>;

	/** [kind, id] pairs a model depends on (only ones that still exist) */
	const depsOf = (modelId: string): [Dep, string][] => {
		const m = data?.model.find((x) => x.id === modelId);
		return DEPS.flatMap(([k, field]) =>
			((m?.[field] as string[] | undefined) ?? [])
				.filter((id) => exists[k].has(id))
				.map((id) => [k, id] as [Dep, string])
		);
	};

	const nameOf = (kind: Dep, id: string) => data?.[kind].find((x) => x.id === id)?.name ?? id;

	const toggle = (kind: Kind, id: string, on: boolean) => {
		if (on) {
			checked[kind].add(id);
			// a model brings its tools, skills and knowledge along
			if (kind === 'model') depsOf(id).forEach(([k, d]) => checked[k].add(d));
		} else {
			checked[kind].delete(id);
		}
		checked = checked;
	};

	// ticked models whose dependencies this group still cannot use
	$: gaps = data
		? data.model
				.filter((m) => checked.model.has(m.id))
				.map((m) => ({
					model: m.name,
					missing: depsOf(m.id).filter(([k, d]) => !checked[k].has(d))
				}))
				.filter((g) => g.missing.length)
		: [];

	const fixGaps = () => {
		gaps.forEach((g) => g.missing.forEach(([k, d]) => checked[k].add(d)));
		checked = checked;
	};

	$: items = data
		? (data[tab] ?? []).filter(
				(i) =>
					!query.trim() ||
					`${i.name} ${i.id} ${i.description}`.toLowerCase().includes(query.trim().toLowerCase())
			)
		: [];
	$: dirty = data ? snapshot(checked) !== saved : false;

	const setAll = (on: boolean) => items.forEach((i) => toggle(tab, i.id, on));

	const save = async () => {
		saving = true;
		try {
			await updateGroupAccess(
				localStorage.token,
				groupId,
				Object.fromEntries(KINDS.map(([k]) => [k, [...checked[k]]])) as Record<Kind, string[]>
			);
			toast.success($i18n.t('Access saved'));
			await load();
		} catch (e) {
			toast.error(`${e}`);
		}
		saving = false;
	};

	onMount(load);
</script>

{#if !data}
	<div class="flex justify-center py-8"><Spinner className="size-5" /></div>
{:else}
	<div class="flex h-full min-w-0 flex-col gap-3 text-sm">
		<div class="flex flex-wrap gap-1" role="tablist" aria-label={$i18n.t('Access type')}>
			{#each KINDS as [k, label]}
				<button
					type="button"
					role="tab"
					aria-selected={tab === k}
					class="rounded-full px-3 py-1 text-xs transition {tab === k
						? 'bg-(--theme-accent) text-(--theme-on-accent)'
						: 'bg-gray-50 text-gray-600 hover:bg-gray-100 dark:bg-gray-850 dark:text-gray-300 dark:hover:bg-gray-800'}"
					on:click={() => {
						tab = k;
						query = '';
					}}
				>
					{$i18n.t(label)}
					<span class="ml-1 opacity-60 tabular-nums"
						>{checked[k].size}/{(data[k] ?? []).length}</span
					>
				</button>
			{/each}
		</div>

		{#if gaps.length}
			<div
				class="flex flex-wrap items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300"
				role="status"
			>
				<div class="min-w-0 flex-1">
					<div class="font-medium">
						{$i18n.t("Some models use tools, skills or knowledge this group can't access")}
					</div>
					{#each gaps.slice(0, 3) as g}
						<div class="truncate">
							{g.model}: {g.missing.map(([k, d]) => nameOf(k, d)).join(', ')}
						</div>
					{/each}
					{#if gaps.length > 3}<div>+{gaps.length - 3}</div>{/if}
				</div>
				<button
					type="button"
					class="shrink-0 rounded-lg border border-amber-300 px-2.5 py-1 font-medium hover:bg-amber-100 dark:border-amber-800 dark:hover:bg-amber-900/40"
					on:click={fixGaps}>{$i18n.t('Grant missing')}</button
				>
			</div>
		{/if}

		<div class="flex items-center gap-2">
			<label
				class="flex flex-1 items-center gap-2 rounded-lg border border-gray-100 px-2.5 py-1.5 dark:border-gray-850"
			>
				<Search className="size-3.5 text-gray-400" />
				<input
					class="w-full bg-transparent text-sm outline-hidden"
					placeholder={$i18n.t('Search')}
					aria-label={$i18n.t('Search')}
					bind:value={query}
				/>
			</label>
			<button
				type="button"
				class="shrink-0 text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white"
				on:click={() => setAll(true)}>{$i18n.t('Select all')}</button
			>
			<button
				type="button"
				class="shrink-0 text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white"
				on:click={() => setAll(false)}>{$i18n.t('Clear')}</button
			>
		</div>

		<div class="min-h-0 flex-1 overflow-y-auto -mx-1 px-1">
			{#if items.length === 0}
				<div class="py-6 text-center text-xs text-gray-500">{$i18n.t('No items found')}</div>
			{:else}
				{#each items as item (item.id)}
					{@const on = checked[tab].has(item.id)}
					{@const uses = tab === 'model' ? depsOf(item.id) : []}
					<!-- one control per row (no nested checkbox button), so a click always toggles once -->
					<button
						type="button"
						role="checkbox"
						aria-checked={on}
						class="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-850"
						on:click={() => toggle(tab, item.id, !on)}
					>
						<span
							class="grid size-4 shrink-0 place-items-center rounded-[4px] border transition {on
								? 'border-(--theme-accent) bg-(--theme-accent) text-(--theme-on-accent)'
								: 'border-(--theme-line-2)'}"
							aria-hidden="true"
						>
							{#if on}<Check className="size-3" strokeWidth="3" />{/if}
						</span>
						<span class="min-w-0 flex-1">
							<span class="flex items-center gap-2">
								<span class="truncate">{item.name}</span>
								{#if item.everyone}
									<span
										class="shrink-0 rounded-full bg-gray-100 px-1.5 py-0.5 text-[0.625rem] text-gray-500 dark:bg-gray-800 dark:text-gray-400"
										title={$i18n.t('Already shared with all users')}>{$i18n.t('Everyone')}</span
									>
								{/if}
							</span>
							{#if uses.length || item.description}
								<span class="block truncate text-xs text-gray-500">
									{#if uses.length}
										{$i18n.t('Uses')}: {uses.map(([k, d]) => nameOf(k, d)).join(', ')}
									{:else}
										{item.description}
									{/if}
								</span>
							{/if}
						</span>
					</button>
				{/each}
			{/if}
		</div>

		<div
			class="flex items-center justify-between gap-2 border-t border-gray-100 pt-3 dark:border-gray-850"
		>
			<span class="text-xs text-gray-500">
				{$i18n.t('Only read access for this group is changed.')}
			</span>
			<button
				class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full disabled:opacity-50"
				disabled={!dirty || saving}
				on:click={save}
			>
				{$i18n.t('Save')}
			</button>
		</div>
	</div>
{/if}
