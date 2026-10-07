// Accent + background-pattern data (source: .claude/ref-html theme tokens file).
// Colours for components come from CSS variables (src/lib/styles/theme-tokens.css);
// the hex values here exist only because an SVG data-URI cannot read CSS variables.

export type ThemeAccentId =
	| 'indigo'
	| 'purple'
	| 'violet'
	| 'blue'
	| 'teal'
	| 'mint'
	| 'pink'
	| 'orange'
	| 'bronze'
	| 'black';

export type ThemePatternId = 'none' | 'dots' | 'grid' | 'lines' | 'plus' | 'waves' | 'contours';

export type AppTheme = {
	accent: ThemeAccentId;
	pattern: ThemePatternId;
	/** 0.1 – 1, default 0.5 */
	strength: number;
};

export const DEFAULT_APP_THEME: AppTheme = { accent: 'indigo', pattern: 'none', strength: 0.2 };

/** [id, label, light accent, dark accent] */
export const THEME_ACCENTS: [ThemeAccentId, string, string, string][] = [
	['indigo', 'Indigo', '#5B46E5', '#8C7DF7'],
	['purple', 'Purple', '#7A45D6', '#A98DF2'],
	['violet', 'Violet', '#A43BCB', '#CC86EE'],
	['blue', 'Blue', '#1D6AE0', '#6AA3FF'],
	['teal', 'Teal', '#0C7F80', '#3CC4C4'],
	['mint', 'Mint', '#0B8A5E', '#45CE97'],
	['pink', 'Pink', '#D02D68', '#F57BA6'],
	['orange', 'Orange', '#D4570F', '#FF9152'],
	['bronze', 'Bronze', '#946247', '#CFA284'],
	['black', 'Black', '#1C1B26', '#EDECF6']
];

/** [id, label, tile width, tile height, svg body for a given colour] */
const PATTERNS: [Exclude<ThemePatternId, 'none'>, string, number, number, (c: string) => string][] =
	[
		['dots', 'Dots', 20, 20, (c) => `<circle cx="2" cy="2" r="1.4" fill="${c}"/>`],
		['grid', 'Grid', 28, 28, (c) => `<path d="M28 .5H.5V28" fill="none" stroke="${c}"/>`],
		[
			'lines',
			'Lines',
			14,
			14,
			(c) => `<path d="M-2 2l4-4M0 14L14 0M12 16l4-4" stroke="${c}" stroke-width="1.1"/>`
		],
		[
			'plus',
			'Plus',
			26,
			26,
			(c) => `<path d="M13 9v8M9 13h8" stroke="${c}" stroke-width="1.5" stroke-linecap="round"/>`
		],
		[
			'waves',
			'Waves',
			48,
			20,
			(c) =>
				`<path d="M0 10C4 10 8 4 12 4S20 10 24 10 32 16 36 16 44 10 48 10" fill="none" stroke="${c}" stroke-width="1.2"/>`
		],
		[
			'contours',
			'Contours',
			140,
			140,
			(c) =>
				`<g fill="none" stroke="${c}" stroke-width="1"><path d="M70 18c30 0 52 18 50 46s-26 50-54 48-48-24-46-50 20-44 50-44z"/><path d="M70 38c18 0 32 11 31 29s-17 31-34 30-30-15-29-32 13-27 32-27z"/><path d="M70 56c8 0 14 5 13 12s-7 13-14 13-13-6-12-13 5-12 13-12z"/></g>`
		]
	];

export const THEME_PATTERN_OPTIONS: [ThemePatternId, string][] = [
	['none', 'None'],
	...PATTERNS.map(([id, label]) => [id, label] as [ThemePatternId, string])
];

/** Coerce anything read from settings into a valid theme (unknown values fall back to defaults). */
export const normalizeAppTheme = (value: any): AppTheme => {
	const accent = THEME_ACCENTS.some(([id]) => id === value?.accent)
		? value.accent
		: DEFAULT_APP_THEME.accent;
	const pattern = THEME_PATTERN_OPTIONS.some(([id]) => id === value?.pattern)
		? value.pattern
		: DEFAULT_APP_THEME.pattern;
	const n = Number(value?.strength);
	const strength = Number.isFinite(n) ? Math.min(1, Math.max(0.1, n)) : DEFAULT_APP_THEME.strength;
	return { accent, pattern, strength };
};

/**
 * CSS `background-image` value for the pattern, or null for `none`.
 * Drawn in the accent colour at 20% × strength (light) / 30% × strength (dark), per the token file.
 */
/** Karix theme uses a fixed accent (v2 tokens); accent colours apply to Light/Dark only. */
export const KARIX_ACCENT = '#9DB0EE';

export const themePatternImage = (
	theme: AppTheme,
	dark: boolean,
	colorOverride?: string
): string | null => {
	const p = PATTERNS.find(([id]) => id === theme.pattern);
	if (!p) return null;
	const acc = THEME_ACCENTS.find(([id]) => id === theme.accent) ?? THEME_ACCENTS[0];
	const color = colorOverride ?? (dark ? acc[3] : acc[2]);
	const opacity = +(theme.strength * (dark ? 0.3 : 0.2)).toFixed(3);
	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${p[2]}" height="${p[3]}" viewBox="0 0 ${p[2]} ${p[3]}"><g opacity="${opacity}">${p[4](color)}</g></svg>`;
	return `url("data:image/svg+xml,${encodeURIComponent(svg).replace(/"/g, '%22')}")`;
};

/** CSS mask for a pattern tile (opaque strokes); paint it with any colour, e.g. `var(--theme-accent)`. */
export const themePatternMask = (pattern: ThemePatternId): string | null => {
	const p = PATTERNS.find(([id]) => id === pattern);
	if (!p) return null;
	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${p[2]}" height="${p[3]}" viewBox="0 0 ${p[2]} ${p[3]}">${p[4]('#000')}</svg>`;
	return `url("data:image/svg+xml,${encodeURIComponent(svg).replace(/"/g, '%22')}")`;
};

let originalThemeColor: string | null = null;

/**
 * Set / clear the accent on <html>; the tokens CSS re-themes the app from that attribute.
 * Also keeps `<meta name="theme-color">` (PWA / mobile browser chrome) on the chat surface
 * colour, and restores the value the existing theme code set when the accent is cleared.
 */
// `_theme` is only a reactivity trigger: pass the light/dark theme so callers re-run on change.
export const applyThemeAccent = (accent: ThemeAccentId | null, _theme?: unknown) => {
	const root = document.documentElement;
	const meta = document.querySelector('meta[name="theme-color"]');

	if (!accent) {
		if (root.hasAttribute('data-accent')) {
			root.removeAttribute('data-accent');
			if (meta && originalThemeColor) meta.setAttribute('content', originalThemeColor);
			originalThemeColor = null;
		}
		return;
	}

	root.setAttribute('data-accent', accent);
	if (!meta) return;
	if (originalThemeColor === null) originalThemeColor = meta.getAttribute('content');

	// Resolve the color-mix() token to a concrete colour, which theme-color requires.
	const probe = document.createElement('span');
	probe.style.cssText = 'position:absolute;width:0;height:0;color:var(--theme-bg)';
	document.body.appendChild(probe);
	const color = getComputedStyle(probe).color;
	probe.remove();
	if (color) meta.setAttribute('content', color);
};
