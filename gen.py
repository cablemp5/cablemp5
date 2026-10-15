"""Builds card.svg: a neofetch-style card with an animated halftone ASCII aurora.

Art: "aurora fjord" from https://ascii.rest (MIT, github.com/bas3line/ascii), 3 s of frames
rendered by dump-frames.mjs into aurora-fjord.json (dot glyphs plus a palette character per
cell, '0' = PALETTE[0]). Each glyph is drawn as a dot of its size so the art does not depend
on the viewer's fonts. The frames play forward then back, so the loop has no seam. The info
text types itself out on load.

Edit INFO below, then run `python gen.py`.
"""
import json
from collections import Counter
from xml.sax.saxutils import escape

INFO = [  # (key, value) | '' for a spacer | '- Title' for a section rule
    ('School', 'Virginia Tech'),
    ('Major', 'Computer Science, junior'),
    ('Location', 'Blacksburg, VA'),
    ('Seeking', 'SWE internship, summer 2027'),
    '',
    ('Languages', 'Python, Java, TypeScript, JavaScript'),
    ('Stack.Web', 'React, Next.js, Tailwind, Node.js'),
    ('Stack.Data', 'FastAPI, PostgreSQL, MongoDB'),
    ('Stack.ML', 'pandas, OpenCV'),
    ('Interests', 'machine learning, AI, game modding'),
    ('Building', 'Marvel Rivals mods + mod tooling'),
    '',
    '- Contact',
    ('Email', 'cmikec12@gmail.com'),
    ('LinkedIn', 'in/caleb-m-collins'),
    ('Discord', 'cablemp5'),
]
USER, HOST = 'caleb', 'collins'

with open('aurora-fjord.json', encoding='utf-8') as f:
    DATA = json.load(f)
PALETTE, FPS = DATA['palette'], DATA['fps']  # the piece's own palette: the card's text and swatches come from it
FRAMES = [[[(g, ord(c) - 48) for g, c in zip(gs, cs)] for gs, cs in zip(fr['glyphs'], fr['colors'])] for fr in DATA['frames']]
BG, BORDER, KEY, DOTS, TEXT = DATA['ground'], PALETTE[2], PALETTE[9], PALETTE[4], PALETTE[30]
RADIUS = {'·': 0.17, '•': 0.29, '●': 0.41}  # dot radius per glyph, in cells
CELL = 4  # px per cell
CH, CW_ = len(FRAMES[0]), len(FRAMES[0][0])

TYPE_LINE, TYPE_START = 0.25, 0.4  # s to type one info line, s before the first

FONT, LINE, CW = 14, 18, 8.4  # px; CW is an estimate of monospace advance (0.6em)
PAD, GAP, COLS = 24, 28, 54   # COLS = width of the info column in characters
ART_W, HEIGHT = CW_ * CELL, round(CH * CELL)
TX = ART_W + GAP
WIDTH = round(TX + COLS * CW + PAD)


def span(cls, s):
    return f'<tspan class="{cls}">{escape(s)}</tspan>'


def info_lines():
    yield span('key', USER) + span('dots', '@') + span('val', HOST) + span('dots', ' ' + '-' * (COLS - len(USER + HOST) - 2))
    for item in INFO:
        if item == '':
            yield ''
        elif isinstance(item, str):
            title = item[2:]
            yield span('val', '- ' + title) + span('dots', ' ' + '-' * (COLS - len(title) - 3))
        else:
            k, v = item
            key = span('dots', '.').join(span('key', part) for part in k.split('.'))
            dots = COLS - len(k) - len(v) - 5
            assert dots >= 3, f'{k}: {v!r} is too long for {COLS} columns'
            yield span('dots', '. ') + key + span('dots', ': ' + '.' * dots + ' ') + span('val', v)


def path(cls, pts):
    """A zero-length round-capped stroke per point: each m..h0 is a dot."""
    d, px, py = [], 0, 0
    for x, y in pts:  # relative moves keep the path data short
        d.append(f'm{x - px} {y - py}h0' if d else f'M{x} {y}h0')
        px, py = x, y
    return f'<path class="{cls}" d="{"".join(d)}"/>'


def dots(cells):
    """One path per (glyph, colour)."""
    groups = {}
    for (y, x), (g, ci) in sorted(cells.items()):
        if g != ' ':
            groups.setdefault((g, ci), []).append((x, y))
    return '\n'.join(path(f'g{"·•●".index(g)} c{ci}', pts) for (g, ci), pts in sorted(groups.items()))


def flipbook(cls, seq):
    """CSS that shows the frame group .{cls}{k} only in the slots of seq that hold k."""
    slot = 100 / len(seq)
    css = [f'.{cls} {{visibility: hidden; animation: {len(seq) / FPS:g}s step-end infinite;}}']
    for k in sorted(set(seq)):
        stops = [f'{s * slot:.3f}%{{visibility:visible}} {(s + 1) * slot:.3f}%{{visibility:hidden}}' for s, v in enumerate(seq) if v == k]
        css.append(f'.{cls}{k} {{animation-name: {cls}{k};}} @keyframes {cls}{k} {{0%{{visibility:hidden}} {" ".join(stops)}}}')
    return css


def svg():
    grids = [{(y, x): cell for y, row in enumerate(fr) for x, cell in enumerate(row) if cell[0] != ' '} for fr in FRAMES]
    static = {k: v for k, v in grids[0].items() if all(g.get(k) == v for g in grids)}  # drawn once, under every frame
    n = len(FRAMES)
    seq = list(range(n)) + list(range(n - 2, 0, -1))  # forward then back: the loop has no seam

    css = [
        'text, tspan {white-space: pre;}',
        f'.key {{fill: {KEY};}} .dots {{fill: {DOTS};}} .val {{fill: {TEXT};}}',
        '.art {fill: none; stroke-linecap: round;}',
        *(f'.g{i} {{stroke-width: {r * 2:g};}}' for i, r in enumerate(RADIUS.values())),
        *(f'.c{i} {{stroke: {c};}}' for i, c in enumerate(PALETTE)),
        *flipbook('f', seq),
        '.f0 {visibility: visible;}',
        # typing: a background-coloured cover, cursor on its edge, slides off each line a character at a time
        f'.ty {{animation: type {TYPE_LINE:g}s steps({COLS}) both;}} @keyframes type {{to {{transform: translateX({COLS}ch);}}}}',
        f'.cu {{fill: {KEY}; visibility: hidden; animation: cursor {TYPE_LINE:g}s;}} @keyframes cursor {{from, to {{visibility: visible;}}}}',
        '.sw {animation: pop 0s both;} @keyframes pop {from {visibility: hidden;}}',
        # last, so it overrides the rules above
        '@media (prefers-reduced-motion: reduce) {.art .f, .sw {animation: none;} .ty {display: none;}}',
    ]

    swatches = [PALETTE[ci] for ci in sorted(ci for ci, _ in Counter(ci for _, ci in grids[0].values()).most_common(8))]
    lines = list(info_lines())
    top = round((HEIGHT - (len(lines) + 1) * LINE - 14) / 2) + 14  # centre the info block and swatches
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f"font-size=\"{FONT}\" font-family=\"ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace\">",
        '<style>' + '\n'.join(css) + '</style>',
        '<defs>',
        f'<clipPath id="card"><rect width="{WIDTH}" height="{HEIGHT}" rx="12"/></clipPath>',
        # the art's right edge melts into the card instead of ending in a hard line
        '<linearGradient id="fade"><stop offset="0.8" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>',
        f'<mask id="art"><rect width="{ART_W:g}" height="{HEIGHT}" fill="url(#fade)"/></mask>',
        '</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="{BG}"/>',
        '<g clip-path="url(#card)"><g mask="url(#art)">',
        f'<g class="art" transform="scale({CELL}) translate(.5 .5)">',
        dots(static),
    ]
    for k, g in enumerate(grids):
        out += [f'<g class="f f{k}">', dots({c: v for c, v in g.items() if c not in static}), '</g>']
    out += ['</g></g></g>', '<text>']
    out += [f'<tspan x="{TX:.1f}" y="{top + y * LINE}">{line}</tspan>' for y, line in enumerate(lines) if line]
    out.append('</text>')
    delay = TYPE_START
    for y, line in enumerate(lines):
        if line:
            style = f'style="animation-delay: {delay:.2f}s"'
            out += [f'<g class="ty" {style}>',
                    f'<rect x="{TX:.1f}" y="{top + y * LINE - 13}" width="{WIDTH - TX:.1f}" height="{LINE}" fill="{BG}"/>',
                    f'<rect class="cu" {style} x="{TX:.1f}" y="{top + y * LINE - 12}" width=".6em" height="16"/>', '</g>']
        delay += TYPE_LINE if line else TYPE_LINE / 2  # a spacer is a short pause
    py = top + len(lines) * LINE + 2
    out.append(f'<g class="sw" style="animation-delay: {delay:.2f}s">')
    out += [f'<rect x="{TX + i * 30:.1f}" y="{py}" width="22" height="14" rx="2" fill="{c}"/>' for i, c in enumerate(swatches)]
    out.append('</g>')
    out += [f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" fill="none" stroke="{BORDER}"/>', '</svg>', '']
    return '\n'.join(out)


if __name__ == '__main__':
    assert all(len(fr) == CH and all(len(r) == CW_ for r in fr) for fr in FRAMES), 'frames differ in size'
    assert all(0 <= ci < len(PALETTE) for fr in FRAMES for row in fr for _, ci in row), 'colour outside the palette'
    assert {g for fr in FRAMES for row in fr for g, _ in row} <= set(RADIUS) | {' '}, 'unknown glyph in aurora-fjord.json'
    with open('card.svg', 'w', encoding='utf-8', newline='\n') as f:
        f.write(svg())
