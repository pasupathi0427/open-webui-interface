<script lang="ts">
	// CUSTOM: shown above the chat input when the user's token allowance is used up
	// (style of a Claude "response was interrupted" bar). The server enforces the block;
	// this explains it and lets the user raise a reset request to their admin.
	import { getContext, onDestroy, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { toast } from 'svelte-sonner';

	import { user } from '$lib/stores';
	import { usageStatus, refreshUsageStatus, timeUntil } from '$lib/stores/usage';
	import { createResetRequest } from '$lib/apis/usage';
	import InfoCircle from '$lib/components/icons/InfoCircle.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	let sending = false;

	onMount(() => {
		if ($user?.role !== 'admin' && !$usageStatus) refreshUsageStatus();
	});

	// while blocked, pick up the admin's decision without a reload
	let poll: ReturnType<typeof setInterval> | undefined;
	$: if ($usageStatus?.blocked && !poll) poll = setInterval(refreshUsageStatus, 60_000);
	$: if (!$usageStatus?.blocked && poll) poll = (clearInterval(poll), undefined);
	onDestroy(() => clearInterval(poll));

	$: s = $usageStatus;
	$: latest = s?.latest_request;
	$: renews = s ? timeUntil(s.period_end) : '';

	const request = async () => {
		sending = true;
		try {
			await createResetRequest(localStorage.token);
			toast.success($i18n.t('Reset request sent to your admin'));
		} catch (e) {
			toast.error(`${e}`);
		}
		await refreshUsageStatus();
		sending = false;
	};
</script>

<svelte:window on:focus={() => $usageStatus?.blocked && refreshUsageStatus()} />

{#if s?.blocked && $user?.role !== 'admin'}
	<div
		class="usage-banner flex flex-wrap items-center gap-x-3 gap-y-2 rounded-2xl border px-3.5 py-2.5 text-sm"
		role="status"
	>
		<InfoCircle className="size-4 shrink-0 text-(--theme-ink-3)" />
		<div class="flex-1 min-w-[12rem] text-(--theme-ink-2)">
			{#if latest?.status === 'pending'}
				{$i18n.t('Reset requested. Waiting for your admin to respond.')}
			{:else if s.resets_left <= 0}
				{$i18n.t("You've used your token allowance. It renews in {{time}}.", { time: renews })}
			{:else if latest?.status === 'denied'}
				{$i18n.t('Your admin declined the reset request. Your allowance renews in {{time}}.', {
					time: renews
				})}
			{:else}
				{$i18n.t(
					"You've used your token allowance for this period. Raise a reset request to your admin."
				)}
			{/if}
		</div>
		{#if latest?.status !== 'pending' && s.resets_left > 0}
			<button
				type="button"
				class="usage-banner-btn shrink-0 rounded-lg border px-3 py-1 text-sm font-medium transition disabled:opacity-50"
				disabled={sending}
				on:click={request}
			>
				{$i18n.t('Request reset')}
			</button>
		{/if}
	</div>
{/if}

<style>
	.usage-banner {
		background: var(--theme-surface);
		border-color: var(--theme-line-2);
		box-shadow: var(--theme-sh-1);
	}
	.usage-banner-btn {
		background: var(--theme-surface);
		border-color: var(--theme-line-2);
		color: var(--theme-ink);
	}
	.usage-banner-btn:hover {
		border-color: var(--theme-accent-line);
		color: var(--theme-accent-2);
	}
</style>
