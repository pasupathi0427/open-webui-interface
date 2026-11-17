<script lang="ts">
	// CUSTOM: admin "token reset requests" shortcut in the sidebar — next to Notifications when
	// expanded, under the pinned items (Workspace) when collapsed — so a pending request stays
	// visible on every page and whichever chat tab is active. Shown only while requests are pending.
	import { getContext, onDestroy, onMount } from 'svelte';

	import { user } from '$lib/stores';
	import { pendingResetCount, watchPendingResetCount } from '$lib/stores/usage';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import QueueList from '$lib/components/icons/QueueList.svelte';
	import ResetRequestsModal from '$lib/components/chat/Usage/ResetRequestsModal.svelte';

	const i18n = getContext<any>('i18n');

	/** 'header' = expanded sidebar top bar, 'rail' = collapsed sidebar icon column */
	export let variant: 'header' | 'rail' = 'header';

	let show = false;
	let stopPoll = () => {};
	onMount(() => {
		if ($user?.role === 'admin') stopPoll = watchPendingResetCount();
	});
	onDestroy(() => stopPoll());

	$: count = $pendingResetCount;
	$: label = $i18n.t('{{count}} token reset requests', { count });
</script>

{#if $user?.role === 'admin' && count > 0}
	<Tooltip content={$i18n.t('Token reset requests')} placement={variant === 'rail' ? 'right' : 'bottom'}>
		<button
			type="button"
			class="group flex shrink-0 cursor-pointer items-center justify-center transition {variant ===
			'rail'
				? 'size-8'
				: 'size-[1.875rem] rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-900'}"
			aria-label={label}
			on:click={(e) => {
				e.stopPropagation();
				show = true;
			}}
		>
			<span
				class="relative flex items-center justify-center {variant === 'rail'
					? 'size-[calc(30px*var(--app-text-scale,1))] rounded-lg group-hover:bg-gray-100 dark:group-hover:bg-gray-900'
					: 'size-4'}"
			>
				<QueueList className="size-4" strokeWidth="1.8" />
				<span
					class="absolute {variant === 'rail'
						? 'top-0 right-0'
						: '-top-1.5 -right-2'} min-w-[0.9375rem] h-[0.9375rem] px-[0.1875rem] rounded-full bg-(--theme-accent) text-(--theme-on-accent) text-[0.5625rem] font-semibold leading-[0.9375rem] text-center"
					aria-hidden="true">{count > 99 ? '99+' : count}</span
				>
			</span>
		</button>
	</Tooltip>
{/if}
<!-- outside the count check so the modal stays open after the last request is decided -->
{#if $user?.role === 'admin'}
	<ResetRequestsModal bind:show />
{/if}
