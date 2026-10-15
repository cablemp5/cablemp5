// Renders cloud-sea.json from the ascii.rest "cloud sea" piece.
// usage: curl -LO https://ascii.rest/pieces/cloud-sea.js
//        node dump-frames.mjs cloud-sea.js > cloud-sea.json
import { pathToFileURL } from 'node:url';

const T0 = 44, SECONDS = 3, FPS = 10; // a stretch with no birds inside the crop
const [CX, CY, W, H] = [108, 12, 88, 88]; // crop: the sun sits in the middle

const mod = await import(pathToFileURL(process.argv[2]).href);
const { cols, rows, palette } = mod.meta;
const render = mod.default();
const color = new Uint8Array(cols * rows);
const frames = [];
for (let i = 0; i < SECONDS * FPS; i++) {
  const lines = render(T0 + i / FPS, { color }).split('\n');
  frames.push({
    glyphs: lines.slice(CY, CY + H).map((l) => l.slice(CX, CX + W)),
    // palette index per cell as a letter: a = palette[0]
    colors: Array.from({ length: H }, (_, r) =>
      String.fromCharCode(...color.subarray((CY + r) * cols + CX, (CY + r) * cols + CX + W).map((v) => 97 + v))),
  });
}
console.log(JSON.stringify({ fps: FPS, palette, frames }));
