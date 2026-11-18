# -*- coding: utf-8 -*-
"""
pse/grid.py — periodni sustav kao SVG.

Tri načina umetanja:
  render_table(theme)   cijeli periodni sustav (18×7 + lantanoidi/aktinoidi)
  render_group(g, ...)  jedna grupa (stupac 1..18)
  render_period(p, ...) jedna perioda (red 1..7)

Sve bez pozadinskog grida; podloga ovisi o temi (svijetla=default, prozirna,
tamna). Boje polja = kategorija elementa (konzistentno s karticom i legendom).
"""

from core import elements as E
from core.svgkit import SvgDoc, theme as _theme, esc, MONO
from core.i18n import t, group_name

CELL = 46          # stranica polja
GAP = 3            # razmak
PAD = 10           # vanjski rub
BLOCK_GAP = 16     # razmak glavne mreže od lantanoid/aktinoid bloka


def _mix(hex_color, bg_hex, frac):
    """Pomiješaj hex_color preko bg_hex: frac*boja + (1-frac)*podloga."""
    def ch(h, i):
        return int(h.lstrip('#')[i:i + 2], 16)
    r = round(ch(hex_color, 0) * frac + ch(bg_hex, 0) * (1 - frac))
    g = round(ch(hex_color, 2) * frac + ch(bg_hex, 2) * (1 - frac))
    b = round(ch(hex_color, 4) * frac + ch(bg_hex, 4) * (1 - frac))
    return "#%02x%02x%02x" % (r, g, b)


def _darken(hex_color, frac=0.55):
    """Zatamni hex za čitljiv simbol na svijetlom polju."""
    return _mix(hex_color, '#000000', 1 - frac)


def _cell(doc, x, y, el):
    """Nacrtaj jedno polje elementa u doc na (x, y)."""
    th = doc.th
    cat = E.CATEGORY_COLORS.get(el.category, '#888888')
    surface = th['surface'] if th['bg'] is not None else '#ffffff'
    is_dark = th['bg'] == '#0a0a0f'
    base = th['surface'] if is_dark else '#ffffff'
    fill = _mix(cat, base, 0.30 if not is_dark else 0.28)
    border = _mix(cat, base, 0.60)
    sym_color = cat if is_dark else _darken(cat)

    doc.rect(x, y, CELL, CELL, fill=fill, stroke=border, sw=1, rx=4)
    doc.text(x + 4, y + 11, str(el.z), size=8, fill=th['muted'])
    doc.text(x + CELL / 2, y + CELL * 0.62, el.sym, size=17, weight='700',
             fill=sym_color, anchor='middle')
    doc.text(x + CELL / 2, y + CELL - 5, el.mass, size=6.5, fill=th['muted'],
             anchor='middle')


def _placeholder(doc, x, y, label):
    th = doc.th
    doc.rect(x, y, CELL, CELL, fill='none', stroke=th['line'], sw=1, rx=4)
    doc.text(x + CELL / 2, y + CELL / 2 + 3, label, size=7, fill=th['muted'],
             anchor='middle')


def _pos(col, row):
    """Gornji-lijevi kut polja za stupac (0-based) i red (0-based)."""
    return (PAD + col * (CELL + GAP), PAD + row * (CELL + GAP))


# ---------------------------------------------------------------------------
#  Cijeli periodni sustav
# ---------------------------------------------------------------------------
def render_table(theme_name=None, title=None, title_align='left', title_color=None):
    main_w = PAD * 2 + 18 * CELL + 17 * GAP
    main_h = PAD + 7 * (CELL + GAP)
    la_y0 = main_h + BLOCK_GAP
    total_h = la_y0 + 2 * (CELL + GAP) + PAD
    title_h = 26 if title else 0

    doc = SvgDoc(main_w, total_h + title_h, theme_name)
    if title:
        col = title_color or doc.th['accent']
        if title_align == 'center':
            tx, anc = main_w / 2, 'middle'
        elif title_align == 'right':
            tx, anc = main_w - PAD, 'end'
        else:
            tx, anc = PAD, 'start'
        doc.text(tx, 18, title, size=14, weight='700', fill=col, anchor=anc)

    off = title_h

    # glavna mreža: elementi s grupom na (grupa, perioda)
    for el in E.ELEMENTS:
        if el.group is None:
            continue
        x, y = _pos(el.group - 1, el.period - 1)
        _cell(doc, x, y + off, el)

    # (bez placeholdera "57–71"/"89–103" — f-blokovi ispod su dovoljno jasni)

    # lantanoidi (57–71) i aktinoidi (89–103) — dva reda ispod, uvučeno za 2 polja
    lan = E.lanthanides()
    act = E.actinides()
    for i, el in enumerate(lan):
        x = PAD + (i + 2) * (CELL + GAP)
        _cell(doc, x, la_y0 + off, el)
    for i, el in enumerate(act):
        x = PAD + (i + 2) * (CELL + GAP)
        _cell(doc, x, la_y0 + (CELL + GAP) + off, el)

    return doc.tostring()


# ---------------------------------------------------------------------------
#  Jedna grupa (stupac)
# ---------------------------------------------------------------------------
def render_group(g, theme_name=None, title=None):
    g = int(g)
    els = E.group(g)
    if title is None:
        title = t("Group %d") % g
    gname = group_name(g)            # naziv po svojstvima (ili None)
    lm = 24 if gname else 0          # lijevi prostor za rotirani naziv
    title_h = 24
    cells_h = len(els) * (CELL + GAP)
    w = PAD * 2 + CELL + lm
    h = PAD + title_h + cells_h
    doc = SvgDoc(w, h, theme_name)
    cx = PAD + lm
    doc.text(cx, 17, title, size=12, weight='700', fill=doc.th['accent'])
    for i, el in enumerate(els):
        _cell(doc, cx, PAD + title_h + i * (CELL + GAP), el)
    if gname:
        # naziv rotiran 90° uz stupac (čita se odozdo prema gore)
        tx = PAD + 9
        ty = PAD + title_h + cells_h / 2
        doc.raw('<text x="%.1f" y="%.1f" transform="rotate(-90 %.1f %.1f)" '
                'font-size="12" font-family="%s" font-weight="700" fill="%s" '
                'text-anchor="middle">%s</text>'
                % (tx, ty, tx, ty, MONO, doc.th['accent'], esc(gname)))
    return doc.tostring()


# ---------------------------------------------------------------------------
#  Jedna perioda (red)
# ---------------------------------------------------------------------------
def render_period(p, theme_name=None, title=None):
    p = int(p)
    main = [e for e in E.period(p) if e.group is not None]
    fblock = [e for e in E.period(p) if e.group is None]
    if title is None:
        title = t("Period %d") % p

    cols = 18
    title_h = 24
    w = PAD * 2 + cols * CELL + (cols - 1) * GAP
    rows = 1 + (1 if fblock else 0)
    h = PAD + title_h + rows * (CELL + GAP) + (BLOCK_GAP if fblock else 0)
    doc = SvgDoc(w, h, theme_name)
    doc.text(PAD, 17, title, size=12, weight='700', fill=doc.th['accent'])

    y0 = PAD + title_h
    for el in main:
        x = PAD + (el.group - 1) * (CELL + GAP)
        _cell(doc, x, y0, el)
    if fblock:
        y1 = y0 + (CELL + GAP) + BLOCK_GAP
        for i, el in enumerate(fblock):
            x = PAD + i * (CELL + GAP)
            _cell(doc, x, y1, el)
    return doc.tostring()


if __name__ == "__main__":
    import os
    outdir = os.path.join(os.path.dirname(__file__), '..', '_preview')
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    cases = {
        'pse_light.svg': render_table('light', title='Periodni sustav elemenata'),
        'pse_transparent.svg': render_table('transparent'),
        'pse_dark.svg': render_table('dark'),
        'grupa_1.svg': render_group(1, 'light'),
        'perioda_2.svg': render_period(2, 'light'),
        'perioda_6.svg': render_period(6, 'light'),
    }
    for name, svg in cases.items():
        with open(os.path.join(outdir, name), 'w', encoding='utf-8') as f:
            f.write(svg)
        assert svg.startswith('<svg') and svg.endswith('</svg>')
    # provjere sadržaja
    full = render_table('light')
    for sym in ('H', 'Og', 'La', 'U', 'Fe'):
        assert '>%s<' % sym in full, sym
    assert '57–71' not in full and '89–103' not in full  # placeholderi maknuti
    assert render_group(18, 'light').count('<rect') >= 6  # plemeniti plinovi
    print("grid.py OK — PSE, grupa i perioda generirani u", outdir)
