<script lang="ts">
	// CUSTOM: admin-set disclaimer line above the chat input once a chat has messages (Admin Settings ›
	// General › Chat Disclaimer). Renders nothing when the text is empty, so the default layout is unchanged.
	import { config } from '$lib/stores';

	$: text = ($config?.ui?.chat_disclaimer ?? '').trim();
</script>

{#if text}
	<p
		class="mx-auto w-full max-w-3xl px-4 pb-2 text-center text-xs leading-snug text-gray-500 dark:text-gray-400 line-clamp-2 select-none"
		role="note"
	>
		{text}
	</p>
{/if}
