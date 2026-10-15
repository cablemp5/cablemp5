"""Builds dark_mode.svg and light_mode.svg: a neofetch-style card with ASCII mountains.

Art: one frame (t=12, 44x20) of "ruled mountains" from https://ascii.rest (MIT, github.com/bas3line/ascii).
mountains.txt holds the frame, then `---`, then a same-shape mask of which ruled line
(0 back .. 5 front) owns each cell; the mask picks each character's colour.

Edit INFO below, then run `python gen.py`.
"""
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

THEMES = {  # depth: ruled lines back to front, also the swatch row
    'dark': dict(bg='#0d1117', border='#30363d', text='#e6edf3', key='#f08a3c', dots='#3d444d',
                 depth=['#34557f', '#41699a', '#5180b8', '#6797ce', '#89b2e1', '#b3d1f3']),
    'light': dict(bg='#ffffff', border='#d0d7de', text='#1f2328', key='#b4501a', dots='#d0d7de',
                  depth=['#9fb8d8', '#7f9fcc', '#6087bd', '#4270ab', '#2a5891', '#183f73']),
}

with open('mountains.txt', encoding='utf-8') as f:
    ART, DEPTH = (part.split('\n') for part in f.read().rstrip('\n').split('\n---\n'))
H, W = len(ART), len(ART[0])

FONT, LINE, CW = 14, 18, 8.4  # px; CW is an estimate of monospace advance (0.6em)
PAD, GAP, COLS = 24, 32, 54   # COLS = width of the info column in characters
TX = PAD + W * CW + GAP
WIDTH, HEIGHT = round(TX + COLS * CW + PAD), PAD * 2 + H * LINE - 4


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


def art_row(chars, depth):
    out, run, cls = [], '', None
    for ch, d in zip(chars, depth):  # merge same-depth neighbours into one tspan
        c = 'sky' if d == ' ' else f'd{d}'
        if c != cls and run:
            out.append(span(cls, run))
            run = ''
        run, cls = run + ch, c
    return ''.join(out) + span(cls, run)


def svg(t):
    css = [f'.{c} {{fill: {t[c]};}}' for c in ('key', 'dots')] + [f'.val {{fill: {t["text"]};}}']
    css += [f'.d{i} {{fill: {c};}}' for i, c in enumerate(t['depth'])]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-size="{FONT}" '
        "font-family=\"ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace\">",
        '<style>text, tspan {white-space: pre;} ' + ' '.join(css) + '</style>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        '<text>',
    ]
    for y, (chars, depth) in enumerate(zip(ART, DEPTH)):
        out.append(f'<tspan x="{PAD}" y="{PAD + 10 + y * LINE}">{art_row(chars, depth)}</tspan>')
    lines = list(info_lines())
    for y, line in enumerate(lines):
        if line:
            out.append(f'<tspan x="{TX:.1f}" y="{PAD + 10 + y * LINE}">{line}</tspan>')
    out.append('</text>')
    py = PAD + 10 + (len(lines) + 1) * LINE - FONT + 2  # swatch row under the info: the art's depth colours
    out += [f'<rect class="d{i}" x="{TX + i * 30:.1f}" y="{py}" width="22" height="14" rx="2"/>' for i in range(len(t['depth']))]
    out += ['</svg>', '']
    return '\n'.join(out)


if __name__ == '__main__':
    assert len(DEPTH) == H and all(len(a) == len(d) == W for a, d in zip(ART, DEPTH)), 'mountains.txt mask/art shape mismatch'
    assert len(list(info_lines())) + 2 <= H, 'info column is taller than the art'
    for name, theme in THEMES.items():
        with open(f'{name}_mode.svg', 'w', encoding='utf-8', newline='\n') as f:
            f.write(svg(theme))
