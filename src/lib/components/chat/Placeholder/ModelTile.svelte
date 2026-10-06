<script context="module" lang="ts">
	// model id → true when the backend serves only the default brand image (no custom logo)
	const defaultImageCache = new Map<string, Promise<boolean>>();

	const TONES = ['rose', 'blue', 'green', 'amber', 'violet', 'orange'];

	/** Stable tone per model id, so a model keeps its colour across sessions. */
	export const modelTone = (id: string = '') => {
		let h = 0;
		for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
		return TONES[Math.abs(h) % TONES.length];
	};
</script>

<script lang="ts">
	// Reference `.mdl-ic.lg` tile: the model's own logo when it has one, otherwise a
	// tone-tinted tile with a sparkle. The profile-image endpoint redirects to
	// /static/karix-icons/* when a model has no image, which is how "no logo" is detected.
	import { brandLogoCircle, brandVariant } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';

	export let model: { id?: string } | undefined = undefined;
	export let lang = 'en-US';
	export let className = 'size-11 rounded-[13px]';

	$: src = model?.id
		? `${WEBUI_API_BASE_URL}/models/model/profile/image?id=${model.id}&lang=${lang}&theme=${$brandVariant}`
		: null;

	let usesDefault = true;
	$: checkImage(src);

	const checkImage = async (url: string | null) => {
		usesDefault = true;
		if (!url) return;
		if (!defaultImageCache.has(url)) {
			defaultImageCache.set(
				url,
				fetch(url, { credentials: 'include' })
					.then((r) => !r.ok || (r.redirected && r.url.includes('/static/karix-icons/')))
					.catch(() => true)
			);
		}
		const isDefault = await defaultImageCache.get(url);
		if (url === src) usesDefault = isDefault ?? true;
	};

	// no model selected → accent tile
	$: toneColor = model?.id ? `var(--theme-tone-${modelTone(model.id)})` : 'var(--theme-accent)';
</script>

{#if src && !usesDefault}
	<img
		{src}
		class="{className} shrink-0 object-cover bg-(--theme-surface) ring-1 ring-(--theme-line)"
		alt=""
		aria-hidden="true"
		draggable="false"
		on:error={(e) => {
			// LICENSE covers this Open WebUI fallback logo.
			// Do not alter, remove, obscure, or replace it except as LICENSE permits:
			// https://docs.openwebui.com/license.
			(e.currentTarget as HTMLImageElement).src = $brandLogoCircle;
		}}
	/>
{:else}
	<span
		class="{className} shrink-0 inline-grid place-items-center"
		style="--tc: {toneColor}; color: var(--tc); background: color-mix(in srgb, var(--tc) 11%, var(--theme-surface));"
		aria-hidden="true"
	>
		<Sparkles className="size-[50%]" strokeWidth="1.8" />
	</span>
{/if}
