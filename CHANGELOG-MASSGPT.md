# CHANGELOG-MASSGPT

Append an entry for every change set (template: CLAUDE.md section 9).
No change merges without a changelog entry.

## Upstream touchpoints
Every hunk in an upstream Open WebUI file is marked `CUSTOM:` and listed here, so an upstream merge is a checklist.
- src/routes/+layout.svelte — one import of `$lib/styles/theme-tokens.css` after `app.css`
- src/lib/stores/index.ts — `Settings` type: `appTheme`, `hasSeenModelPicker`
- backend/open_webui/models/users.py — `InterfaceAppTheme` model + `appTheme`, `hasSeenModelPicker` on `InterfaceSettings`
- src/routes/(app)/+layout.svelte — import + one reactive line applying the accent
- src/lib/components/chat/Chat.svelte — import, 4 reactive lines, one `{#if themeBackground}` block before the existing background block
- src/lib/components/chat/SettingsModal.svelte — Appearance tab: 2 imports, group entry, tab entry, tab button, panel branch
- src/lib/i18n/locales/en-US/translation.json — new keys only (appearance.*, accent/pattern names)
- src/lib/components/chat/Suggestions.svelte — import + list markup replaced by `<SuggestionCards>` (Fuse filtering untouched); dead waterfall CSS removed
- src/lib/components/chat/Placeholder.svelte — suggestions wrapper `max-w-2xl` → `max-w-3xl w-full` (aligns cards with input box)

## [2026-10-05] Phase 0 - analysis only, no source changes
- Author: Claude (Phase 0 session) / reviewer: <owner>
- Files modified: none
- Files created:
  - docs/PLAN.md - Phase 0 analysis and plan
  - CHANGELOG-MASSGPT.md - this file
- Files deleted: none
- Config added: none
- DB migration: none
- Risk / regression notes: none (no source changes)
- Verified: read-only analysis of repo; reference HTML reviewed

## [2026-10-05] P1 Foundations — theme tokens, theme helpers, icon, store types
- Author: Claude / reviewer: <owner>
- Naming rule (owner): feature-oriented, global names; no product prefix in code (`theme-*`, `--theme-*`, `appTheme`).
- Files modified:
  - src/app.css — import theme tokens (additive, nothing existing changed)
  - src/lib/stores/index.ts — optional `appTheme`, `hasSeenModelPicker` on `Settings` type
- Files created:
  - src/lib/styles/theme-tokens.css — neutrals, 10 accents (light/dark), derived tints, tones, shadows as `--theme-*` vars; `<html data-accent>` selects accent
  - src/lib/utils/themes.ts — accent list, 6 pattern tiles, `normalizeAppTheme`, `themePatternImage`, `applyThemeAccent`
  - src/lib/components/icons/LayoutGrid.svelte — icon for model picker button
- Files deleted: none
- Config added: none
- DB migration: none
- Risk / regression notes: no visible change (variables unused until P2; no `data-accent` set). Backend `InterfaceSettings` (`extra='forbid'`) must get `appTheme`/`hasSeenModelPicker` in P2/P3 before the UI saves them.
- Verified: `vite build` succeeds; PostCSS/Tailwind compiles app.css with tokens inlined; themes.ts type-checks. Not yet run: lint/check, device/PWA checklist (no UI yet).

## [2026-10-05] P2 Themes & backgrounds (F4) — accent, pattern, strength in Settings → Interface
- Author: Claude / reviewer: <owner>
- Files modified: see "Upstream touchpoints" above (backend users.py, +layout.svelte, Chat.svelte, InterfaceSettings.svelte, en-US translation.json)
- Files created: none
- Files deleted: none
- Config added: none (per-user `settings.ui.appTheme = {accent, pattern, strength}`; `null` clears it)
- DB migration: none (`settings` is a JSON column)
- Behaviour: users with no `appTheme` see exactly the previous UI. When set: `<html data-accent>` drives `--theme-*` tokens; chat space gets page tint + optional pattern (light/dark variants via `dark:` classes). Precedence unchanged for images: folder/model image → user image → licence image; theme background shows only when no image applies. Existing background upload/reset control untouched.
- Risk / regression notes: Chat.svelte edits are outside all DO-NOT-TOUCH regions (imports, reactive block near line 190, background markup near 4285). Backend validates accent/pattern/strength (unknown values rejected by `extra='forbid'`).
- Verified: svelte-check error count identical to baseline (7001 before/after; none in new code); backend model accepts valid / rejects bad accent; en-US JSON valid; Tailwind compiles every new class (`bg-(--theme-page)`, `dark:hidden`, `dark:block`, `bg-(--c)`, `dark:bg-(--cd)`). Full `vite build` reached the adapter stage with no errors but exceeded the 10 min tool limit on the final run, so a complete build is still to be confirmed. Not yet run: manual device/PWA/regression checklist in browser.

## [2026-10-05] P2 rework (F4) — global accent + dedicated Appearance tab (owner feedback)
- Author: Claude / reviewer: <owner>
- Why: the first cut only tinted the pattern and was squeezed into Interface; owner wants the token-file behaviour (accent tints buttons, sidebar, page) and the reference Appearance design.
- Files modified:
  - src/lib/styles/theme-tokens.css — global accent layer: `:root[data-accent]` redefines Tailwind `--color-gray-*` (accent-tinted neutrals) and `--color-blue-*` (accent scale), same mechanism as existing `html.karix`; primary inverse buttons, switches, range inputs, selection use the accent. Dark surfaces use `!important` because existing theme code writes gray-800..950 inline.
  - src/lib/utils/themes.ts — `themePatternMask` (preview tiles), `applyThemeAccent` now also syncs `<meta name="theme-color">` to the tinted page colour and restores the original when cleared.
  - src/routes/(app)/+layout.svelte — imports `theme` store; accent re-applied on light/dark change.
  - src/lib/components/chat/SettingsModal.svelte — registers Appearance tab (Basics group, after Interface).
- Reverted: src/lib/components/common/InterfaceSettings.svelte back to upstream (zero diff).
- Files created:
  - src/lib/components/chat/Settings/Appearance.svelte — live preview, accent cards (3/2 cols), pattern preview tiles (4/3 cols), Subtle–Bold strength slider, reset; radio-group semantics with arrow keys.
  - src/lib/components/icons/Swatch.svelte — tab icon.
- Config added: none. DB migration: none.
- Known limits: OLED-dark users who pick an accent get the reference dark neutrals instead of pure black; the karix theme's navy input box keeps its own colour; `theme-color` is not re-synced on OS light/dark auto-switch until the next theme/accent change; browsers without `color-mix` fall back to flat accent greys (all current evergreen browsers support it).
- Verified: svelte-check 7001 errors = baseline, none in new files; Tailwind compiles all new classes and accent rules. Not yet verified in a browser (owner to check).

## [2026-10-05] P2 fix — theme tokens were never loaded
- Author: Claude / reviewer: <owner>
- Cause: the `@import` added to `src/app.css` sat after Tailwind's `@reference` directive; an `@import` after other statements is invalid CSS, so it was dropped and every `--theme-*` variable (and the global accent layer) was missing. Only the chat pattern showed because its colour is baked into the SVG.
- Fix: `src/app.css` reverted to upstream (zero diff); tokens imported from `src/routes/+layout.svelte` alongside `tailwind.css` / `app.css`.
- Verified: dev server serves theme-tokens.css with the `:root[data-accent]` gray/blue overrides; served app.css previously contained 0 token references.

## [2026-10-05] F4 fix + suggestion cards — untinted chat surface, prompts as cards (owner feedback)
- Author: Claude / reviewer: <owner>
- Why: compared with the reference, the accent tint covered the whole chat space. In the reference only the sidebar is tinted (`.nav{background:var(--side)}`); the chat area stays white (`.main{background:var(--bg)}`) with the pattern on top. Owner also asked for suggested prompts as cards ("Suggested questions" in the reference) instead of the list.
- Files modified:
  - src/lib/components/chat/Chat.svelte — theme layer no longer paints `--theme-page`; it is a transparent pattern overlay on the existing `bg-white dark:bg-gray-900` surface, rendered only when a pattern is chosen
  - src/lib/components/chat/Settings/Appearance.svelte — live preview shows a tinted sidebar strip beside an untinted chat surface
  - src/lib/utils/themes.ts — `theme-color` meta follows `--theme-bg` (chat surface) instead of the tinted page colour
  - src/lib/components/chat/Suggestions.svelte, src/lib/components/chat/Placeholder.svelte — see Upstream touchpoints
- Files created:
  - src/lib/components/chat/SuggestionCards.svelte — reference `.rc/.sgc` card: 92px decorative thumbnail (chat bubbles / document with check / bar chart, cycling), title + subtitle with accent dot, hover lift + arrow badge. 3 per row on ≥640px, 72%-wide snap-scroll row on mobile; more than 3 prompts scroll horizontally. Arrow badge always visible on touch (`hover: none`); reduced-motion respected; all colours from `--theme-*` tokens (light/dark).
- Files deleted: none. Config added: none. DB migration: none.
- Risk / regression notes: suggestion click still calls `onSelect({type:'prompt', data})` exactly as before; search-as-you-type filtering unchanged. ChatPlaceholder also uses Suggestions, so its `grid-cols-2` className is now unused (one svelte-check warning). Sidebar accent tint unchanged (global gray-50 override).
- Verified: svelte-check 6998 errors (baseline 7001; 0 in new/changed custom code). Not yet verified in a browser on desktop/tablet/mobile (owner to check).
