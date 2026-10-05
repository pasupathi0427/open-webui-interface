# MASS-GPT Redesign — Phase 0 Analysis & Plan

Repo: `open-webui-interface/` (branch state: only `.gitignore` modified). Paths are relative to it.
Copied from the approved Phase 0 plan. Updated to as-built in Phase 8.

## 0. Context
Re-skin the Open WebUI fork to MASS-GPT and add token-usage governance (F1–F6) without changing existing behaviour. Phase 0 = analysis only; no source edited.

## 1. Corrections to CLAUDE.md §4 (verified by reading the repo)
| CLAUDE.md says | Reality |
|---|---|
| `PersistentConfig` in `config.py` | **Does not exist in this fork.** Config is a DB key/value `Config` table (`models/config.py`): env default → `DEFAULT_CONFIG` dict (`config.py` ~2826–3130) → `Config.get/get_many/upsert`. Admin toggles go through `ADMIN_CONFIG_KEYS` + `AdminConfig` in `routers/auths.py` (`/api/v1/auths/admin/config`). Public flags reach `$config` via `main.py` `GET /api/config`. |
| Tailwind + `tailwind.config` tokens | **Tailwind 4** (`@import 'tailwindcss'; @config '../tailwind.config.js'` in `src/tailwind.css`). Tokens go in CSS (`@theme`/CSS vars), not the JS config. Svelte 5, SvelteKit 2. |
| Admin Settings "tabs" file | No `admin/Settings.svelte`. Tabs live in `src/lib/components/chat/SettingsModal.svelte` (import list, `adminSettingGroups`, `adminSettings[]`, `{:else if selectedTab===…}` chain). Routes only redirect to `/?settings=admin:<tab>`. |
| `src/service-worker`, offline shell | **No service worker exists** (no `src/service-worker.*`, no vite-plugin-pwa; `+layout.svelte:87-100` actively unregisters workers). Manifest is served dynamically by `main.py:2870` `/manifest.json`; `static/manifest.json` is `{}`. "Don't break SW caching" → nothing to break; we must **not add** one. |
| Theme is a per-user setting | Theme is **per-device `localStorage.theme`** (`system/dark/oled-dark/light/karix/her`), applied by `applyTheme` in `chat/Settings/General.svelte` and an inline FOUC script in `src/app.html` (also sets `theme-color`). A `karix` theme/brand variant already exists. F4 "persists per user" therefore needs a new `settings.ui.*` key. |
| Background image storage | Base64 data URL in user settings `ui.backgroundImageUrl` (no upload endpoint). Applied in `Chat.svelte:181-190`, rendered `4278-4287`. Backend `InterfaceSettings` (`models/users.py:67`) is `extra='forbid'` → **any new ui key must be added there or the save is rejected.** |
| Alembic in `migrations/` | Alembic at `backend/open_webui/migrations/versions/`; single head **`d4c1a8e37b62`**. No peewee. |
| "department" | No `department` field on `User` (`info` is free-form; OAuth claims not stored). `Group` (+`GroupMember`, `Group.data` JSON) is the right entity; groups are already synced from OAuth/LDAP claims. |
| Analytics covers all usage | Analytics sums `chat_message.usage`, written only for **saved chats with chat_id+message_id**. API-key calls without chat_id and temporary chats are **not recorded** → undercount. A hard quota needs its own counter. |
| Missing from CLAUDE.md | Streaming/usage code sits in `utils/middleware.py` (listed "do not touch"); counting requires a minimal hook there (needs approval, §10-D1). i18n parse script rewrites **all** locales. |

## 2. Tooling check (what exists, what I'll use)
- **frontend-design skill: NOT in the available skill list.** I won't pretend to use it. Substitute: the two reference HTML files are the visual spec; UI sections below are derived from them directly. (If you have the skill, tell me where it's installed.)
- **graphify**: skill is installed, but `graphify-out/` doesn't exist. Not needed for Phase 0; optional later to map the codebase (writes a `graphify-out/` folder — your call).
- **Pony tail**: found as the *ponytail* plugin (minimal-code mode, not a design tool). I use it as a constraint: reuse existing components/helpers, fewest files, no new dependencies.
- **Serena MCP** (symbol navigation) is available; I'll use it in implementation phases for safe symbol-level edits.
- Explore subagents were used for read-only codebase mapping.

## 3. Reference extraction
**Tokens** (single source: `MASS-GPT Theme Tokens.html`; light + dark, 10 accents). Values are computed, so reproduce the formulas, don't hand-copy hex:
- Accents `[name, light accent, light hover, dark accent, dark hover]`: indigo `#5B46E5 #4A36D1 #8C7DF7 #A396FA` (**Karix default**), purple `#7A45D6 #6835C2 #A98DF2 #BBA4F6`, violet `#A43BCB #8E2DB3 #CC86EE #D8A0F3`, blue `#1D6AE0 #1858C0 #6AA3FF #8AB6FF`, teal `#0C7F80 #0A6B6C #3CC4C4 #62D2D2`, mint `#0B8A5E #08744F #45CE97 #6ADAAE`, pink `#D02D68 #B42358 #F57BA6 #F899BB`, orange `#D4570F #B8490B #FF9152 #FFA874`, bronze `#946247 #7E523A #CFA284 #DAB59C`, black `#1C1B26 #000000 #EDECF6 #FFFFFF`.
- Neutrals light/dark: bg `#FFFFFF/#12111C`, bg-2 `#F8F8FB/#181725`, bg-3 `#F1F0F6/#23222F`, surface `#FFFFFF/#1A1927`, line `#E8E7F0/#2A293A`, line-2 `#D9D7E5/#3A394D`, ink `#17162C/#EEEDF7`, ink-2 `#4A4960/#C1BFD3`, ink-3 `#74738C/#8F8DA8`, ink-4 `#A4A3B8/#66647E`, on-accent `#FFFFFF/#12111C`.
- Derived (per accent): soft = accent 10%(light)/16%(dark) into surface; line = 30%/40%; side = accent 5% into bg-2; side-hover 9%; side-on 15% into surface; page = 3% into bg-2. Workspace file uses `color-mix(in srgb, …)` for the same → use CSS `color-mix`, no JS needed.
- Tones (Workspace): rose `#C2185B`, blue `#2358C4`, green `#0E7A52`, amber `#A15C00`, violet `#6D3FD6`, orange `#C2410C` (dark: `#F48FB1 #7AA7FF #43C993 #F0B35A #B39BFA #FF9A62`).
- Radii/shadows/easing: cards 22px (picker) / 16–18px (glance), `--sh-1/2/3`, `--ease cubic-bezier(.2,.8,.2,1)`, `--spring cubic-bezier(.34,1.4,.64,1)`; fonts Inter + JetBrains Mono (already similar stack; no new font dependency needed unless approved).
- **Pattern SVGs** (tile, drawn in accent at 20%×strength light / 30%×strength dark, default strength 50%): dots 20×20, grid 28×28, lines 14×14, plus 26×26, waves 48×20, contours 140×140 (+ none). Path data is in the tokens file `PATTERNS` array → port verbatim into `utils/themes.ts`.
- Token file's own CSS convention: `:root[data-accent=…]` / `:root[data-appearance="dark"]`. Our app uses the `dark` **class**, so selectors become `.dark[data-accent=…]`.

**Choose Model card (picker modal)**: centered modal (`.mp-wrap`), header + pill search (50px, radius 999) + scroll body + footer. Grid 3-col desktop / 2-col tablet / 1-col mobile (mobile card turns horizontal with 116px art). Each `.mcard`: 22px radius, 1.5px line border, 8px padding, **art strip** (162px, tone-tinted scene) with overlapping **icon badge** (50px, tone-tinted), body: title 18/600, description 13.5px (mobile: 2-line clamp), tag pill, selected check (accent circle), hover lift + badge rotate, radio semantics (`role=radio`, roving tabindex). Footer: "make default" checkbox + Cancel + primary "Start with <model>". Empty state text. Our adaptation: cards show **name + full description** from `$models` (already access-filtered), search via same Fuse behaviour as `Selector.svelte`, no "coming soon/notify" states, art strip uses tone from deterministic hash of model id unless model has a configured icon (see D8).

**Chat Space at a Glance card**: section titled "At a glance" with source/updated line, horizontal scroll-snap track of stat cards (`.qcc`, 236px basis, 16px radius): icon chip, label, big value + unit, mini viz (ring/spark/bar/status), caption; edge-fade mask, prev/next arrows; mobile = 2-col `.mstat` grid + one row card. Cards open a detail popover in the reference — **omit detail popover in v1** (display only).

## 4. Feature → files (F1–F6)
- **F1 Usage/Token Management (admin)**: backend `config.py`, `routers/auths.py`, `main.py`, `models/token_usage.py`*, `utils/token_quota.py`*, `routers/usage.py`*, migration*, `utils/middleware.py`(approval); frontend `SettingsModal.svelte`, `AdminTabIcon.svelte`, `settings-search.ts`, `admin/Settings/Usage.svelte`*, `apis/usage/index.ts`*, `translation.json`.
- **F2 Usage page**: `routes/(app)/usage/+page.svelte`*, `components/usage/UserUsage.svelte`*, `AdminUsage.svelte`*, `UserMenu.svelte` (link), reuse `admin/Analytics/ChartLine.svelte`, `routers/usage.py`*.
- **F3 Choose Model**: `ModelPickerModal.svelte`*, `Navbar.svelte`, `(app)/+layout.svelte` (first-login trigger), `models/users.py` (`ui.hasSeenModelPicker`), `stores/index.ts` (Settings type).
- **F4 Themes/backgrounds**: `theme-tokens.css`*, `app.css`, `utils/themes.ts`*, `InterfaceSettings.svelte`, `Chat.svelte` (bg lines only), `models/users.py`, `stores/index.ts`, (cond.) `Settings/General.svelte`.
- **F5 Glance**: `ChatGlance.svelte`*, `Placeholder.svelte`, admin Interface tab (toggle), `config.py`, `auths.py`, `main.py`, `stores/index.ts`.
- **F6 Response header toggles**: `ResponseMessage.svelte` (wrap lines ~677-681 logo, ~685-693 name), admin Interface tab, `config.py`, `auths.py`, `main.py`, `stores/index.ts`.

## 5. Impact map
### Files to MODIFY — 20 (2 conditional)
Frontend (15):
1. `src/app.css` — import tokens file; no existing rule changed.
2. `src/lib/stores/index.ts` — `Config.features` (+4 flags), `Settings` type (`appTheme`, `hasSeenModelPicker`).
3. `src/lib/components/chat/SettingsModal.svelte` — register `admin:usage` tab (import, group, entry, branch).
4. `src/lib/components/admin/Settings/AdminTabIcon.svelte` — usage icon id.
5. `src/lib/utils/settings-search.ts` — search prefixes for new tab.
6. `src/lib/components/admin/Settings/Interface.svelte` (confirm filename; imported as `AdminInterface`) — F5/F6 switches.
7. `src/lib/components/common/InterfaceSettings.svelte` — "Theme & background" section; existing background-image control kept untouched.
8. `src/lib/components/chat/Chat.svelte` — **only** background-computation (181-190) and background div (4278-4287); no other region.
9. `src/lib/components/chat/Placeholder.svelte` — mount `ChatGlance` behind flag.
10. `src/lib/components/chat/Navbar.svelte` — new button sibling before temp-chat block (line ~180, inside `gap-2` container line 177).
11. `src/lib/components/chat/Messages/ResponseMessage.svelte` — two `{#if}` wrappers only.
12. `src/routes/(app)/+layout.svelte` — first-login picker trigger (next to changelog logic ~355) + mount modal.
13. `src/lib/components/layout/Sidebar/UserMenu.svelte` — "Usage" link after Playground (~470).
14. `src/lib/i18n/locales/en-US/translation.json` — new keys only.
15. *(conditional, D6)* `src/lib/components/chat/Settings/General.svelte` — `theme-color` follows accent.
Backend (5):
16. `backend/open_webui/config.py` — env vars + `DEFAULT_CONFIG` keys (§6).
17. `backend/open_webui/routers/auths.py` — `ADMIN_CONFIG_KEYS` + `AdminConfig` fields.
18. `backend/open_webui/main.py` — mount `usage` router; `/api/config` flags (+`get_many` list); **pre-check call in `chat_completion` after metadata built (~1299)**.
19. `backend/open_webui/models/users.py` — `InterfaceSettings` new optional keys (`appTheme`, `hasSeenModelPicker`).
20. *(approval D1)* `backend/open_webui/utils/middleware.py` — one call to `record_usage(...)` at the two existing usage-save points (non-streaming ~4363, streaming ~6555). No change to stream handling.

### Files to CREATE — 22 (icon count approximate, ≤6 new)
Frontend (14): `src/lib/styles/theme-tokens.css` (tokens, light/dark, accents, patterns); `src/lib/utils/themes.ts` (accent list, pattern tile SVGs, apply/clear helpers); `src/lib/apis/usage/index.ts`; `src/lib/components/chat/ModelPickerModal.svelte`; `src/lib/components/chat/ChatGlance.svelte`; `src/lib/components/admin/Settings/Usage.svelte`; `src/lib/components/usage/UserUsage.svelte`; `src/lib/components/usage/AdminUsage.svelte`; `src/routes/(app)/usage/+page.svelte`; up to 6 icon components in `src/lib/components/icons/` (only those not already present: e.g. `LayoutGrid`, `Gauge`, `Lock`, `Flame`, `Zap`, `Sparkles` — Phase 1 greps first and reuses).
Backend (5): `models/token_usage.py`; `routers/usage.py`; `utils/token_quota.py` (limit resolve, check, record, estimate); `migrations/versions/<new>_add_token_usage_tables.py`; `test/test_token_quota.py` (one small runnable test).
Docs (2): `docs/PLAN.md`, `CHANGELOG-MASSGPT.md`.
Files deleted: none.

### DO NOT TOUCH (confirmed locations)
`chat/Artifacts.svelte`, `chat/FileNav/{FilePreview,PortPreview}.svelte`, `common/FullHeightIframe.svelte`, `chat/ChatControls/Embeds.svelte`, `chat/Messages/Markdown/{HTMLToken,MarkdownTokens,MarkdownInlineTokens}.svelte`, `Citations/CitationModal.svelte`, `Messages/CodeBlock.svelte`, `PyodideFileNav.svelte`, `common/ToolCallDisplay.svelte`, `lib/apis/streaming/index.ts`, and in `Chat.svelte` the regions: embed-origin trust (~1431-1436), artifact contents (~1973-1988), `chatEventHandler` (~1203), `chatCompletedHandler` (~2563), `chatActionHandler` (~2571). Also: `app.html` FOUC/splash/`getKarixBrandAsset`, `main.py` manifest/branding blocks (2870-2935), `models/config.py` internals, existing migrations, non-en-US locale files by hand.

## 6. New admin configs
| Name | Env var | Config key | Default | Type | UI location |
|---|---|---|---|---|---|
| Enable token limits | `ENABLE_TOKEN_LIMITS` | `usage.enable_token_limits` | `False` | bool | Admin → Usage |
| Limit period | `TOKEN_LIMIT_PERIOD` | `usage.period` | `daily` (`daily`/`monthly`) | enum | Admin → Usage |
| Revoke duration (minutes) | `TOKEN_REVOKE_MINUTES` | `usage.revoke_minutes` | `120` | int | Admin → Usage |
| Default limit (tokens/period; 0 = unlimited) for users in no limited group | `TOKEN_DEFAULT_LIMIT` | `usage.default_limit` | `0` | int | Admin → Usage |
| Multi-group policy | `TOKEN_MULTI_GROUP_POLICY` | `usage.multi_group_policy` | `max` (`max`/`min`) | enum | Admin → Usage |
| Count mode | `TOKEN_COUNT_MODE` | `usage.count_mode` | `total` (`total`/`output`) | enum | Admin → Usage |
| Warn threshold % (0 = off) | `TOKEN_WARN_PERCENT` | `usage.warn_percent` | `80` | int | Admin → Usage |
| Admins exempt | `TOKEN_ADMIN_EXEMPT` | `usage.admin_exempt` | `True` | bool | Admin → Usage |
| Chat space at a glance | `ENABLE_CHAT_GLANCE` | `ui.enable_chat_glance` | `False` | bool | Admin → Interface |
| Show model name on responses | `SHOW_RESPONSE_MODEL_NAME` | `ui.show_response_model_name` | `True` | bool | Admin → Interface |
| Show model logo on responses | `SHOW_RESPONSE_MODEL_LOGO` | `ui.show_response_model_logo` | `True` | bool | Admin → Interface |
Per-department limits are **not** global config: stored as `Group.data.config.token_limit = {"tokens": N}` and edited in the Usage tab (writes the full `data` object — `update_group_by_id` replaces `data` wholesale and would otherwise wipe `config.share`). Flags exposed to the frontend in `/api/config` under `features`.

## 7. DB schema + migration
New revision, `down_revision = 'd4c1a8e37b62'`, idempotent (`inspector.get_table_names()` guard, mirroring `4de81c2a3af1_add_pinned_note_table.py`).
- `token_usage` (append-only): `id` Text PK, `user_id` Text, `model_id` Text null, `chat_id` Text null, `input_tokens` BigInteger, `output_tokens` BigInteger, `total_tokens` BigInteger, `source` Text (`provider`/`estimate`), `via` Text (`ui`/`api_key`), `created_at` BigInteger (epoch, matches `chat_message`). Indexes: `(user_id, created_at)`, `(created_at)`.
- `token_quota_state`: `user_id` Text PK, `window_start` BigInteger, `blocked_until` BigInteger null, `updated_at` BigInteger.
- Semantics: used = `SUM(token_usage)` since `max(period_start, window_start)`. When used ≥ limit → `blocked_until = now + revoke`. On first check after `blocked_until`, set `window_start = blocked_until` (counter restarts) and clear block. Manual reset = set `window_start = now`, clear block.
- Rollback: `downgrade()` drops both tables (no data in existing tables altered). Config keys are seeded by `Config.seed_defaults`, no migration needed; removing them is harmless.
- Config/ui keys need no migration (`settings.ui` is a JSON dict).

## 8. API changes and auth
| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/v1/usage/me` | verified user | own used/limit/%/blocked_until/history (daily series) |
| `GET /api/v1/usage/admin/summary?start&end&group_id&model_id` | **admin** | per-user + per-group consumption vs limit |
| `POST /api/v1/usage/admin/reset` `{user_id? group_id?}` | **admin** | manual reset |
| `GET/POST /api/v1/auths/admin/config` (existing) | admin | + new toggles via `ADMIN_CONFIG_KEYS` |
| `POST /api/v1/groups/id/{id}/update` (existing) | admin | store `data.config.token_limit` |
| `GET /api/config` (existing) | public | + `features.enable_token_limits/enable_chat_glance/show_response_model_*` |
| `POST /api/chat/completions` (changed) | verified user / API key | returns **429** `{code:"token_limit_reached", blocked_until, used, limit}` before any work starts |
- Pre-check at `main.py` after metadata (~1299), before the 1805 fan-out; the `except HTTPException: raise` (1640) passes it through. Because background-task mode shows errors via `chat:message:error`, the same check is also called at the start of `process_chat_payload` so UI errors render inline (existing `Chat.svelte:1284` path — no streaming change). **Phase 2 must verify how the frontend renders a non-OK HTTP response from `chatCompletion` (`apis/openai/index.ts:392`); unverified today.**
- API keys use the same endpoint → counted/blocked uniformly (D4).
- Overshoot: the check is "already ≥100%" so the final response may exceed the limit slightly (documented; no prompt-size estimation pre-flight).
- Counting: provider `usage` (already normalized by `utils/response.py`); fallback `tiktoken` estimate of output text (already a dependency) when absent. Warning at 80%: surfaced by `/usage/me` and a toast/banner in the Usage UI and glance card.
- Non-admin cannot reach `/usage/admin/*` (`get_admin_user`) nor the admin tab (`SettingsModal` admin guard).

## 9. UI design notes (derived from references; frontend-design skill unavailable)
- **Tokens**: `theme-tokens.css` defines neutrals + 10 accents × light/dark under `[data-accent]` and `.dark[data-accent]`, exposed through Tailwind 4 `@theme` aliases; components use `var(--accent)` etc., never hex.
- **ModelPickerModal**: reuses existing `Modal` pattern and Fuse search from `ModelSelector/Selector.svelte`; items from `$models` mapped like `ModelSelector.svelte:71-75`; descriptions via `resolveLocalizedModelDescription`; selecting sets `selectedModels` (same binding as chat input). Grid `lg:3 / md:2 / base:1`; mobile horizontal card; full keyboard (radio group, Esc, focus trap); touch targets ≥44px. Opened from navbar button (new button, tooltip "Choose model", `max-md` shows icon only) and from first-login. Chat-input `ModelSelector` untouched.
- **First login**: `ui.hasSeenModelPicker` (backend per-user); layout opens picker once when false and user has >1 model, sets flag on close.
- **Themes (Settings → Interface)**: new section above/below existing background row: appearance follows existing theme; accent swatch chips, pattern chips (none + 6), strength slider, "custom image" = existing upload. Stored `ui.appTheme = {accent, pattern, strength}`. Precedence: folder/model image → user custom image → pattern → licence image (existing order preserved; pattern slots after user image). Applied by setting `data-accent` on `<html>` and rendering the pattern via CSS `background-image` data-URI inside the existing `Chat.svelte` background div.
- **Glance card**: v1 tiles (all from existing endpoints/`usage/me`): Tokens used today (ring + %), Messages today, Chats this week, Most-used model; scroll-snap track desktop, 2-col grid mobile; hidden unless `features.enable_chat_glance`.
- **Usage page**: user: gauge/ring + limit + reset countdown + `ChartLine` daily history; admin: table (user, group, used, limit, %, blocked_until) with date/group/model filters, reset action; responsive table → card list below 768px.
- **A11y**: aria labels, focus-visible rings, contrast checked in light/dark for all 10 accents (black accent in dark is `#EDECF6`).

## 10. Risk register
| Risk | Level | Mitigation |
|---|---|---|
| Iframe/artifact injection broken | High | No edits to listed files; `Chat.svelte` edited only in two background regions; diff review rule: no hunk outside them. Regression checklist §8 each phase. |
| Streaming / usage hook in `middleware.py` | High | Single call to new helper wrapped in try/except (never raises); behind D1 approval; no change to chunk handling. Without approval fall back to summing `chat_message` (undercounts). |
| Block semantics wrong for background-mode errors | Med | Check at both `main.py` and `process_chat_payload`; test UI + API-key + temp chat. |
| Group `data` overwritten on update | Med | Usage tab always sends merged full `data`. |
| `InterfaceSettings` `extra='forbid'` rejects new keys | Med | Add keys in same commit as frontend; test save round-trip. |
| Quota race / double count | Low-Med | Append-only inserts; block computed from sums; acceptable overshoot documented. |
| PWA/theme-color | Low | No SW exists, none added; manifest untouched; `app.html` untouched unless D6 yes. |
| Mobile layout of navbar (extra icon) | Med | Icon-only <md; tested at 360–420px with temp-chat + new-chat buttons. |
| i18n | Med | All strings via `$i18n.t`; run `npm run i18n:parse` but **commit only en-US** (D9), else 60+ locale files churn. |
| Upstream merge conflicts | Med | New components wired with small edits; keep diffs minimal. |
| Base64 backgrounds bloating settings | Low | Pattern is data-free (tokens only); existing image unchanged. |
| Tailwind 4 token wiring differs from CLAUDE.md | Low | Use CSS vars + `@theme`; verify build in Phase 1. |

## 11. Test plan
**Per device** (Chrome DevTools + one real phone): Desktop ≥1280, tablet 768–1024, mobile ≤420 — navbar fits with new button; picker grid 3/2/1; glance scroll/grid; usage page table→cards; Interface theme section usable by touch; no horizontal page scroll.
**PWA**: manifest loads/valid (Lighthouse), install prompt works, no service worker registered (expected, unchanged), `theme-color` correct for light/dark/oled/karix (and accent if D6), splash/FOUC unchanged, icons unchanged.
**Functional**: chat send/stream/stop/regenerate/edit/continue; iframe/HTML artifacts; code/KaTeX/mermaid/citations/tools; file/image/voice; chat-input selector unchanged; temp chat; Interface existing options + background image; other admin tabs; non-admin 403/redirect on admin endpoints & tab.
**Quota**: limit 1k tokens → block at 100% with friendly message (UI chat, temp chat, API key); auto-restore after revoke minutes (test with 1 min); manual reset; multi-group max/min; admin exempt; streaming + non-streaming counting; estimate fallback.
**Automated**: `test_token_quota.py` (resolve limit, block/unblock timing, reset), `npm run lint`, `npm run check`, `npm run build`.

## 12. Priority & phased commit plan (REVISED per owner: UI first, usage later)
**Priority order:** (1) F4 themes/backgrounds → (2) F3 Choose Model landing + navbar button → (3) F5 glance + F6 response toggles → (4) F1/F2 usage & token limits.
Rationale: 1–3 are mostly frontend, low-risk, and need only tiny backend additions; usage touches DB + the chat path, so it comes last.

- **P1 Foundations** (no visible change): tokens css + `app.css` import; `themes.ts`; icons; store types.
- **P2 Themes & backgrounds (F4)**: `models/users.py` (`appTheme` key, same commit as UI), `InterfaceSettings.svelte` section, `Chat.svelte` background regions.
- **P3 Model landing (F3)**: `ModelPickerModal.svelte`, navbar button, first-login flag (`hasSeenModelPicker`), `(app)/+layout.svelte`.
- **P4 Glance + response toggles (F5/F6)**: config keys (3 flags) + `auths.py` + `main.py` `/api/config`, admin Interface switches, `ChatGlance.svelte`, `ResponseMessage.svelte`. Glance v1 tiles that need usage data (tokens) are omitted until P6; ship with messages/chats/top-model only.
- **P5 QA gate for UI** (full §8 checklist, 3 device classes, PWA) — sign-off before touching usage.
- **P6 Usage backend (F1)**: migration + models; `token_quota.py` + test; usage config keys; `usage` router; `main.py` pre-check; (D1) middleware hook.
- **P7 Usage UI (F1/F2)**: admin Usage tab, groups limit editing, `/usage` page + menu link, glance token tile, 80% warning.
- **P8 Final regression**, changelog, `docs/PLAN.md` updated to as-built.
Every commit includes its `CHANGELOG-MASSGPT.md` entry (§9 template). P6/P7 can be re-scoped after P5 without affecting P1–P5.

## 12a. Upstream-merge safety (design rule for all phases)
Goal: future community/upstream Open WebUI updates merge with minimal conflicts.
1. **New files over edits.** All logic lives in new files (`theme-*`, `themes.ts`, `ModelPickerModal`, `ChatGlance`, `token_quota`, `usage` router/models). Existing upstream files get only small, single-purpose hunks (an import + one tag/`{#if}` + one prop), never reformatting or moved code.
2. **One-hunk-per-file rule** where possible; each hunk marked with a short `// CUSTOM:` comment so merge conflicts are easy to spot and re-apply. A tracked list of every upstream hunk is kept in `CHANGELOG-MASSGPT.md` ("Upstream touchpoints") so a merge is a checklist, not archaeology.
3. **No refactors, renames, or prettier/format-only changes** in upstream files; no reordering of existing imports/keys.
4. **Config/ui settings:** new keys are additive (new `ui.*` keys, new `DEFAULT_CONFIG` entries appended in one block at the end of the dict); never change existing keys' semantics.
5. **Migrations:** one new revision chained on the current head; if upstream adds revisions, we rebase ours by changing only `down_revision` (kept idempotent). No edits to existing migrations.
6. **Tokens/themes are additive CSS** (`[data-accent]`-scoped); no overrides of existing Tailwind/gray variables or the existing `karix`/dark theme code; `app.html` untouched.
7. **Hardest-conflict files** (high upstream churn): `Chat.svelte`, `ResponseMessage.svelte`, `Navbar.svelte`, `SettingsModal.svelte`, `main.py`, `middleware.py`, `config.py`. For these, the hunk is minimal and delegates to a new component/helper. `middleware.py` hook (D1) is a single line calling `record_usage` — if the owner prefers zero touch, the fallback is counting from `chat_message` (D1).
8. **i18n:** only `en-US` keys added (D9); other locales stay as upstream generates them.
9. **Merge rehearsal:** before P5 sign-off, do a dry-run `git merge` of latest upstream into a scratch branch to confirm conflicts are limited to the listed touchpoints (needs the upstream remote — owner to confirm remote name).

## 13. Open questions — recommended defaults (**all need owner decision**)
1. Department = Groups? **Rec: yes**, `Group.data.config.token_limit`.
2. Revoke window: **Rec:** fixed from the moment 100% is hit; counter restarts when it expires; usage period daily (configurable monthly).
3. Per-user vs shared pool: **Rec: per-user limit** taken from the user's group (pool needs more design).
4. Multi-group: **Rec: max** (matches existing most-permissive permission merge); configurable `min`.
5. Count: **Rec: input+output**, configurable output-only; **API keys counted: yes.**
6. Warn at threshold: **Rec: yes, 80%**, configurable, shown in Usage page + glance card.
7. F6: **Rec: two toggles, both ON.**
8. Glance contents: **Rec:** tokens used/limit, messages today, chats this week, top model (existing data only). Default OFF.
9. First-login flag: **Rec: backend** (`settings.ui.hasSeenModelPicker`), survives devices.
10. Admin bypass: **Rec: admins exempt (configurable).**
Additional decisions found during analysis:
- **D1** Allow minimal `record_usage()` hook in `utils/middleware.py` (no stream-handling change)? Rec: yes; otherwise API/temp traffic is uncounted.
- **D2** Reset by admin (nice-to-have): Rec: include (small endpoint + button).
- **D3** Re-skin scope: Rec: tokens apply to new components + chat background only in this program; full-app chrome re-skin is a separate approval (much higher regression risk).
- **D4** Limits scope for internal calls (title/tags/follow-ups generated for the user): Rec: count only the main chat response path.
- **D5** `frontend-design` skill missing — provide it or accept reference-HTML-as-spec.
- **D6** `theme-color` follow accent? Rec: no (keep existing per-theme values; fewer FOUC risks). CLAUDE.md §1.4 says theme changes must update it — confirm interpretation.
- **D7** Include a navbar "Choose model" admin toggle? Rec: no (YAGNI).
- **D8** Model card art strip: Rec: tone from model id hash + generic icon (models have no tone/icon metadata).
- **D9** i18n: commit en-US only? Rec: yes.
- **D10** Is the `ow-ragflow-sync` repo in scope? Rec: no — this work lives only in `open-webui-interface`.

## 14. CHANGELOG-MASSGPT.md (to be created on approval)
Template from CLAUDE.md §9, first entry:
```
## [2026-10-05] Phase 0 — Phase 0 - analysis only, no source changes
- Author: Claude (Phase 0 session) / reviewer: <owner>
- Files modified: none
- Files created: docs/PLAN.md, CHANGELOG-MASSGPT.md
- Files deleted: none
- Config added: none
- DB migration: none
- Risk / regression notes: none (no source changes)
- Verified: read-only analysis of repo; reference HTML reviewed
```

## 15. Verification of this plan
Plan itself is verified by approval; each phase is verified by §11 and the CLAUDE.md §8 checklist before sign-off.
