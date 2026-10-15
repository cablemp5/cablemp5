// Renders aurora-fjord.json from the ascii.rest "aurora fjord" piece.
// usage: curl -LO https://ascii.rest/pieces/aurora-fjord.js
//        node dump-frames.mjs aurora-fjord.js > aurora-fjord.json
import { readFileSync } from 'node:fs';

const T0 = 108, SECONDS = 3, FPS = 10; // the aurora arcs over the cabin; plays forward then back on the card
const [CX, CY, W, H] = [74, 0, 110, 100]; // crop: the aurora over the lit cabin, full height

// The piece caches its nearest-colour lookups by a coarse key, so a cell's colour depends on which
// frames were drawn before it; turn the cache off so every frame gets its true nearest colour.
const src = readFileSync(process.argv[2], 'utf8').replace('if (lut[k] !== 255)', 'if (false)');
if (!src.includes('if (false)')) throw new Error('colour cache not found in the piece');
const mod = await import('data:text/javascript,' + encodeURIComponent(src));
const { cols, rows, palette, ground } = mod.meta;
if (palette.length > 75) throw new Error('palette runs past the colour characters 0..z');
const render = mod.default();
const color = new Uint8Array(cols * rows);
const frames = [];
for (let i = 0; i < SECONDS * FPS; i++) {
  const lines = render(T0 + i / FPS, { color }).split('\n');
  frames.push({
    glyphs: lines.slice(CY, CY + H).map((l) => l.slice(CX, CX + W)),
    // palette index per cell as a character: '0' = palette[0]
    colors: Array.from({ length: H }, (_, r) =>
      String.fromCharCode(...color.subarray((CY + r) * cols + CX, (CY + r) * cols + CX + W).map((v) => 48 + v))),
  });
}
console.log(JSON.stringify({ fps: FPS, ground, palette, frames }));
