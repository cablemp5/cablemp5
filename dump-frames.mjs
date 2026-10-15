// Renders cloud-sea.json from the ascii.rest "cloud sea" piece.
// usage: curl -LO https://ascii.rest/pieces/cloud-sea.js
//        node dump-frames.mjs cloud-sea.js > cloud-sea.json
import { readFileSync } from 'node:fs';

const T0 = 44, SECONDS = 3, FPS = 10; // the scenery: plays forward then back
const B0 = 13, B1 = 42.5; // the birds: forward only, from just before the first enters the crop to after the last leaves
const [CX, CY, W, H] = [108, 12, 88, 88]; // crop: the sun sits in the middle

// The scenery and the birds loop separately, so render the piece once without its birds and diff the two.
// The piece caches its nearest-colour lookups by a coarse key, so a cell's colour depends on which
// frames were drawn before it; turn the cache off so both renders agree everywhere but the birds.
const src = readFileSync(process.argv[2], 'utf8').replace('if (lut[k] !== 255)', 'if (false)');
const noBirds = src.replace(/for \(let i = 0; i < 3; i\+\+\) \{(\s*const bx)/, 'for (let i = 0; i < 0; i++) {$1');
if (noBirds === src || !src.includes('if (false)')) throw new Error('bird loop or colour cache not found in the piece');
const load = async (s) => (await import('data:text/javascript,' + encodeURIComponent(s))).default();
const mod = await import('data:text/javascript,' + encodeURIComponent(src));
const { cols, palette } = mod.meta;
const [withBirds, scenery] = [mod.default(), await load(noBirds)];

const color = new Uint8Array(cols * mod.meta.rows);
const letters = (r) => String.fromCharCode(...color.subarray((CY + r) * cols + CX, (CY + r) * cols + CX + W).map((v) => 97 + v));
const crop = (render, t) => {
  const lines = render(t, { color }).split('\n');
  return Array.from({ length: H }, (_, r) => [lines[CY + r].slice(CX, CX + W), letters(r)]);
};

const frames = [];
for (let i = 0; i < SECONDS * FPS; i++) {
  const rows = crop(scenery, T0 + i / FPS);
  frames.push({ glyphs: rows.map(([g]) => g), colors: rows.map(([, c]) => c) }); // a = palette[0]
}

// per frame, the cells the birds change: [row, col, glyph, colour letter]
const birds = [];
for (let i = 0; i < (B1 - B0) * FPS; i++) {
  const [a, b] = [crop(scenery, B0 + i / FPS), crop(withBirds, B0 + i / FPS)];
  const cells = [];
  for (let r = 0; r < H; r++)
    for (let x = 0; x < W; x++)
      if (a[r][0][x] !== b[r][0][x] || a[r][1][x] !== b[r][1][x]) cells.push([r, x, b[r][0][x], b[r][1][x]]);
  birds.push(cells);
}
if (birds[0].length || birds.at(-1).length) throw new Error('birds in the crop at a loop edge: the loop would jump');
console.log(JSON.stringify({ fps: FPS, palette, frames, birds }));
