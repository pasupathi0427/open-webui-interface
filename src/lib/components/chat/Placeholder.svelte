<script lang="ts">
	import { brandLogoCircle, brandVariant } from '$lib/stores';
	import type { TerminalContext } from '$lib/types';
	import type { Writable } from 'svelte/store';
	import { toast } from 'svelte-sonner';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
	import { blur, fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	import { updateFolderById } from '$lib/apis/folders';

	import { config, user, selectedFolder } from '$lib/stores';
	import { sanitizeResponseContent, extractCurlyBraceWords } from '$lib/utils';
	import {
		resolveLocalizedModelDescription,
		resolveLocalizedModelName,
		resolveLocalizedModelPromptSuggestions,
		resolveLocalizedPromptSuggestions
	} from '$lib/utils/localizedContent';
	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';

	import Suggestions from './Suggestions.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
	import MessageInput from './MessageInput.svelte';
	import FolderPlaceholder from './Placeholder/FolderPlaceholder.svelte';
	import LandingHero from './Placeholder/LandingHero.svelte'; // CUSTOM
	import ChatGlance from './Placeholder/ChatGlance.svelte'; // CUSTOM
	import { getChatContext } from '$lib/components/chat/context';

	const { models: _models, temporary } = getChatContext();

	const i18n: any = getContext('i18n');

	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;
	export let callActive = false;
	export let callEnabled = true;

	export let atSelectedModel: Model | undefined;
	export let selectedModels: [''];
	export let onModelSelect: (models: string[]) => void = () => {};
	export let chatFiles: any[] = [];
	export let params: Record<string, any> = {};
	export let onParamChange: (key: string, value: unknown) => void = () => {};

	export let history;
	export let chatId = '';
	export let folderTabActions: import('svelte').Snippet | undefined = undefined;

	export let prompt = '';
	export let files = [];
	export let terminalContext: TerminalContext | null = null;
	export let selectedTerminalId: Pick<Writable<string | null>, 'subscribe' | 'set'>;
	export let terminalSkills: Writable<any[]>;
	export let messageInput = null;

	export let selectedToolIds = [];
	export let selectedSkillIds = [];
	export let selectedFilterIds = [];
	export let pendingOAuthTools = [];

	export let showCommands = false;

	export let imageGenerationEnabled = false;
	export let selectedImageModelId = '';
	export let videoGenerationEnabled = false;
	export let selectedVideoModelId = '';
	export let codeInterpreterEnabled = false;
	export let webSearchEnabled = false;
	export let toolApprovalMode = 'full';
	export let onToolApprovalModeChange: Function = () => {};
	export let oauthRedirectHandler: Function = () => {};

	export let onUpload: Function = (e) => {};
	export let onUpdate: (data?: { file?: any }) => void = () => {};
	export let onSelect = (e) => {};
	export let onTemporaryChange: ((value: boolean) => void) | null = null;
	export let onChange = (e) => {};
	export let onWebSearchToggle: Function = () => {};
	export let messageQueue: { id: string; prompt: string; files: any[] }[] = [];
	export let onQueueSendNow: (id: string) => void = () => {};
	export let onQueueEdit: (id: string) => void = () => {};
	export let onQueueDelete: (id: string) => void = () => {};
	export let askUser = {
		show: false,
		questions: [],
		allowOther: true,
		timeoutMs: null,
		onConfirm: (_value: any) => {},
		onCancel: () => {}
	};

	export let dragged = false;

	// Height of the floating folder composer, so lists can scroll clear of it.
	let composerHeight = 0;
	// The composer only belongs with the folder's chats, not its automations.
	let folderSection: 'chats' | 'automations' | 'knowledge' = 'chats';

	let models = [];
	export let selectedModelIdx = 0;
	let selectedModel;
	let selectedModelName = '';
	let selectedModelDescription = '';
	let selectedSuggestionPrompts = [];

	$: models = selectedModels.map((id) => $_models.find((m) => m.id === id));
	$: selectedModel = atSelectedModel ?? models[selectedModelIdx];
	$: selectedModelName = resolveLocalizedModelName(selectedModel, $i18n.language);
	$: selectedModelDescription =
		$config?.license_metadata?.chat_placeholder_description ||
		resolveLocalizedModelDescription(selectedModel, $i18n.language);
	$: selectedSuggestionPrompts =
		resolveLocalizedModelPromptSuggestions(atSelectedModel, $i18n.language) ??
		resolveLocalizedModelPromptSuggestions(models[selectedModelIdx], $i18n.language) ??
		resolveLocalizedPromptSuggestions(
			$config?.default_prompt_suggestions,
			$config?.default_prompt_suggestions_i18n ?? {},
			$i18n.language,
			(key) => $i18n.t(key)
		);

	// True when viewing a shared folder the current user doesn't own AND lacks write access
	$: folderReadOnly =
		$selectedFolder != null &&
		$user?.role !== 'admin' &&
		$selectedFolder.user_id !== $user?.id &&
		!$selectedFolder.write_access;
</script>

{#snippet composer(placeholder = '')}
	<MessageInput
		{selectedTerminalId}
		{terminalSkills}
		{chatId}
		{onTemporaryChange}
		bind:terminalContext
		{callActive}
		{callEnabled}
		bind:this={messageInput}
		{history}
		bind:selectedModels
		{onModelSelect}
		bind:chatFiles
		bind:params
		{onParamChange}
		bind:files
		bind:prompt
		bind:autoScroll
		bind:selectedToolIds
		bind:selectedSkillIds
		bind:selectedFilterIds
		bind:imageGenerationEnabled
		bind:selectedImageModelId
		bind:videoGenerationEnabled
		bind:selectedVideoModelId
		bind:codeInterpreterEnabled
		bind:webSearchEnabled
		bind:atSelectedModel
		bind:showCommands
		bind:dragged
		{pendingOAuthTools}
		{oauthRedirectHandler}
		{toolApprovalMode}
		{onToolApprovalModeChange}
		{stopResponse}
		{createMessagePair}
		{placeholder}
		{onChange}
		{onUpload}
		{onUpdate}
		{messageQueue}
		{onQueueSendNow}
		{onQueueEdit}
		{onQueueDelete}
		{askUser}
		{onWebSearchToggle}
		on:chatVariables
		on:submit={(e) => {
			dispatch('submit', e.detail);
		}}
	/>
{/snippet}

<!-- CUSTOM (phones): home view is one full-height column, chat input docked at the bottom (reference mobile) -->
<div
	class="w-full {$selectedFolder
		? 'flex h-full min-h-0 flex-col overflow-hidden'
		: 'm-auto max-w-[58rem] px-1 md:@3xl:px-20 translate-y-6 py-24 max-md:m-0 max-md:self-stretch max-md:min-h-full max-md:flex max-md:flex-col max-md:translate-y-0 max-md:pt-14 max-md:pb-0'} text-center"
>
	<!-- In a folder, temporary mode shows on the composer alone. -->
	{#if $temporary && !$selectedFolder}
		<Tooltip
			content={$i18n.t("This chat won't appear in history and your messages will not be saved.")}
			className="w-full flex justify-center mb-0.5"
			placement="top"
		>
			<div class="flex items-center gap-1.5 text-gray-500 text-xs my-1 w-fit">
				<EyeSlash strokeWidth="2" className="size-3.5" />{$i18n.t('Temporary Chat')}
			</div>
		</Tooltip>
	{/if}

	{#if $selectedFolder}
		<div
			class="relative min-h-0 w-full flex-1"
			style="--folder-composer-space: {folderReadOnly || folderSection !== 'chats'
				? 0
				: composerHeight}px"
		>
			<FolderPlaceholder
				folder={$selectedFolder}
				readOnly={folderReadOnly}
				bind:folderTabActions
				bind:folderSection
				onNewChat={() => messageInput?.focus()}
			/>

			{#if !folderReadOnly}
				<!-- Same mount as the in-chat composer, floating over the list and board. -->
				<div
					class="pointer-events-none absolute inset-x-0 bottom-0 bg-linear-to-t from-white from-40% to-transparent pt-8 pb-2 text-left dark:from-gray-900 {dragged
						? 'z-0'
						: 'z-10'}"
					class:hidden={folderSection !== 'chats'}
					bind:clientHeight={composerHeight}
				>
					<div class="pointer-events-auto">
						{@render composer()}
					</div>
				</div>
			{/if}
		</div>
	{:else}
		<div
			class="w-full shrink-0 text-3xl text-gray-800 dark:text-gray-100 text-center flex items-center gap-4 max-md:contents"
		>
			<div class="w-full flex flex-col justify-center items-center max-md:contents">
				<!-- CUSTOM: "Chat space at a glance" (admin toggle) -->
				{#if $config?.features?.enable_chat_glance}
					<div class="w-full @md:max-w-3xl mb-6 md:-translate-y-20"><ChatGlance /></div>
				{/if}
				<!-- CUSTOM: landing greeting (reference .lp-eyebrow) -->
				<LandingHero />
			</div>
		</div>

		<div
			class="relative text-base font-normal mx-auto @md:max-w-3xl py-3 w-full {atSelectedModel
				? 'mt-2'
				: ''} max-md:order-last max-md:mt-auto max-md:sticky max-md:bottom-0 max-md:z-10 max-md:pb-[max(0.75rem,env(safe-area-inset-bottom))]"
		>
			<!-- Soft halo, like the denser fade around the in-chat composer, so it doesn't float on a vivid background. -->
			<div
				aria-hidden="true"
				class="pointer-events-none absolute -inset-x-8 -inset-y-3 rounded-[3rem] bg-white/40 blur-2xl dark:bg-gray-900/40"
			></div>
			<div class="relative">
				{@render composer($i18n.t('How can I help you today?'))}
			</div>
		</div>

		<!-- CUSTOM: max-w-3xl so the suggestion cards line up with the input box (was max-w-2xl); --sc-bleed = mx-5 so the mobile card row reaches the screen edge -->
		<div class="mx-auto max-w-3xl w-full mt-2 max-md:mt-8" in:fade={{ duration: 200, delay: 200 }}>
			<div class="mx-5" style="--sc-bleed: 1.25rem">
				<Suggestions suggestionPrompts={selectedSuggestionPrompts} inputValue={prompt} {onSelect} />
			</div>
		</div>
	{/if}
</div>
