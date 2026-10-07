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
- src/lib/components/layout/Sidebar.svelte — 2 imports; `brandLogoCircle` import commented out; collapsed-rail `<img>` → `<BrandMark>`; expanded header logo `<img>` + `{$WEBUI_NAME}` text → one `<BrandWordmark>` link (LICENSE comments kept)
- src/app.html — `<title>` "Open WebUI" → "Karix"; apple-touch-icon SVG → PNG; 3 iOS/Android web-app meta tags
- src/lib/constants.ts — `APP_NAME` 'Open WebUI' → 'Karix' (initial `WEBUI_NAME` store value)
- backend/open_webui/main.py — `/manifest.json`: `background_color` #343541 → #ffffff, `theme_color` added, SVG maskable icon replaced by PNG 192/512 + padded maskable 512
- src/lib/components/chat/Placeholder.svelte — landing heading (model image stack + name + description + author) replaced by `<LandingHero>`; old imports left in place to keep the diff small
- src/lib/components/chat/Navbar.svelte — 3 imports + `models` store; `selectedModelId`/`onChooseModel` props; first-login trigger; "Choose model" button before Temporary Chat; `<ModelPickerModal>` mount
- src/lib/components/chat/Chat.svelte — passes `selectedModelId` / `onChooseModel` (sets `selectedModels = [id]`) to Navbar
- src/lib/components/layout/Sidebar/UserMenu.svelte — Swatch import, `profile-menu` class, header name + role, "Customize" item, scoped `<style>` skin
- backend/open_webui/routers/users.py — `appTheme`, `hasSeenModelPicker` exempt from the Interface-permission strip
- backend/open_webui/main.py — usage router import + `include_router('/api/v1/usage')`; token-limit pre-check at the top of `chat_completion` (429 `USAGE_LIMIT_REACHED`)
- backend/open_webui/utils/middleware.py — `Usage` import; new `record_usage_from_ctx()`; one call at the start of `outlet_filter_handler`
- src/lib/components/chat/MessageInput.svelte — import + `<UsageLimitBanner />` as first child of the input form
- src/lib/components/chat/Chat.svelte — `handleOpenAIError`: strip `USAGE_LIMIT_REACHED:` prefix, refresh usage status
- src/lib/components/admin/Users/Groups/EditGroupModal.svelte — `UsageTab` import, `usageGroupId`, "Usage" tab button + panel
- src/lib/components/admin/Users/Groups/EditGroupModal.svelte (also) — tab bar `[&>button]:shrink-0 [&>button]:whitespace-nowrap` (mobile fix)
- src/lib/components/admin/Users/Groups/GroupItem.svelte — `'usage'` added to the edit modal's tabs
- src/lib/components/chat/Settings/General.svelte — theme row, `applyTheme`/`themeChangeHandler`, `themes`/`selectedTheme` removed (moved to `utils/themeMode.ts` + Appearance); `theme` import dropped
- backend/open_webui/config.py — `ENABLE_CHAT_GLANCE` env + `DEFAULT_CONFIG['ui.enable_chat_glance']`
- backend/open_webui/routers/auths.py — `ADMIN_CONFIG_KEYS['ENABLE_CHAT_GLANCE']`, `AdminConfig.ENABLE_CHAT_GLANCE: bool = False`
- backend/open_webui/main.py (also) — `ui.enable_chat_glance` in `/api/config` get_many + `features.enable_chat_glance`
- src/lib/components/admin/Settings/General.svelte — "Chat space at a glance" switch after User Status
- src/lib/stores/index.ts (also) — `Config.features.enable_chat_glance`
- src/lib/components/chat/Placeholder.svelte (also) — `ChatGlance` import + gated mount above the landing heading
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

## [2026-10-05] Branding — reference logos in the sidebar (owner request)
- Author: Claude / reviewer: <owner>
- Why: sidebar logo came from config (`brandLogoCircle` image + `WEBUI_NAME` text); owner wants the reference SVG logos, switching with the theme.
- Files modified:
  - src/lib/components/layout/Sidebar.svelte — see Upstream touchpoints. Header link keeps `href="/"` + `newChatHandler`, gains `aria-label={$WEBUI_NAME}` so screen readers still announce the name.
- Files created:
  - src/lib/components/icons/BrandWordmark.svelte — reference `KX_LOGO` (navy wordmark + gradient dot / white wordmark for dark), path data verified identical to the reference
  - src/lib/components/icons/BrandMark.svelte — reference `KX_MARK` (navy square K / white square K for dark) for the collapsed rail
- Behaviour: variants switch on the existing `.dark` class, so light, dark, OLED-dark, karix (`dark karix`) and system all pick the right logo with no extra state. Each instance gets unique gradient ids, so the hidden variant cannot break the visible one's gradient. Logo colours are the fixed brand identity and live in the icon components (not theme tokens; they do not follow the accent, as in the reference).
- Not changed: favicon / PWA icons / splash (`static/static/karix-icons`, manifest), model avatars, `AppSidebar` (desktop app), and other uses of `brandLogoCircle` (model fallback images).
- Config added: none. DB migration: none.
- Verified: svelte-check 6998 errors / 199 warnings (unchanged; none in new files). Not yet verified in a browser.

## [2026-10-05] Title, PWA icons, mobile suggestion cards (owner feedback)
- Author: Claude / reviewer: <owner>
- Why: (1) the tab showed "Open WebUI" while the app loaded: hard-coded `<title>` in app.html and the `APP_NAME` initial store value; the backend name already defaults to Karix (env.py `WEBUI_NAME`). (2) Suggestion cards were clipped by the page padding on phones and switched layout on viewport width rather than the space available. (3) PWA review: iOS ignores SVG `apple-touch-icon`, the only PNG icons in `static/static` were the Open WebUI "OI" mark, and the install splash background was dark grey (#343541) behind a navy logo.
- Files modified: see Upstream touchpoints (app.html, constants.ts, main.py, Placeholder.svelte) and:
  - src/lib/components/chat/SuggestionCards.svelte — container query (`@container (min-width: 560px)`) instead of a viewport media query: narrow = 72% snap-scroll row (reference mobile), wide = 3 columns (reference tablet/desktop). Narrow row bleeds to the screen edge via `--sc-bleed` (Placeholder sets it to its 1.25rem padding); `overscroll-behavior-x: contain`.
- Files created:
  - static/static/karix-icons/apple-touch-icon.png (180), icon-192.png, icon-512.png, icon-512-maskable.png (wordmark at 72% inside the maskable safe zone). Rendered from the existing `karix-icons/light-rounded.svg` with headless Chromium; opaque RGB (iOS renders transparency black).
- Not changed: the upstream "OI" PNGs in `static/static` (unreferenced by the app shell); `backend/open_webui/static/*` is regenerated from `static/static` at startup (config.py), so its working-tree deletions are build output. The app has no service worker (upstream only unregisters old ones), so no cache/versioning impact.
- PWA checklist (static review): manifest has name/short_name Karix, `display: standalone`, `start_url`, SVG + PNG 192/512 + maskable icons, white background/theme colour; iOS gets PNG touch icon, `apple-mobile-web-app-title`, `apple-mobile-web-app-capable`; `theme-color` meta still synced by `applyThemeAccent`.
- Verified: `main.py` parses; svelte-check 6998 errors / 199 warnings (unchanged). Card layout rendered at 390 / 820 / 1280 px in headless Chromium from the component's real CSS + theme tokens: phone = 72% card with peek reaching the screen edge, iPad and desktop = 3 aligned columns. Not yet verified: real device install (Android / iOS), in-app browser check.

## [2026-10-05] Landing heading — reference model tile + title (owner request)
- Author: Claude / reviewer: <owner>
- Why: landing showed a centred brand-circle image + "Hello, admin"; the reference (`.lp-hero`) is a left-aligned heading: greeting eyebrow with green dot, 44px tone-tinted model tile, "karix <Model name>" title (32px, 25px on phones), model description below.
- Files modified: src/lib/components/chat/Placeholder.svelte (see Upstream touchpoints); src/lib/i18n/locales/en-US/translation.json — `Good morning/afternoon/evening, {{name}}` (custom-key group at top).
- Files created:
  - src/lib/components/chat/Placeholder/LandingHero.svelte — heading aligned with the input box (`@md:max-w-3xl`). Keeps every behaviour of the old block: multi-model stack with click-to-select (`bind:selectedModelIdx`), tag tooltip, sanitised markdown description + tooltip, "By <author>" line. Greeting uses the user's first name and local time; hidden when no model is selected (title already says "Hello, <name>"). Brand word in the title is `$WEBUI_NAME` lower-cased, in the accent colour.
  - src/lib/components/chat/Placeholder/ModelTile.svelte — model's own logo when it has one; otherwise a tinted tile with a sparkle in a stable per-model tone (`--theme-tone-*`, hashed from the model id), or the accent when no model is selected. "No logo" = the profile-image endpoint redirects to `/static/karix-icons/*` (one cached `fetch` per model/theme). Error fallback to `brandLogoCircle` kept (LICENSE comment preserved).
- Not included: the reference "Switch model" chip next to the title — it opens the Choose Model card (F3), which is not built yet.
- Config added: none. DB migration: none.
- Verified: svelte-check 6988 errors / 198 warnings (down from 6998 / 199; 0 in new files). Not yet verified in a browser.

## [2026-10-06] F3 Choose Model card + navbar button; profile menu skin; theme persistence fix (owner request)
- Author: Claude / reviewer: <owner>
- F3: `ModelPickerModal.svelte` (reference v3.1 compact `.mp`): title, subtitle (welcome copy on first login), pill search, card grid 3 cols / 2 cols (container ≤640px) / phone = bottom sheet with horizontal cards; each card = illustrated scene + tone badge (model logo when it has one) + name + "Default" pill + full description + first tag; radio semantics (arrows move, Space selects, Enter/double-click confirms); footer "Make X my default" (same save as the chat-input selector: `settings.models`) / "X is your default", Cancel, "Start with X" (landing) / "Use X" (chat). Models = `$models` minus hidden, Fuse search with the selector's keys/threshold. Chosen model → `selectedModels = [id]` in Chat.svelte; chat-input selector untouched.
- Navbar: "Choose model" pill (current model tile + label; icon only below md) immediately left of Temporary Chat.
- First login: opens once on the landing page when the user has >1 visible model and `settings.ui.hasSeenModelPicker` is not true; closing (or any manual open) sets the flag via `updateUserSettings` (backend, per user, survives devices).
- Scene art: `src/lib/utils/modelScenes.ts` — the 6 reference scenes + helpers ported verbatim (`@ts-nocheck`, static markup); scene chosen from `modelTone(model.id)` so each model keeps the same picture.
- Landing title: removed the "karix" prefix (owner) — model name only.
- Profile menu (owner: menu did not follow the theme): reference `.pop.pf` skin over the existing markup — token surface/border/radius/shadow, icon tiles, name + role header, new "Customize" item → Settings › Appearance. All items/permissions/pin behaviour unchanged. Row height kept at the original 27px; knobs `--pm-row-h`, `--pm-row-py`, `--pm-tile` in UserMenu.svelte `<style>`. Theme switcher row from the reference not added (General tab owns the light/dark/OLED/Karix logic).
- Backend fix: non-admin users without the "Interface settings" permission had every Interface key stripped on save, so their `appTheme` and `hasSeenModelPicker` never persisted. Those two keys are now exempt (personal appearance / onboarding, not admin-governed).
- i18n (en-US): Choose a model, Choose model, Customize, Make {{name}} my default, No model matches "{{query}}", Pick the right model for your task, Search models, Start with {{name}}, Theme, accent colour, pattern, Try a different name or tag., Use {{name}}, Welcome… , {{name}} is your default.
- Config added: none. DB migration: none.
- Verified: svelte-check 6991 errors (0 in new files; +3 vs 6988 are new `$i18n` lines in UserMenu, matching that file's existing untyped-i18n pattern); users.py parses; all 6 scenes generate valid SVG (node smoke test). Not yet verified in a browser.

## [2026-10-06] F1/F2 Token usage governance — department limits, reset requests, usage card, limit banner
- Author: Claude / reviewer: <owner>
- Model: department = Open WebUI group. Each user's allowance = department monthly limit (default 10,000,000, env `USAGE_DEFAULT_TOKEN_LIMIT`) or their per-user override, plus approved top-up/reset grants in the current period. Multi-group user → the group giving the highest limit; no group → "Default" department (10M, period anchored at account creation).
- Period: 30 days from the department's anchor, rolled forward lazily on read (no cron). Saving a different token limit restarts the department period today; grants made in a period expire with it ("Expires at" shown in the group Usage tab).
- Counting: new `usage_ledger` (one row per completion, provider `total_tokens`, else chars/4 estimate of prompt + reply), recorded at the single choke point every UI completion passes (`outlet_filter_handler`). Deleting chats does not refund usage; temporary chats are counted.
- Enforcement: server-side pre-check in `chat_completion` → HTTP 429 for non-admins whose usage ≥ allowance. Admins are tracked (card shows usage) but never blocked.
- Reset requests: user clicks "Request reset" in the limit banner → `usage_request` (pending). Rejected immediately when one is already pending or the department's resets per period (default 2, env `USAGE_DEFAULT_RESETS`) are used (pending + approved count; denied do not).
- Admin decisions (dropdown per row): Top-up (+N this period) · Reset (grant = used − earlier grants → full base allowance this period) · Raise limit (permanent per-user override = N) · Deny (block stays). Top-up/Raise need a token amount → "Update" icon; Reset/Deny → "Confirm" icon (tooltips).
- UI:
  - Admin Panel › Groups › edit group › **Usage** tab (`UsageTab.svelte`): monthly limit per user, reset requests per period, period started / expires at, Save (own save, independent of the group Save), this department's pending requests, members' used / allowance bars.
  - Navbar (admin only, chat page): queue badge with pending count, immediately left of "Choose model"; hidden at 0; opens `ResetRequestsModal` (all departments). Count polled every 60 s.
  - Profile menu: `UsageCard` — Monthly usage limit, used / allowance, "Resets in Xd Yh", "% remaining", bar (accent → amber ≤20% → red when blocked).
  - Chat input: `UsageLimitBanner` (Claude-style bar) when blocked — states: request reset (button) / pending / declined / no resets left; re-checks every 60 s and on window focus while blocked.
- Files created: backend/open_webui/models/usage.py, backend/open_webui/routers/usage.py, backend/open_webui/migrations/versions/a7f3c2e1b9d4_add_usage_tables.py, src/lib/apis/usage/index.ts, src/lib/stores/usage.ts, src/lib/components/chat/Usage/{UsageLimitBanner,ResetRequestsTable,ResetRequestsModal,UsageCard}.svelte, src/lib/components/admin/Users/Groups/UsageTab.svelte
- API (`/api/v1/usage`): GET /me (user), POST /requests (user), GET /requests/count, GET /requests[?group_id], POST /requests/{id}/decide, GET|POST /groups/{id} (admin).
- DB migration: a7f3c2e1b9d4 (revises d4c1a8e37b62) — tables usage_config, usage_ledger (+ index user_id, created_at), usage_request (+ index user_id). Downgrade drops all three. Usage config lives in its own table, not `group.data`, because the group edit Save rewrites `data` wholesale.
- i18n (en-US): 33 keys (usage card, banner, requests table, group tab).
- Known gaps: direct API-key calls that bypass the UI response handler (streaming API, or non-streaming with `ENABLE_API_OUTLET_FILTERS` off) are pre-checked but not yet counted; no 80% warning; no admin note on Deny; queue badge updates by 60 s poll, not push.
- Verified: end-to-end check on a temp SQLite DB through the real migration chain (period roll-over maths; default 10M; block at 100%; pending/duplicate rejection; top-up, reset, raise, deny; resets-per-period exhaustion; decided-twice guard; limit change restarts the period and drops old grants; same limit keeps the period; no-group default; members usage) — all passed. Backend files compile. svelte-check 6992 (0 in new usage files; +1 = new `$i18n` tab label in EditGroupModal, that file's existing untyped-i18n pattern). Not yet verified in a browser.

## [2026-10-06] Usage fixes — grant period, capped display, layout; group dialog mobile tabs (owner feedback)
- Author: Claude / reviewer: <owner>
- Bug (backend/open_webui/models/usage.py): a grant was stamped with the period the request was *made* in. If the admin changed the limit (which restarts the period) before deciding, the approved top-up/reset landed in the old period and never counted (owner saw 24.2K / 14.5K after "Request updated"). `decide()` now stamps the request with the department's current period at approval time.
- Display: used tokens are shown capped at the allowance (14.5K / 14.5K) in the profile-menu card and the group members list. The last reply may run past the allowance and is still answered; the raw total stays in the ledger so a Reset still restores a full allowance.
- Layout: requests table scroller is `w-0 min-w-full overflow-x-auto`, so its 46rem minimum no longer widens the Usage tab (inputs/Save were pushed outside the dialog when a request was queued). Usage card: title on its own line (no wrap), token count moved under the bar.
- Existing issue (mobile): Edit User Group tab buttons shrank until labels broke per letter; tab bar now keeps labels whole and scrolls sideways.
- Verified: backend check suite re-run incl. new regression (request → limit change → approve → grant counts) — all passed. svelte-check 6992 (unchanged; 0 in usage files). Not yet verified in a browser.

## [2026-10-06] Usage fix — count a reply only up to the allowance left (owner report)
- Author: Claude / reviewer: <owner>
- Symptom: user at 24.4K / 24.5K (100 left) sent a message whose reply used ~6K tokens; card showed the capped 24.5K / 24.5K, but after a Reset it showed 30.2K / 30.4K.
- Cause: the ledger stored the full reply (true total ~30.2K) while the UI showed it capped at the allowance; Reset grants "used beyond earlier grants", so it was computed from the hidden 30.2K. Arithmetic was consistent with the rule, but display and rule used different numbers.
- Fix (backend/open_webui/utils/middleware.py `record_usage_from_ctx`): the reply that crosses the limit is still answered, but recorded only up to the allowance remaining, so used ≤ allowance always and a Reset shows X / X + limit. Real per-message usage stays in `chat_message` (Analytics). Frontend `Math.min` display caps kept for ledger rows written before this fix.
- Note: users already over (e.g. the tester at 30.2K) keep their current figures until the next reset or period.
- Verified: backend suite + owner scenario via the real `record_usage_from_ctx` (limit 100: 6000-token reply → 100 / 100 blocked; further reply adds 0; Reset → 100 / 200; another big reply + Reset → 200 / 300) — all passed.

## [2026-10-06] Usage — estimate disclaimer (owner request)
- Author: Claude / reviewer: <owner>
- Files modified: src/lib/components/chat/Usage/UsageCard.svelte (under the token count), src/lib/components/admin/Users/Groups/UsageTab.svelte (under "Members this period"), en-US translation.json (1 key).
- Text: "Token counts are estimates and may not reflect actual API usage".
- Follow-up: removed from the profile-menu card; in the group Usage tab moved to the bottom-right under the members list (small muted text, Analytics style).

## [2026-10-06] F5 Chat space at a glance + theme picker moved to Appearance (owner request)
- Author: Claude / reviewer: <owner>
- F5: `src/lib/components/chat/Placeholder/ChatGlance.svelte` — reference `.qc` strip above the landing heading, horizontal snap row of `.qcc` cards (236px, 210px on phones), hover lift, tone icon tiles:
  - Token allowance (accent): % left + ring, "used / allowance · resets in X" (`/usage/me`).
  - Messages this week (blue): count + 7-day sparkline, "+N vs last week".
  - Active streak (green): current streak + 7-day activity bars, "N of 7 days active · best M".
  - Top model (violet): most-used model name, "N models used".
  Data only from existing endpoints (`GET /users/usage?days=14`, `/usage/me`); no new backend data code.
- Config added: `ENABLE_CHAT_GLANCE` (default **False**) → `ui.enable_chat_glance`; Admin Settings › General › "Chat space at a glance"; exposed as `features.enable_chat_glance`. No migration (falls back to DEFAULT_CONFIG).
- Theme: light/dark mode picker moved from Settings › General to Settings › Appearance as reference `.ap` preview cards (Auto/System split preview, Light, Dark, OLED Dark, Karix, + Her when easter eggs are on); radio semantics + arrow keys. `src/lib/utils/themeMode.ts` holds General's `applyTheme` verbatim + `setThemeMode` (store + localStorage + apply) — behaviour unchanged, incl. theme-color meta and OLED overrides.
- i18n: settings.admin.general.chatGlance.{label,description}, glance strings, Follows your device, Karix, Her.
- Verified: svelte-check 6992 (unchanged; 0 new); backend: flag defaults False, read via admin config, saved via `Config.upsert` — passed. Not yet verified in a browser.

## [2026-10-06] Settings window + theme card size (owner feedback)
- Author: Claude / reviewer: <owner>
- src/lib/components/chat/SettingsModal.svelte — `!max-w-[80rem] h-[min(max(54rem,80dvh),...)]` → `!max-w-[920px] h-[min(680px,calc(100dvh-4rem))]` (reference `.modal.set` 920×680).
- src/lib/components/chat/Settings/Appearance.svelte — theme cards use `.ap-grid` (auto-fill, each card 7.5rem–9.5rem wide via `--ap-min` / `--ap-max`; 16:10 height).

## [2026-10-06] Landing — greeting only (owner request)
- Author: Claude / reviewer: <owner>
- src/lib/components/chat/Placeholder/LandingHero.svelte — now only "Good morning/afternoon/evening, <first name>" (green dot eyebrow, as an h1). Removed model tile, model name, description tooltip, "By" author line, multi-model tile switcher.
- src/lib/components/chat/Placeholder.svelte — `<LandingHero />` (props dropped).
- Note: with several models selected, the landing no longer has the tile to pick whose prompt suggestions show; suggestions follow the first model (selectedModelIdx 0), as in the chat-input selector.
- Follow-up (owner: warmer, more visible): greeting is now a 28px (34px ≥sm) semibold heading, first name capitalised and tinted with the accent, plus a welcome line "It's good to see you. What shall we work on today?". Name split via a placeholder so translations keep their own word order.

## [2026-10-06] Mobile landing — two-up glance, suggestions as list, input at the bottom (owner request)
- Author: Claude / reviewer: <owner>
- src/lib/components/chat/Placeholder/ChatGlance.svelte — `.glance` is a size container; ≤559px wide: exactly two cards in view (`calc((100% - 10px)/2)`), rest swipe in; smaller padding/icon/value, mini charts hidden to fit.
- src/lib/components/chat/SuggestionCards.svelte — ≤559px container: plain text list (title, subtitle, chevron, dividers; no illustration, no dot), no horizontal scroll. Wide layout (3 cards) unchanged. New ChevronRight import + `.sc-chev`.
- src/lib/components/chat/Placeholder.svelte — phones only (`max-md:`): root becomes a full-height flex column (`min-h-full`, no translate, pt-6), the two inner wrappers become `display: contents`, and the input wrapper is `order-last mt-auto sticky bottom-0 z-10` with safe-area bottom padding → order: glance, greeting, suggestions, input docked at the bottom. ≥768px markup/behaviour unchanged.
- Verified: svelte-check 6992 (unchanged); 390×780 headless render of the same flex/contents/order/sticky structure → input bottom = 780 (screen bottom), suggestions above it. Not yet verified on a device.
- Follow-up: phones — top padding pt-6 → pt-14 so the glance strip clears the floating navbar; suggestion list shows the first 3 prompts only (`.sc:nth-child(n + 4) { display: none }`).
- Follow-up: glance wrapper `-translate-y-20` (owner tweak) → `md:-translate-y-20` so the lift applies only ≥768px; on phones it pushed the strip under the floating navbar and left an empty gap above the greeting.
