<script context="module" lang="ts">
	let uid = 0;
</script>

<script lang="ts">
	// Square brand mark from .claude/ref-html (KX_MARK) for the collapsed sidebar rail.
	// Light/dark variants follow the `.dark` class, like BrandWordmark.
	// Colours are the fixed brand identity, not theme tokens.
	export let className = 'size-7';

	const id = `brand-mk-${uid++}`;
	const K =
		'M210.57,348.74v-124.5h27.02v124.5h-27.02ZM296.96,348.74l-44.35-57.97h-19.4l54.74-66.52h28.64l-50.35,60.52,1.15-13.86,60.52,77.84h-30.95Z';
</script>

<svg class="{className} block dark:hidden" viewBox="0 0 64 64" aria-hidden="true">
	<defs>
		<linearGradient id="{id}-l" x1="0.146" y1="0.854" x2="0.854" y2="0.146">
			<stop offset="0" stop-color="#a42887" />
			<stop offset="1" stop-color="#e6358f" />
		</linearGradient>
	</defs>
	<rect width="64" height="64" rx="14" fill="#160e7a" />
	<g transform="translate(32 32) scale(0.245) translate(-277 -268)">
		<path fill="#ffffff" d={K} />
		<circle fill="url(#{id}-l)" cx="327.69" cy="193.36" r="16.92" />
	</g>
</svg>
<svg class="{className} hidden dark:block" viewBox="0 0 64 64" aria-hidden="true">
	<defs>
		<linearGradient id="{id}-d" x1="0.146" y1="0.854" x2="0.854" y2="0.146">
			<stop offset="0" stop-color="#a42887" />
			<stop offset="1" stop-color="#e6358f" />
		</linearGradient>
	</defs>
	<rect width="64" height="64" rx="14" fill="#ffffff" />
	<g transform="translate(32 32) scale(0.245) translate(-277 -268)">
		<path fill="#160e7a" d={K} />
		<circle fill="url(#{id}-d)" cx="327.69" cy="193.36" r="16.92" />
	</g>
</svg>
