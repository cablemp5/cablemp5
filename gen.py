"""Builds card.svg: a neofetch-style card with a halftone ASCII sunset.

Art: one frame (t=28) of "cloud sea" from https://ascii.rest (MIT, github.com/bas3line/ascii).
cloud-sea.txt holds the 200x100 frame of dot glyphs, then `---`, then a same-shape grid of
palette indices (a = PALETTE[0] ... y = PALETTE[24]). Each glyph is drawn as a dot of
its size so the art does not depend on the viewer's fonts.

Edit INFO or CROP below, then run `python gen.py`.
"""
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

# cloud sea's own palette, so the card's text and swatches come from the art
PALETTE = [
    '#0e0e0f', '#161617', '#1f1f20', '#2a2a2b', '#353536', '#404041', '#545456', '#6c6c6e', '#8a8a8c',
    '#a39a94', '#2c211c', '#43302a', '#5e3c2a', '#7c4826', '#9c521f',
    '#c2601c', '#dc6f1e', '#f38020', '#f6922e', '#faae40', '#fbbd5c', '#fccb7c', '#fdda9e', '#feeac4', '#fff6e6',
]
BG, BORDER, KEY, DOTS, TEXT = PALETTE[0], PALETTE[3], PALETTE[17], PALETTE[5], PALETTE[24]
RADIUS = {'·': 0.17, '•': 0.29, '●': 0.41}  # dot radius per glyph, in cells
CROP = (108, 12, 88, 88)  # col, row, width, height of the frame shown: the sun sits in the middle
CELL = 4.6  # px per cell

with open('cloud-sea.txt', encoding='utf-8') as f:
    GLYPHS, COLORS = (part.split('\n') for part in f.read().rstrip('\n').split('\n---\n'))

FONT, LINE, CW = 14, 18, 8.4  # px; CW is an estimate of monospace advance (0.6em)
PAD, GAP, COLS = 24, 28, 54   # COLS = width of the info column in characters
CX, CY, CW_, CH = CROP
ART_W, HEIGHT = CW_ * CELL, round(CH * CELL)
TX = ART_W + GAP
WIDTH = round(TX + COLS * CW + PAD)


def cells():
    for r in range(CY, CY + CH):
        for c in range(CX, CX + CW_):
            g = GLYPHS[r][c]
            if g != ' ':
                yield c - CX, r - CY, g, ord(COLORS[r][c]) - ord('a')


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


def svg():
    # one path of zero-length round-capped strokes per (glyph, colour): each M..h0 is a dot
    paths = {}
    for x, y, g, ci in cells():
        paths.setdefault((g, ci), []).append(f'M{x} {y}h0')
    # the 8 colours the art uses most, in the palette's own order: greys, then the oranges
    swatches = [PALETTE[ci] for ci in sorted(ci for ci, _ in Counter(ci for *_, ci in cells()).most_common(8))]
    lines = list(info_lines())
    top = round((HEIGHT - (len(lines) + 1) * LINE - 14) / 2) + 14  # centre the info block and swatches
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f"font-size=\"{FONT}\" font-family=\"ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace\">",
        f'<style>text, tspan {{white-space: pre;}} .key {{fill: {KEY};}} .dots {{fill: {DOTS};}} .val {{fill: {TEXT};}}</style>',
        '<defs>',
        f'<clipPath id="card"><rect width="{WIDTH}" height="{HEIGHT}" rx="12"/></clipPath>',
        # the art's right edge melts into the card instead of ending in a hard line
        '<linearGradient id="fade"><stop offset="0.8" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>',
        f'<mask id="art"><rect width="{ART_W:g}" height="{HEIGHT}" fill="url(#fade)"/></mask>',
        '</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="{BG}"/>',
        f'<g clip-path="url(#card)"><g mask="url(#art)">',
        f'<g transform="scale({CELL}) translate(.5 .5)" fill="none" stroke-linecap="round">',
    ]
    out += [f'<path stroke="{PALETTE[ci]}" stroke-width="{RADIUS[g] * 2:g}" d="{"".join(d)}"/>' for (g, ci), d in sorted(paths.items())]
    out += ['</g></g></g>', '<text>']
    out += [f'<tspan x="{TX:.1f}" y="{top + y * LINE}">{line}</tspan>' for y, line in enumerate(lines) if line]
    out.append('</text>')
    py = top + len(lines) * LINE + 2
    out += [f'<rect x="{TX + i * 30:.1f}" y="{py}" width="22" height="14" rx="2" fill="{c}"/>' for i, c in enumerate(swatches)]
    out += [f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" fill="none" stroke="{BORDER}"/>', '</svg>', '']
    return '\n'.join(out)


if __name__ == '__main__':
    assert len(GLYPHS) == len(COLORS) and all(len(g) == len(c) for g, c in zip(GLYPHS, COLORS)), 'cloud-sea.txt shape mismatch'
    assert CX + CW_ <= len(GLYPHS[0]) and CY + CH <= len(GLYPHS), 'CROP runs off the frame'
    assert set(''.join(GLYPHS)) <= set(RADIUS) | {' '}, 'unknown glyph in cloud-sea.txt'
    with open('card.svg', 'w', encoding='utf-8', newline='\n') as f:
        f.write(svg())
