<script lang="ts">
	import { getContext, onDestroy, onMount, tick, type Snippet } from 'svelte';
	import { toast } from 'svelte-sonner';

	import {
		WEBUI_NAME,
		artifactContents,
		banners,
		chatId,
		chatTitle as _chatTitle,
		config,
		mobile,
		models, // CUSTOM
		selectedTerminalId,
		settings,
		showSidebar,
		showTabs,
		temporaryChatEnabled,
		user
	} from '$lib/stores';

	import { slide } from 'svelte/transition';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	import ShareChatModal from '../chat/ShareChatModal.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import Menu from '$lib/components/layout/Navbar/Menu.svelte';
	import AdjustmentsHorizontal from '../icons/AdjustmentsHorizontal.svelte';

	import PencilSquare from '../icons/PencilSquare.svelte';
	import Banner from '../common/Banner.svelte';
	import Sidebar from '../icons/Sidebar.svelte';

	import ChatBubbleDotted from '../icons/ChatBubbleDotted.svelte';
	import ChatBubbleDottedChecked from '../icons/ChatBubbleDottedChecked.svelte';

	import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
	import ChatPlus from '../icons/ChatPlus.svelte';
	import ChatCheck from '../icons/ChatCheck.svelte';
	import SplitPanel from '../icons/SplitPanel.svelte';
	import Sparkles from '$lib/components/layout/Sidebar/icons/Sparkles.svelte';
	import { isTemporaryChatId } from '$lib/utils/chatId';
	import { updateUserSettings } from '$lib/apis/users'; // CUSTOM
	import ModelPickerModal from './ModelPickerModal.svelte'; // CUSTOM
	import ModelTile from './Placeholder/ModelTile.svelte'; // CUSTOM
	import ResetRequestsModal from './Usage/ResetRequestsModal.svelte'; // CUSTOM
	import QueueList from '../icons/QueueList.svelte'; // CUSTOM
	import { pendingResetCount, watchPendingResetCount } from '$lib/stores/usage'; // CUSTOM
	import { createMessagesList } from '$lib/utils';
	import { generateTitle } from '$lib/apis';
	import { updateChatById } from '$lib/apis/chats';
	import { getOutputText } from './Messages/structuredOutput';
	import { refreshChatList, refreshFolderChatLists } from '$lib/stores/chatList';
	import ChatParticipants from '$lib/components/common/ChatParticipants.svelte';

	const i18n: any = getContext('i18n');

	export let initNewChat: Function;
	export let readOnly: boolean = false;
	export let liveParticipants: { id: string; name: string }[] = [];
	export let shareEnabled: boolean = false;
	export let scrollTop = 0;
	export let scrollToTop: (() => void) | null = null;

	export let chat: any;
	export let history: any;
	export let title = '';
	export let tabbed = false;
	export let tabTitleEditor: Snippet | undefined = undefined;
	export let tabActions: Snippet | undefined = undefined;
	export let tabBarActions: Snippet | undefined = undefined;
	$: tabTitleEditor = confirmEdit ? renderTitleEditor : undefined;
	$: tabActions = renderChatActions;
	$: tabBarActions = renderTabBarActions;
	export let onSaveTempChat: () => {};
	export let archiveChatHandler: (id: string) => void;
	export let deleteChatHandler: (id: string) => void;
	export let moveChatHandler: (id: string, folderId: string) => void;

	// CUSTOM: "Choose model" card — opened from the navbar button, and once on first login
	export let selectedModelId = '';
	export let onChooseModel: (id: string) => void = () => {};
	let showModelPicker = false;
	let pickerWelcome = false;

	// CUSTOM: admin queue of token reset requests
	let showResetRequests = false;
	let stopResetPoll = () => {};
	onMount(() => {
		if ($user?.role === 'admin') stopResetPoll = watchPendingResetCount();
	});
	onDestroy(() => stopResetPoll());
	$: if (
		!pickerWelcome &&
		$settings &&
		$settings.hasSeenModelPicker !== true &&
		!chat?.id &&
		($models ?? []).filter((m) => !(m?.info?.meta?.hidden ?? false)).length > 1
	) {
		pickerWelcome = true;
		showModelPicker = true;
	}
	$: if (pickerWelcome && !showModelPicker && $settings?.hasSeenModelPicker !== true) {
		settings.set({ ...$settings, hasSeenModelPicker: true });
		updateUserSettings(localStorage.token, { ui: { hasSeenModelPicker: true } }).catch(
			console.error
		);
	}

	let closedBannerIds = [];

	const getDismissedBannerIds = (): string[] => {
		try {
			return JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]');
		} catch {
			return [];
		}
	};

	let showShareChatModal = false;
	let showDownloadChatModal = false;

	let confirmEdit = false;
	let chatTitle = '';
	let chatTitleInput: HTMLInputElement;
	let generating = false;

	const renameHandler = async () => {
		chatTitle = title || chat?.chat?.title || '';
		confirmEdit = true;

		await tick();
		setTimeout(() => {
			chatTitleInput?.focus();
			chatTitleInput?.select();
		}, 0);
	};

	const editChatTitle = async () => {
		// Disabling the field to generate a title blurs it, which would save the empty field
		if (!confirmEdit || generating) return;
		confirmEdit = false;

		const newTitle = chatTitle.trim();
		if (newTitle === (title || chat?.chat?.title)) return;
		if (!newTitle) {
			toast.error($i18n.t('Title cannot be an empty string.'));
			return;
		}

		const res = await updateChatById(localStorage.token, chat.id, { title: newTitle }).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);
		if (!res) return;

		if (chat.id === $chatId) {
			_chatTitle.set(newTitle);
		}
		await refreshChatList(localStorage.token, { refreshPinned: true });
		await refreshFolderChatLists();
	};

	const generateTitleHandler = async () => {
		generating = true;
		chatTitle = '';

		const messages = createMessagesList(history, history.currentId).map((message) => ({
			role: message.role,
			content: getOutputText(message.output) || message.content || ''
		}));
		const model = chat.chat.models.find((modelId: string) => modelId) ?? '';

		const generatedTitle = await generateTitle(localStorage.token, model, messages).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);
		generating = false;

		chatTitle = generatedTitle || title;
		await editChatTitle();
	};
</script>

{#snippet renderTitleEditor()}
	<input
		bind:this={chatTitleInput}
		bind:value={chatTitle}
		class="min-w-0 flex-1 bg-transparent md:py-1 text-[0.9375rem] font-normal text-gray-700 outline-hidden dark:text-gray-300"
		aria-label={$i18n.t('Title')}
		placeholder={generating ? $i18n.t('Generating...') : ''}
		disabled={generating}
		on:keydown={(e) => {
			if (e.isComposing || e.keyCode === 229) return;

			if (e.key === 'Enter') {
				e.preventDefault();
				editChatTitle();
			} else if (e.key === 'Escape') {
				e.preventDefault();
				confirmEdit = false;
			}
		}}
		on:blur={editChatTitle}
	/>

	<Tooltip content={$i18n.t('Generate')}>
		<button
			class="flex size-6 shrink-0 cursor-pointer items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-50/40 hover:text-gray-700 disabled:cursor-not-allowed dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-200"
			id="generate-title-button"
			aria-label={$i18n.t('Generate')}
			disabled={generating}
			on:mousedown={(e) => e.preventDefault()}
			on:click={() => {
				generateTitleHandler();
			}}
		>
			<Sparkles strokeWidth="1.5" />
		</button>
	</Tooltip>
{/snippet}

{#snippet renderTemporaryChatToggle()}
	{#if $user?.role === 'user' ? ($user?.permissions?.chat?.temporary ?? true) && !($user?.permissions?.chat?.temporary_enforced ?? false) : true}
		{#if !chat?.id}
			<Tooltip content={$i18n.t(`Temporary Chat`)}>
				<button
					class="flex size-6 cursor-pointer items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-50/40 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-200"
					id="temporary-chat-button"
					on:click={async () => {
						if (($settings?.temporaryChatByDefault ?? false) && $temporaryChatEnabled) {
							// for proper initNewChat handling
							await temporaryChatEnabled.set(null);
						} else {
							await temporaryChatEnabled.set(!$temporaryChatEnabled);
						}

						if ($page.url.pathname !== '/' && !$page.url.pathname.startsWith('/folders/')) {
							await goto('/');
						}

						// add 'temporary-chat=true' to the URL
						if ($temporaryChatEnabled) {
							window.history.replaceState(window.history.state, '', '?temporary-chat=true');
						} else {
							window.history.replaceState(window.history.state, '', location.pathname);
						}
					}}
					aria-label={$i18n.t(`Temporary Chat`)}
				>
					{#if $temporaryChatEnabled}
						<ChatBubbleDottedChecked className="size-4" strokeWidth="1.5" />
					{:else}
						<ChatBubbleDotted className="size-4" strokeWidth="1.5" />
					{/if}
				</button>
			</Tooltip>
		{/if}
	{/if}
{/snippet}

<!-- CUSTOM: our navbar buttons. Rendered in the navbar row, and in the tab bar when the tab
     workspace hides that row (v0.13+), so they stay immediately left of Temporary Chat in both. -->
{#snippet renderCustomActions(compact: boolean)}
	<!-- reset requests: mobile only here; on larger screens the sidebar button (next to Notifications /
	     under Workspace) is always visible, while on mobile the sidebar is a hidden drawer -->
	{#if $mobile && $user?.role === 'admin' && $pendingResetCount > 0}
		<Tooltip content={$i18n.t('Token reset requests')}>
			<button
				id={compact ? undefined : 'reset-requests-button'}
				class="relative flex {compact
					? 'size-7'
					: 'size-8'} shrink-0 items-center justify-center rounded-full border border-(--theme-line-2) bg-(--theme-surface) text-(--theme-ink-2) shadow-(--theme-sh-1) transition hover:border-(--theme-accent-line)"
				aria-label={$i18n.t('{{count}} token reset requests', {
					count: $pendingResetCount
				})}
				on:click={() => (showResetRequests = true)}
			>
				<QueueList className="size-4" strokeWidth="1.8" />
				<span
					class="absolute -top-1.5 -right-1.5 min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-(--theme-accent) text-(--theme-on-accent) text-[0.625rem] font-semibold leading-[1.125rem] text-center"
					aria-hidden="true">{$pendingResetCount > 99 ? '99+' : $pendingResetCount}</span
				>
			</button>
		</Tooltip>
	{/if}

	{#if ($models ?? []).length > 0}
		<Tooltip content={$i18n.t('Choose model')}>
			<button
				id={compact ? undefined : 'choose-model-button'}
				class="flex shrink-0 items-center gap-2 {compact
					? 'h-7 max-lg:w-7'
					: 'h-8 max-md:w-8'} {compact
					? 'max-lg:justify-center lg:pl-0.5 lg:pr-2.5'
					: 'max-md:justify-center md:pl-1 md:pr-3'} rounded-full border border-(--theme-line-2) bg-(--theme-surface) text-[0.8125rem] font-medium text-(--theme-ink) shadow-(--theme-sh-1) transition hover:border-(--theme-accent-line)"
				aria-label={$i18n.t('Choose model')}
				on:click={() => {
					pickerWelcome = true;
					showModelPicker = true;
				}}
			>
				<ModelTile
					model={$models.find((m) => m.id === selectedModelId)}
					lang={$i18n.language}
					className="{compact ? 'size-5.5' : 'size-6'} rounded-full"
				/>
				<span class={compact ? 'max-lg:hidden' : 'max-md:hidden'}>{$i18n.t('Choose model')}</span>
			</button>
		</Tooltip>
	{/if}
{/snippet}

{#snippet renderTabBarActions()}
	{@render renderCustomActions(true)}
	{@render renderTemporaryChatToggle()}
	{#if liveParticipants.length > 0}
		<div class="flex h-6 shrink-0 items-center px-1">
			<ChatParticipants participants={liveParticipants} mode="presence" avatarClass="size-4" />
		</div>
	{/if}
{/snippet}

{#snippet renderChatActions()}
	{#if !tabbed}{@render renderTemporaryChatToggle()}{/if}
	{#if $user?.role === 'user' ? ($user?.permissions?.chat?.temporary ?? true) && !($user?.permissions?.chat?.temporary_enforced ?? false) : true}
		{#if chat?.id && $temporaryChatEnabled}
			<Tooltip content={$i18n.t(`Save Chat`)}>
				<button
					class="flex size-6 cursor-pointer items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-50/40 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-200"
					id="save-temporary-chat-button"
					on:click={async () => {
						onSaveTempChat();
					}}
					aria-label={$i18n.t(`Save Chat`)}
				>
					<ChatCheck className="size-4.5" strokeWidth="1.5" />
				</button>
			</Tooltip>
		{/if}
	{/if}

	{#if $mobile && !$temporaryChatEnabled && chat && chat.id}
		<Tooltip content={$i18n.t('New Chat')}>
			<button
				class="flex size-6 {$showSidebar
					? 'md:hidden'
					: ''} cursor-pointer items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-50/40 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-200"
				on:click={() => {
					initNewChat();
				}}
				aria-label={$i18n.t('New Chat')}
			>
				<ChatPlus className="size-4" strokeWidth="1.5" />
			</button>
		</Tooltip>
	{/if}

	{#if !tabbed && liveParticipants.length > 0}
		<div class="flex h-6 shrink-0 items-center px-1">
			<ChatParticipants participants={liveParticipants} mode="presence" avatarClass="size-4" />
		</div>
	{/if}

	{#if shareEnabled && chat?.id && (Object.keys(history?.messages ?? {}).length > 0 || scrollToTop || ($artifactContents ?? []).length > 0 || (!readOnly && !$temporaryChatEnabled) || $user?.role === 'admin' || ($user?.permissions?.chat?.export ?? true))}
		<Menu
			{chat}
			{shareEnabled}
			{readOnly}
			{scrollToTop}
			shareHandler={() => {
				showShareChatModal = !showShareChatModal;
			}}
			{renameHandler}
			archiveChatHandler={() => {
				archiveChatHandler(chat.id);
			}}
			deleteChatHandler={() => {
				deleteChatHandler(chat.id);
			}}
			{moveChatHandler}
		>
			<button
				class="flex shrink-0 cursor-pointer items-center justify-center {tabbed
					? 'size-4 rounded text-gray-400 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-white/10 dark:hover:text-white'
					: 'size-6 rounded-lg text-gray-500 transition hover:bg-gray-50/40 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-200'}"
				id="chat-context-menu-button"
				aria-label={$i18n.t('Chat actions')}
			>
				<EllipsisHorizontal className={tabbed ? 'size-3' : 'size-4.5'} strokeWidth="1.5" />
			</button>
		</Menu>
	{/if}
{/snippet}

<ShareChatModal bind:show={showShareChatModal} chatId={$chatId} />

<button
	id="new-chat-button"
	class="hidden"
	on:click={() => {
		initNewChat();
	}}
	aria-label={$i18n.t('New Chat')}
/>

<nav
	class="sticky top-0 z-30 w-full {$mobile ? 'pt-1.5' : ''} {tabbed
		? 'pb-0.5'
		: 'pb-1 -mb-12'} flex flex-col items-center drag-region"
>
	<div class:hidden={tabbed} class="flex items-center w-full {$mobile ? 'px-1.5' : 'pl-1.5 pr-1'}">
		<div
			id="navbar-bg-gradient-to-b"
			class="{chat?.id
				? 'visible'
				: 'invisible'} bg-linear-to-b via-40% to-97% from-white/90 via-white/50 to-transparent dark:from-gray-900/90 dark:via-gray-900/50 dark:to-transparent pointer-events-none absolute inset-0 -bottom-10 z-[-1]"
		></div>

		<div class=" flex max-w-full w-full mx-auto bg-transparent">
			<div class="flex items-center w-full max-w-full">
				{#if $mobile && !$showSidebar}
					<div class="mr-1 flex flex-none items-center self-start">
						<Tooltip content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}>
							<button
								id="sidebar-toggle-button"
								class="flex cursor-pointer rounded-lg text-gray-500 transition hover:bg-gray-50/40 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-200"
								on:click={() => {
									showSidebar.set(!$showSidebar);
								}}
								aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
							>
								<div class="self-center p-1.5">
									<Sidebar className="size-4" />
								</div>
							</button>
						</Tooltip>
					</div>
				{/if}

				<div
					class="flex-1 min-w-0 overflow-hidden max-w-full md:mt-0.5 md:py-0.5 pl-1 {$showSidebar
						? 'ml-1'
						: ''}"
				>
					{#if chat?.id}
						<div class="flex max-w-full min-w-0 items-center gap-2 mr-2">
							{#if confirmEdit && !tabbed}
								{@render renderTitleEditor()}
							{:else}
								<h1
									class="min-w-0 truncate md:py-1 text-left text-[0.9375rem] font-normal text-gray-700 dark:text-gray-300"
								>
									{title || chat?.chat?.title || $i18n.t('New Chat')}
								</h1>
							{/if}

							{#if !$temporaryChatEnabled && ($user?.role === 'admin' || ($user?.permissions?.chat?.delete ?? true))}
								<button
									id="delete-chat-button"
									aria-label={$i18n.t('Delete')}
									class="hidden"
									on:click={() => {
										deleteChatHandler(chat.id);
									}}
								>
									<EllipsisHorizontal className="size-4.5" strokeWidth="1.5" />
								</button>
							{/if}
						</div>
					{:else}
						<h1 class="sr-only">{$i18n.t('New Chat')}</h1>
						<div class="pointer-events-none invisible flex max-w-full min-w-0 items-center gap-2">
							<div
								class="min-w-0 truncate md:py-1 text-left text-[0.9375rem] font-normal text-gray-700 dark:text-gray-300"
							>
								{$i18n.t('New Chat')}
							</div>
						</div>
					{/if}
				</div>

				<div class="lg:mr-1 flex flex-none items-center gap-2 self-center">
					<!-- <div class="md:hidden flex self-center w-[0.0625rem] h-5 mx-2 bg-gray-300 dark:bg-stone-700" /> -->

					<!-- CUSTOM: reset requests + "Choose model", immediately left of Temporary Chat -->
					{#if !tabbed}{@render renderCustomActions(false)}{/if}

					<!-- CUSTOM: the snippet below starts with Temporary Chat, so "Choose model" stays immediately left of it -->
					{#if !tabbed}{@render renderChatActions()}{/if}

					{#if history.currentId || $selectedTerminalId || $user?.role === 'admin' || ($user?.role === 'user' && ($user.permissions?.chat?.side_chat ?? false))}
						<Tooltip content={$i18n.t('Tabs')}>
							<button
								class="flex size-6 cursor-pointer items-center justify-center rounded-lg text-gray-500 transition hover:bg-gray-50/40 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-200"
								on:click={() => showTabs.set(!$showTabs)}
								aria-label={$i18n.t('Tabs')}
								aria-expanded={!!$showTabs}
							>
								<SplitPanel className="size-4.5" strokeWidth="1" />
							</button>
						</Tooltip>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- CUSTOM -->
	{#if $user?.role === 'admin'}
		<ResetRequestsModal bind:show={showResetRequests} />
	{/if}
	<ModelPickerModal
		bind:show={showModelPicker}
		{selectedModelId}
		welcome={$settings?.hasSeenModelPicker !== true}
		hasChat={!!history?.currentId}
		onSelect={onChooseModel}
	/>

	{#if !tabbed && $temporaryChatEnabled && isTemporaryChatId($chatId)}
		<div class=" w-full z-30 text-center">
			<div class="text-xs text-gray-500">{$i18n.t('Temporary Chat')}</div>
		</div>
	{/if}

	<div class="absolute top-full left-0 right-0 h-fit">
		{#if !history.currentId && !$chatId && ($banners.length > 0 || ($config?.license_metadata?.type ?? null) === 'trial' || (($config?.license_metadata?.seats ?? null) !== null && $config?.user_count > $config?.license_metadata?.seats))}
			<div class=" w-full z-30">
				<div
					class=" flex flex-col gap-1 w-full max-h-28 overflow-y-auto overscroll-contain md:max-h-none md:overflow-visible"
				>
					{#if ($config?.license_metadata?.type ?? null) === 'trial'}
						<Banner
							className="px-[11px] rounded-lg"
							banner={{
								type: 'info',
								title: $i18n.t('Trial License'),
								content: $i18n.t(
									'You are currently using a trial license. Please contact support to upgrade your license.'
								)
							}}
						/>
					{/if}

					{#if ($config?.license_metadata?.seats ?? null) !== null && $config?.user_count > $config?.license_metadata?.seats}
						<Banner
							className="px-[11px] rounded-lg"
							banner={{
								type: 'error',
								title: $i18n.t('License Error'),
								content: $i18n.t(
									'Exceeded the number of seats in your license. Please contact support to increase the number of seats.'
								)
							}}
						/>
					{/if}

					{#each $banners.filter((b) => ![...getDismissedBannerIds(), ...closedBannerIds].includes(b.id)) as banner (banner.id)}
						<Banner
							className="px-[11px] rounded-lg"
							{banner}
							on:dismiss={(e) => {
								const bannerId = e.detail;

								if (banner.dismissible) {
									localStorage.setItem(
										'dismissedBannerIds',
										JSON.stringify(
											[bannerId, ...getDismissedBannerIds()].filter((id) =>
												$banners.find((b) => b.id === id)
											)
										)
									);
								} else {
									closedBannerIds = [...closedBannerIds, bannerId];
								}
							}}
						/>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</nav>
