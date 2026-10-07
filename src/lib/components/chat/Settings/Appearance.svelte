<script lang="ts">
	// Appearance: accent colour + background pattern for the whole app (visual spec:
	// .claude/ref-html "Appearance" panel). Every change saves and applies immediately.
	import { getContext } from 'svelte';

	import { config, settings, theme } from '$lib/stores';
	import { setThemeMode } from '$lib/utils/themeMode';
	import {
		DEFAULT_APP_THEME,
		THEME_ACCENTS,
		THEME_PATTERN_OPTIONS,
		normalizeAppTheme,
		themePatternImage,
		themePatternMask,
		KARIX_ACCENT,
		type AppTheme,
		type ThemeAccentId,
		type ThemePatternId
	} from '$lib/utils/themes';

	import Check from '$lib/components/icons/Check.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n: any = getContext('i18n');

	export let saveSettings: Function;

	// Theme mode cards (reference `.ap` previews). Preview colours are artwork, not tokens:
	// [bg, sidebar first, sidebar, panel, line]
	type Mode = { id: string; label: string; sub?: string; c: string[]; c2?: string[]; acc?: string };
	const LIGHT = ['#E7E7EE', '#1C1B26', '#FFFFFF', '#FFFFFF', '#E3E2EC'];
	const DARK = ['#1E1D2B', '#EEEDF7', '#2E2D40', '#12111C', '#2E2D40'];
	$: modes = [
		{ id: 'system', label: 'Auto', sub: 'Follows your device', c: LIGHT, c2: DARK },
		{ id: 'light', label: 'Light', c: LIGHT },
		{ id: 'dark', label: 'Dark', c: DARK },
		{
			id: 'oled-dark',
			label: 'OLED Dark',
			c: ['#0D0D0D', '#EEEEEE', '#1A1A1A', '#000000', '#222222']
		},
		// Karix: v2 tokens, fixed accent
		{
			id: 'karix',
			label: 'Karix',
			c: ['#040D2B', '#EEF1FB', '#10215A', '#06133A', '#1D3373'],
			acc: KARIX_ACCENT
		},
		...($config?.features?.enable_easter_eggs
			? [{ id: 'her', label: 'Her', c: ['#F6E7E0', '#983724', '#FFFFFF', '#FFFFFF', '#ECD5CC'] }]
			: [])
	] as Mode[];
	$: currentMode = $theme ?? 'system';

	$: appTheme = $settings?.appTheme ? normalizeAppTheme($settings.appTheme) : null;
	// Slider value shown while dragging; saved on release.
	let strength = DEFAULT_APP_THEME.strength;
	$: strength = appTheme?.strength ?? DEFAULT_APP_THEME.strength;

	$: preview = { ...(appTheme ?? DEFAULT_APP_THEME), strength: Number(strength) };
	$: previewLight = themePatternImage(preview, false);
	$: previewDark = themePatternImage(preview, true);

	const save = (patch: Partial<AppTheme>) =>
		saveSettings({
			appTheme: normalizeAppTheme({ ...(appTheme ?? DEFAULT_APP_THEME), ...patch })
		});

	const selectAccent = (accent: ThemeAccentId) => save({ accent });
	const selectPattern = (pattern: ThemePatternId) => save({ pattern });

	// Arrow-key navigation inside a radio group (WAI-ARIA radio pattern).
	const onRadioKeydown = (e: KeyboardEvent) => {
		const keys = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp'];
		if (!keys.includes(e.key)) return;
		const current = e.currentTarget as HTMLButtonElement;
		const group = current.closest('[role="radiogroup"]');
		const radios = Array.from(group?.querySelectorAll<HTMLButtonElement>('[role="radio"]') ?? []);
		const step = keys.indexOf(e.key) < 2 ? 1 : -1;
		const next = radios[(radios.indexOf(current) + step + radios.length) % radios.length];
		e.preventDefault();
		next?.focus();
		next?.click();
	};

	const sectionLabel = 'text-sm font-medium text-gray-900 dark:text-white';
	const hint = 'text-xs text-gray-500 dark:text-gray-400 -mt-1.5';
</script>

<div id="tab-appearance" class="flex flex-col h-full text-sm">
	<div class="mb-4">
		<h2 class="text-sm font-medium text-gray-900 dark:text-white">
			{$i18n.t('settings.personal.appearance.title')}
		</h2>
		<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
			{$i18n.t('settings.personal.appearance.description')}
		</p>
	</div>

	<div class="flex-1 min-h-0 overflow-y-auto scrollbar-hover pr-1.5 flex flex-col gap-6 pb-4">
		<!-- Live preview -->
		<div
			class="relative h-28 shrink-0 overflow-hidden rounded-2xl border border-gray-100 dark:border-gray-850 bg-(--theme-bg)"
			aria-hidden="true"
		>
			<!-- tinted sidebar beside an untinted chat surface, as in the reference -->
			<div
				class="absolute inset-y-0 left-0 z-10 w-1/5 border-r border-gray-100 bg-gray-50 dark:border-gray-850 dark:bg-gray-950"
			></div>
			{#if previewLight}
				<div class="absolute inset-0 dark:hidden" style="background-image: {previewLight}"></div>
				<div
					class="absolute inset-0 hidden dark:block"
					style="background-image: {previewDark}"
				></div>
			{/if}
			<div class="relative ml-[20%] flex h-full flex-col justify-between p-3.5">
				<div
					class="self-end rounded-2xl rounded-br-md bg-gray-50 px-3 py-1.5 text-xs text-gray-700 dark:bg-gray-850 dark:text-gray-200"
				>
					{$i18n.t('settings.personal.appearance.preview.question')}
				</div>
				<div class="flex items-end justify-between gap-3">
					<div class="flex w-1/2 flex-col gap-1.5">
						<span class="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700"></span>
						<span class="h-2 w-3/4 rounded-full bg-gray-200 dark:bg-gray-700"></span>
					</div>
					<span
						class="rounded-full bg-(--theme-accent) px-3 py-1 text-xs font-medium text-(--theme-on-accent)"
					>
						{$i18n.t('settings.personal.appearance.preview.action')}
					</span>
				</div>
			</div>
		</div>

		<!-- Theme mode (moved here from General) -->
		<section class="flex flex-col gap-3" aria-labelledby="appearance-mode-label">
			<div id="appearance-mode-label" class={sectionLabel}>{$i18n.t('Theme')}</div>
			<div class="ap-grid" role="radiogroup" aria-labelledby="appearance-mode-label">
				{#each modes as mode}
					{@const checked = currentMode === mode.id}
					<button
						type="button"
						role="radio"
						aria-checked={checked}
						tabindex={checked ? 0 : -1}
						class="ap group flex min-w-0 flex-col items-center gap-2 text-[0.8125rem] transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--theme-accent) {checked
							? 'font-medium text-gray-900 dark:text-white'
							: 'text-gray-500 dark:text-gray-400'}"
						on:click={() => setThemeMode(mode.id)}
						on:keydown={onRadioKeydown}
					>
						<span class="ap-prev" class:on={checked}>
							{#each mode.c2 ? [mode.c, mode.c2] : [mode.c] as c}
								<span class="ap-half" style="background: {c[0]}">
									<span class="ap-s">
										<i style="background: {c[1]}"></i><i style="background: {c[2]}"></i><i
											style="background: {c[2]}"
										></i>
									</span>
									<span class="ap-p" style="background: {c[3]}">
										<i style="background: {c[4]}; width: 62%"></i><i style="background: {c[4]}"></i>
										<i class="a" style={mode.acc ? `background: ${mode.acc}` : undefined}></i>
									</span>
								</span>
							{/each}
						</span>
						<span class="truncate max-w-full">{$i18n.t(mode.label)}</span>
						{#if mode.sub}
							<span class="-mt-2 text-[0.6875rem] font-normal text-gray-400"
								>{$i18n.t(mode.sub)}</span
							>
						{/if}
					</button>
				{/each}
			</div>
		</section>

		<!-- Accent colour -->
		<section class="flex flex-col gap-3" aria-labelledby="appearance-accent-label">
			<div id="appearance-accent-label" class={sectionLabel}>
				{$i18n.t('settings.personal.appearance.accent.label')}
			</div>
			<p class={hint}>
				{currentMode === 'karix'
					? $i18n.t('Karix uses its own accent colour. Switch to Light or Dark to pick one.')
					: $i18n.t('settings.personal.appearance.accent.description')}
			</p>
			<div
				class="grid grid-cols-2 gap-2.5 sm:grid-cols-3 {currentMode === 'karix'
					? 'opacity-40 pointer-events-none'
					: ''}"
				role="radiogroup"
				aria-labelledby="appearance-accent-label"
				aria-disabled={currentMode === 'karix'}
			>
				{#each THEME_ACCENTS as [id, label, light, dark], idx}
					{@const checked = appTheme?.accent === id}
					<button
						type="button"
						role="radio"
						aria-checked={checked}
						tabindex={checked || (!appTheme && idx === 0) ? 0 : -1}
						class="flex h-11 min-w-0 items-center gap-2.5 rounded-xl border-[1.5px] px-3 text-left text-sm transition active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--theme-accent) {checked
							? 'border-gray-900 bg-gray-50 font-medium text-gray-900 dark:border-white dark:bg-gray-850 dark:text-white'
							: 'border-gray-200 text-gray-600 hover:border-gray-400 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-500'}"
						on:click={() => selectAccent(id)}
						on:keydown={onRadioKeydown}
					>
						<span
							class="grid size-5 shrink-0 place-items-center rounded-md bg-(--c) text-white dark:bg-(--cd) dark:text-gray-900"
							style="--c: {light}; --cd: {dark}"
						>
							{#if checked}<Check className="size-3" strokeWidth="3" />{/if}
						</span>
						<span class="truncate">{$i18n.t(label)}</span>
						{#if id === DEFAULT_APP_THEME.accent}
							<span
								class="ml-auto shrink-0 font-mono text-[0.625rem] uppercase tracking-wider text-gray-400"
								>{$i18n.t('Default')}</span
							>
						{/if}
					</button>
				{/each}
			</div>
		</section>

		<!-- Background pattern -->
		<section class="flex flex-col gap-3" aria-labelledby="appearance-pattern-label">
			<div id="appearance-pattern-label" class={sectionLabel}>
				{$i18n.t('settings.personal.appearance.pattern.label')}
			</div>
			<p class={hint}>{$i18n.t('settings.personal.appearance.pattern.description')}</p>
			<div
				class="grid grid-cols-3 gap-2.5 sm:grid-cols-4"
				role="radiogroup"
				aria-labelledby="appearance-pattern-label"
			>
				{#each THEME_PATTERN_OPTIONS as [id, label]}
					{@const checked = (appTheme?.pattern ?? 'none') === id}
					{@const mask = themePatternMask(id)}
					<button
						type="button"
						role="radio"
						aria-checked={checked}
						tabindex={checked ? 0 : -1}
						class="group flex flex-col gap-1.5 text-center text-xs transition focus-visible:outline-none {checked
							? 'font-medium text-gray-900 dark:text-white'
							: 'text-gray-500 dark:text-gray-400'}"
						on:click={() => selectPattern(id)}
						on:keydown={onRadioKeydown}
					>
						<span
							class="relative block h-16 overflow-hidden rounded-xl border-[1.5px] bg-white transition group-hover:-translate-y-0.5 group-focus-visible:ring-2 group-focus-visible:ring-(--theme-accent) dark:bg-gray-900 {checked
								? 'border-(--theme-accent) ring-[3px] ring-(--theme-accent-soft)'
								: 'border-gray-200 dark:border-gray-700'}"
						>
							{#if mask}
								<span
									class="absolute inset-0 bg-(--theme-accent) opacity-45"
									style="mask-image: {mask}; -webkit-mask-image: {mask}; mask-repeat: repeat; -webkit-mask-repeat: repeat"
								></span>
							{:else}
								<span class="absolute inset-0 grid place-items-center text-gray-400">
									<XMark className="size-4" />
								</span>
							{/if}
						</span>
						{$i18n.t(label)}
					</button>
				{/each}
			</div>

			{#if appTheme && appTheme.pattern !== 'none'}
				<div class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
					<span aria-hidden="true">{$i18n.t('settings.personal.appearance.strength.subtle')}</span>
					<input
						id="appearance-strength"
						type="range"
						min="0.1"
						max="1"
						step="0.05"
						class="h-1.5 flex-1 cursor-pointer accent-(--theme-accent)"
						aria-label={$i18n.t('settings.personal.appearance.strength.label')}
						bind:value={strength}
						on:change={() => save({ strength: Number(strength) })}
					/>
					<span aria-hidden="true">{$i18n.t('settings.personal.appearance.strength.bold')}</span>
					<output
						for="appearance-strength"
						class="w-10 text-right font-mono text-gray-700 dark:text-gray-300"
						>{Math.round(Number(strength) * 100)}%</output
					>
				</div>
			{/if}
		</section>

		{#if appTheme}
			<div
				class="flex items-center justify-between gap-3 rounded-xl border border-gray-100 px-3.5 py-3 dark:border-gray-850"
			>
				<div class="min-w-0">
					<div class="text-sm text-gray-900 dark:text-white">
						{$i18n.t('settings.personal.appearance.reset.label')}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">
						{$i18n.t('settings.personal.appearance.reset.description')}
					</div>
				</div>
				<button
					type="button"
					class="shrink-0 rounded-full border border-gray-200 px-3 py-1.5 text-xs text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
					on:click={() => saveSettings({ appTheme: null })}
				>
					{$i18n.t('Reset')}
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Theme cards: each card is between --ap-min and --ap-max wide (height follows 16:10). */
	.ap-grid {
		--ap-min: 7.5rem;
		--ap-max: 9.5rem;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(var(--ap-min), var(--ap-max)));
		gap: 0.75rem;
	}
	/* reference `.ap-prev` theme previews */
	.ap-prev {
		display: flex;
		width: 100%;
		aspect-ratio: 16 / 10;
		overflow: hidden;
		border-radius: 14px;
		border: 2px solid transparent;
		box-shadow: inset 0 0 0 1px var(--theme-line-2);
		transition:
			border-color 0.2s,
			transform 0.2s var(--theme-ease);
	}
	.ap:hover .ap-prev {
		transform: translateY(-2px);
	}
	.ap-prev.on {
		border-color: var(--theme-ink);
		box-shadow: none;
	}
	.ap-half {
		flex: 1;
		display: flex;
		gap: 6px;
		min-width: 0;
		padding: 8px;
	}
	.ap-s {
		width: 22%;
		display: flex;
		flex-direction: column;
		gap: 5px;
	}
	.ap-s i {
		display: block;
		height: 14%;
		border-radius: 4px;
	}
	.ap-p {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 8px;
		border-radius: 8px;
		min-width: 0;
	}
	.ap-p i {
		display: block;
		height: 9%;
		border-radius: 3px;
	}
	.ap-p i.a {
		width: 40%;
		margin-top: auto;
		background: var(--theme-accent);
	}
	@media (prefers-reduced-motion: reduce) {
		.ap-prev {
			transition: none;
		}
	}
</style>
