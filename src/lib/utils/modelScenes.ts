// @ts-nocheck — illustration asset ported verbatim from .claude/ref-html/MASS-GPT Workspace.html
// (SC_* helpers + SCENES). Colours are part of the artwork, not theme tokens.
// Each scene belongs to one tone; models get a tone from `modelTone()` (ModelTile.svelte),
// so every model shows a stable scene. Static markup only (no user input) — safe for {@html}.

const SC_INK='#2A2438';
const scLeaf=(x,y,r,h,c)=>`<path d="M0 0C${(-h*.27).toFixed(1)} ${(-h*.3).toFixed(1)} ${(-h*.27).toFixed(1)} ${(-h*.72).toFixed(1)} 0 ${-h}C${(h*.27).toFixed(1)} ${(-h*.72).toFixed(1)} ${(h*.27).toFixed(1)} ${(-h*.3).toFixed(1)} 0 0Z" transform="translate(${x} ${y}) rotate(${r})" fill="${c}"/>`;
const scSpark=(x,y,s,c)=>`<path d="M0-8C.8-1.6 1.6-.8 8 0 1.6.8.8 1.6 0 8-.8 1.6-1.6.8-8 0-1.6-.8-.8-1.6 0-8Z" transform="translate(${x} ${y}) scale(${s})" fill="${c}"/>`;
const scRays=(n,r1,r2,c,w=2.6)=>Array.from({length:n},(_,i)=>{const a=i/n*Math.PI*2;return`<path d="M${(Math.cos(a)*r1).toFixed(1)} ${(Math.sin(a)*r1).toFixed(1)}L${(Math.cos(a)*r2).toFixed(1)} ${(Math.sin(a)*r2).toFixed(1)}" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/>`}).join('');
function scPlant(x,y,s,c1,c2,pot,potD){
  return`<g transform="translate(${x} ${y}) scale(${s})"><g class="sc-sway">${scLeaf(0,-25,-44,27,c2)}${scLeaf(0,-25,40,29,c1)}${scLeaf(0,-25,-12,40,c1)}${scLeaf(0,-25,66,21,c2)}${scLeaf(0,-25,-72,20,c1)}${scLeaf(0,-25,14,34,c2)}</g><path d="M-13 -27H13L10 0H-10Z" fill="${potD}"/><rect x="-15.5" y="-30" width="31" height="7" rx="3" fill="${pot}"/></g>`;
}
function scMug(x,y,c){
  return`<g transform="translate(${x} ${y})"><path class="sc-steam" d="M-3.5-28c-3-4 3-6 0-10M4-28c-3-4 3-6 0-10" stroke="#FFFFFF" stroke-width="1.8" fill="none" stroke-linecap="round" opacity=".85"/><path d="M9.5-16h3.5a4.5 4.5 0 0 1 0 9H9.5" stroke="${c}" stroke-width="3" fill="none"/><rect x="-10" y="-21" width="20" height="21" rx="4.5" fill="${c}"/><rect x="-10" y="-21" width="20" height="5" rx="2.5" fill="#FFFFFF" opacity=".18"/></g>`;
}
function scLaptop(x,y,w,c,base,logo){
  const h=w*.62;
  return`<rect x="${x-w/2}" y="${(y-h).toFixed(1)}" width="${w}" height="${h.toFixed(1)}" rx="7" fill="${c}"/><rect x="${x-w/2+3}" y="${(y-h+3).toFixed(1)}" width="${w-6}" height="4" rx="2" fill="#FFFFFF" opacity=".07"/><circle cx="${x}" cy="${(y-h/2).toFixed(1)}" r="${(w*.065).toFixed(1)}" fill="${logo}"/><rect x="${x-w/2-10}" y="${y-2}" width="${w+20}" height="7" rx="3.5" fill="${base}"/>`;
}
const scDesk=(y,c,edge)=>`<rect x="0" y="${y+4}" width="360" height="${176-y}" fill="${c}"/><rect x="0" y="${y+4}" width="360" height="3" fill="${edge}"/>`;
function scPerson(o){
  const H=o.hair,SK=o.skin,SS=o.skinShade,SH=o.shirt,SD=o.shirtShade;
  let back='',front='',collar='',extra='';
  if(o.style==='long')back=`<path d="M-25-2C-28-28-12-35 1-35 17-35 29-26 26-2L30 40C18 48-18 48-30 40Z" fill="${H}"/>`;
  if(o.style==='wavy')back=`<path d="M-24-4C-28-30-10-36 2-35 18-34 28-24 25-4 31 8 25 18 31 30 24 38 12 40 0 40-12 40-24 38-31 30-25 18-31 8-24-4Z" fill="${H}"/>`;
  if(o.style==='bun')back=`<circle cx="4" cy="-33" r="11" fill="${H}"/>`;
  const neck=`<path d="M-8 14H8V38C8 43-8 43-8 38Z" fill="${SS}"/>`;
  const body=`<path d="M-52 94C-52 57-36 40-13 37H13C36 40 52 57 52 94Z" fill="${SH}"/>`;
  if(o.top==='hoodie')collar=`<path d="M-19 37C-15 53 15 53 19 37" fill="none" stroke="${SD}" stroke-width="6" stroke-linecap="round"/><path d="M-5 51V65M5 51V63" stroke="${SD}" stroke-width="2.2" stroke-linecap="round"/>`;
  else if(o.top==='jacket')collar=`<path d="M-11 37 0 62 11 37Z" fill="#FFFFFF"/><path d="M-14 37-3 68-15 58-25 45Z" fill="${SD}"/><path d="M14 37 3 68 15 58 25 45Z" fill="${SD}"/>`;
  else if(o.top==='crew')collar=`<path d="M-13 37C-9 45 9 45 13 37" fill="${SS}"/><path d="M-14 37C-10 47 10 47 14 37" fill="none" stroke="${SD}" stroke-width="3.5"/>`;
  else if(o.top==='cardigan')collar=`<path d="M-12 37 0 53 12 37Z" fill="${SS}"/><path d="M-12 37 0 53V94" fill="none" stroke="${SD}" stroke-width="3"/><path d="M12 37 0 53" stroke="${SD}" stroke-width="3"/><circle cx="0" cy="64" r="1.8" fill="${SD}"/><circle cx="0" cy="76" r="1.8" fill="${SD}"/>`;
  else collar=`<path d="M-11 37 0 50 11 37Z" fill="${SS}"/>`;
  const ears=`<circle cx="-20" cy="3" r="4.5" fill="${SK}"/><circle cx="20" cy="3" r="4.5" fill="${SK}"/>`;
  const head=`<ellipse cx="0" cy="0" rx="20" ry="23" fill="${SK}"/>`;
  if(o.style==='long')front=`<path d="M-21 4C-24-20-9-30 3-29 16-28 24-19 21 4 19-6 13-13 4-15-4-10-14-4-21 4Z" fill="${H}"/>`;
  if(o.style==='wavy')front=`<path d="M-22 6C-26-18-10-30 2-30 16-30 25-18 22 6 19-4 14-10 8-11 4-17-6-17-10-10-15-7-19-2-22 6Z" fill="${H}"/>`;
  if(o.style==='bun')front=`<path d="M-21 3C-23-19-10-27 1-27 13-27 23-19 21 3 17-8 9-14 0-14-9-14-16-8-21 3Z" fill="${H}"/>`;
  if(o.style==='short')front=`<path d="M-21 1C-24-18-15-30-2-31 7-36 21-31 22-19 24-11 22-4 21 1 18-9 11-14 1-14-9-14-16-9-21 1Z" fill="${H}"/>`;
  if(o.style==='curly')front=`<g fill="${H}"><circle cx="-15" cy="-12" r="8.5"/><circle cx="-7" cy="-20" r="9.5"/><circle cx="4" cy="-22" r="9.5"/><circle cx="14" cy="-16" r="8.5"/><circle cx="19" cy="-6" r="5.5"/><circle cx="-19" cy="-3" r="5.5"/></g>`;
  const think=o.pose==='think';
  let face=`<path d="M-12-8H-5M5-8H12" stroke="${H}" stroke-width="2.2" stroke-linecap="round"/>`;
  face+=`<circle cx="${think?-6.5:-8}" cy="${think?0:2}" r="2.3" fill="${SC_INK}"/><circle cx="${think?9.5:8}" cy="${think?0:2}" r="2.3" fill="${SC_INK}"/>`;
  if(o.glasses)face+=`<g fill="none" stroke="${SC_INK}" stroke-width="1.6"><circle cx="-8" cy="2" r="6.4"/><circle cx="8" cy="2" r="6.4"/><path d="M-1.6 1.5H1.6"/></g>`;
  face+=`<path d="M0 5V9" stroke="${SS}" stroke-width="2" stroke-linecap="round"/>`;
  face+=think?`<path d="M-4 14.5H3" stroke="#8A3B3B" stroke-width="1.8" stroke-linecap="round"/>`:`<path d="M-5 13Q0 17.5 5 13" stroke="#8A3B3B" stroke-width="1.8" fill="none" stroke-linecap="round"/>`;
  face+=`<circle cx="-13" cy="9" r="3" fill="#F2728B" opacity=".22"/><circle cx="13" cy="9" r="3" fill="#F2728B" opacity=".22"/>`;
  if(o.phones)extra+=`<path d="M-24 2C-26-33 26-33 24 2" fill="none" stroke="${SC_INK}" stroke-width="4" stroke-linecap="round"/><rect x="-29" y="-5" width="10" height="16" rx="5" fill="${SC_INK}"/><rect x="19" y="-5" width="10" height="16" rx="5" fill="${SC_INK}"/><rect x="-27" y="-2" width="4" height="10" rx="2" fill="#8F7BFF"/><rect x="23" y="-2" width="4" height="10" rx="2" fill="#8F7BFF"/>`;
  if(think)extra+=`<path d="M40 92C36 64 24 46 12 32" fill="none" stroke="${SD}" stroke-width="15" stroke-linecap="round"/><circle cx="9" cy="27" r="7.5" fill="${SK}"/>`;
  return`<g transform="translate(${o.x} ${o.y}) scale(${o.s||1})">${back}${neck}${body}${collar}${ears}${head}${front}${face}${extra}</g>`;
}
const SCENES={
  hr:()=>`<rect width="360" height="170" fill="#FCE7EE"/><circle cx="176" cy="98" r="82" fill="#F8D3DF"/><circle cx="36" cy="28" r="24" fill="#F9DDE6"/>${scSpark(94,32,.8,'#E6A2BA')}${scSpark(210,20,.55,'#E6A2BA')}
    <g class="sc-bob"><rect x="244" y="22" width="100" height="70" rx="12" fill="#FFFFFF"/><circle cx="266" cy="46" r="12" fill="#F4B5CA"/><circle cx="266" cy="42.5" r="4.5" fill="#FFFFFF"/><path d="M258 54a8 6 0 0 1 16 0" fill="#FFFFFF"/><rect x="284" y="38" width="46" height="6" rx="3" fill="#EAD7DF"/><rect x="284" y="49" width="32" height="6" rx="3" fill="#F2E6EB"/><rect x="256" y="68" width="76" height="6" rx="3" fill="#F2E6EB"/><rect x="256" y="78" width="50" height="5" rx="2.5" fill="#F2E6EB"/><circle cx="336" cy="26" r="10" fill="#6E4BD8"/><path d="M331.5 26l3 3 5.5-6" stroke="#FFFFFF" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
    ${scPerson({x:176,y:60,s:1.1,skin:'#F1C4A1',skinShade:'#DDA682',hair:'#2B2140',style:'long',shirt:'#6E4BD8',shirtShade:'#5638BD',top:'v',glasses:true})}
    ${scDesk(138,'#F2C6D4','#F7D7E1')}${scLaptop(176,138,88,'#3B3552','#2A263B','#D9D2FA')}${scPlant(44,142,1.05,'#4E9A71','#3B7F5A','#E88B6E','#D77356')}${scMug(306,142,'#7E63E6')}`,
  massgpt:()=>`<rect width="360" height="170" fill="#E4EEFF"/><circle cx="176" cy="98" r="82" fill="#D0E1FD"/><path d="M22 54h44M34 66h32" stroke="#C3D7F9" stroke-width="7" stroke-linecap="round"/>
    <g transform="translate(302 46)"><g class="sc-spin"><circle r="17" fill="#FFC53D"/>${scRays(8,23,30,'#FFB224')}</g></g>${scSpark(254,26,.9,'#FFFFFF')}${scSpark(334,96,.6,'#FFFFFF')}${scSpark(96,28,.7,'#9DBEF5')}
    ${scPerson({x:176,y:60,s:1.1,skin:'#D9A47F',skinShade:'#C08762',hair:'#1F1A2E',style:'short',shirt:'#3E7D5C',shirtShade:'#2F6549',top:'crew',glasses:true})}
    ${scDesk(138,'#C4D7F6','#D5E3FA')}${scLaptop(176,138,88,'#5E6D86','#475469','#DCE6F7')}${scPlant(46,142,1.15,'#4E9A71','#3B7F5A','#FFFFFF','#E1E4EA')}${scPlant(324,142,.72,'#5BA67C','#3F8A60','#F0B35A','#DD9C3E')}`,
  code:()=>`<rect width="360" height="170" fill="#E2F4EC"/><circle cx="172" cy="98" r="82" fill="#C9EBDB"/>
    <g transform="translate(240 20)"><rect width="108" height="76" rx="11" fill="#1E1B2E"/><circle cx="12" cy="11" r="2.8" fill="#FF6B6B"/><circle cx="21" cy="11" r="2.8" fill="#FFC24B"/><circle cx="30" cy="11" r="2.8" fill="#4CD08B"/><path d="M16 31l-6 6 6 6" stroke="#8F7BFF" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/><rect x="22" y="34.5" width="30" height="5" rx="2.5" fill="#4CD08B"/><rect x="56" y="34.5" width="20" height="5" rx="2.5" fill="#FFC24B"/><rect x="22" y="45.5" width="44" height="5" rx="2.5" fill="#8F7BFF"/><rect x="70" y="45.5" width="16" height="5" rx="2.5" fill="#6FC3FF"/><rect x="22" y="56.5" width="26" height="5" rx="2.5" fill="#6FC3FF"/><rect class="sc-blink" x="52" y="55" width="3" height="8" rx="1" fill="#FFFFFF"/><path d="M88 52l6 6-6 6" stroke="#8F7BFF" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
    ${scSpark(46,32,.8,'#9FD9BF')}${scSpark(214,18,.6,'#9FD9BF')}
    ${scPerson({x:170,y:60,s:1.1,skin:'#C98D66',skinShade:'#AE734F',hair:'#1C1726',style:'curly',shirt:'#F2703F',shirtShade:'#D65A2C',top:'hoodie',phones:true})}
    ${scDesk(138,'#B7E0CC','#C9E9D9')}${scLaptop(170,138,88,'#2F2B40','#1F1C2C','#8F7BFF')}${scPlant(40,142,1.1,'#3F9168','#2E7853','#FFFFFF','#E3DED6')}${scMug(306,142,'#F2703F')}`,
  data:()=>`<rect width="360" height="170" fill="#FFF1D6"/><circle cx="172" cy="98" r="82" fill="#FDE3B2"/>
    <g transform="translate(244 20)"><rect width="102" height="76" rx="11" fill="#FFFFFF"/><rect class="sc-grow" x="14" y="46" width="11" height="20" rx="3" fill="#F6C66B"/><rect class="sc-grow" x="31" y="36" width="11" height="30" rx="3" fill="#F6C66B"/><rect class="sc-grow" x="48" y="42" width="11" height="24" rx="3" fill="#F6C66B"/><rect class="sc-grow" x="65" y="28" width="11" height="38" rx="3" fill="#1F7A70"/><rect class="sc-grow" x="82" y="34" width="11" height="32" rx="3" fill="#F6C66B"/><polyline points="19.5,34 36.5,24 53.5,29 70.5,14 87.5,19" fill="none" stroke="#1F7A70" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="70.5" cy="14" r="3.6" fill="#1F7A70"/></g>
    ${scSpark(58,28,.8,'#F2C27A')}${scSpark(222,18,.6,'#F2C27A')}
    ${scPerson({x:172,y:60,s:1.1,skin:'#E5B08A',skinShade:'#CB926B',hair:'#2A1F2E',style:'bun',shirt:'#1F7A70',shirtShade:'#17635B',top:'jacket',glasses:true})}
    ${scDesk(138,'#F4D398','#F9E1B5')}${scLaptop(172,138,88,'#3A4150','#2A303C','#F6C66B')}
    <g><path d="M42 104l-4-18M50 104l1-20M57 104l5-16" stroke="#3A4150" stroke-width="2.4" stroke-linecap="round"/><circle cx="38" cy="86" r="2.4" fill="#F2703F"/><circle cx="51" cy="84" r="2.4" fill="#6E4BD8"/><circle cx="62" cy="88" r="2.4" fill="#1F7A70"/><rect x="38" y="104" width="24" height="38" rx="5" fill="#1F7A70"/><rect x="38" y="112" width="24" height="4" fill="#FFFFFF" opacity=".25"/></g>
    ${scPlant(320,142,.8,'#4E9A71','#3B7F5A','#FFFFFF','#EDE7DA')}`,
  writer:()=>`<rect width="360" height="170" fill="#EFE9FF"/><circle cx="176" cy="98" r="82" fill="#E1D6FF"/>
    <g transform="translate(56 142)"><path class="sc-glow" d="M30-62L86 0H12L20-56Z" fill="#FFE9A8" opacity=".6"/><rect x="-16" y="-6" width="32" height="6" rx="3" fill="#4B3F7A"/><path d="M0-6L-6-52L18-80" stroke="#4B3F7A" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="-6" cy="-52" r="3.5" fill="#6D5BD0"/><path d="M8-90L40-70L28-56L0-78Z" fill="#6D5BD0"/><circle cx="18" cy="-80" r="3.5" fill="#4B3F7A"/></g>
    <g transform="translate(270 0)"><rect x="4" y="128" width="54" height="14" rx="3" fill="#6D5BD0"/><rect x="8" y="116" width="46" height="12" rx="3" fill="#F2A541"/><rect x="2" y="104" width="52" height="12" rx="3" fill="#4EA37E"/><path d="M12 135h36M14 122h30M8 110h38" stroke="#FFFFFF" stroke-width="1.6" opacity=".55"/></g>
    ${scSpark(236,26,.8,'#B9A6F5')}${scSpark(330,58,.6,'#B9A6F5')}
    ${scPerson({x:176,y:60,s:1.1,skin:'#EDBE9B',skinShade:'#D39F7C',hair:'#3A2230',style:'wavy',shirt:'#E26A92',shirtShade:'#C9537B',top:'cardigan'})}
    ${scDesk(138,'#D6C8FB','#E3D9FC')}
    <path d="M176 146L126 134L128 92L176 101L224 92L226 134Z" fill="#6D5BD0"/><path d="M176 141L132 130L134 96L176 104Z" fill="#FFFFFF"/><path d="M176 141L220 130L218 96L176 104Z" fill="#F4F0FF"/><path d="M142 108l24 4M142 116l24 4M142 124l18 3M186 112l24-4M186 120l24-4M186 128l18-3" stroke="#D4CBF2" stroke-width="2" stroke-linecap="round"/>
    <g><path d="M238 132L256 104" stroke="${SC_INK}" stroke-width="4" stroke-linecap="round"/><path d="M256 104l3-5" stroke="#F2A541" stroke-width="4" stroke-linecap="round"/></g>`,
  ideas:()=>`<rect width="360" height="170" fill="#FFEADC"/><circle cx="198" cy="98" r="82" fill="#FFD9C0"/>
    <g transform="translate(302 50)"><circle class="sc-glow" r="31" fill="#FFE7A3"/>${scRays(8,24,31,'#FFB224',2.4)}<g class="sc-bob"><path d="M0-19a14.5 14.5 0 0 1 8.5 26.3V13H-8.5V7.3A14.5 14.5 0 0 1 0-19Z" fill="#FFC53D"/><path d="M-3.5 5 0-4 3.5 5" stroke="#E08A00" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><rect x="-7.5" y="14" width="15" height="4" rx="2" fill="#8A7B6A"/><rect x="-5.5" y="19.5" width="11" height="3.6" rx="1.8" fill="#8A7B6A"/></g></g>
    ${scSpark(40,32,.8,'#F6B38A')}${scSpark(230,22,.6,'#F6B38A')}
    ${scPerson({x:204,y:60,s:1.1,skin:'#C68A62',skinShade:'#A9704B',hair:'#1E1828',style:'short',shirt:'#2F3E7A',shirtShade:'#243163',top:'v',pose:'think'})}
    ${scDesk(138,'#F8C7A6','#FBD7BF')}${scLaptop(114,138,78,'#34304A','#24213A','#FFC53D')}${scPlant(334,142,.8,'#4E9A71','#3B7F5A','#FFFFFF','#EDE0D6')}${scMug(40,142,'#2F3E7A')}`
};

const TONE_SCENE = {
	rose: 'hr',
	blue: 'massgpt',
	green: 'code',
	amber: 'data',
	violet: 'writer',
	orange: 'ideas'
};
const cache = {};

/** SVG markup (360×170, cover-cropped) for a tone: rose | blue | green | amber | violet | orange. */
export const modelScene = (tone: string): string => {
	const id = TONE_SCENE[tone] ?? 'massgpt';
	if (!cache[id])
		cache[id] =
			`<svg viewBox="0 0 360 170" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">${SCENES[id]()}</svg>`;
	return cache[id];
};
