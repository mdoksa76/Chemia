# -*- coding: utf-8 -*-
"""
pse/card.py — kartica jednog elementa.

  atom_svg(el, ...)    samo Bohrov model atoma (jezgra + ljuske), kao SVG slika
  card_data(el)        strukturirani podaci (sekcije ključ/vrijednost) za
                       uređivo umetanje (insert.py ih slaže native po app)
  render_card(el, ...) cijela kartica kao SVG slika: atom + podaci + izotopi

Atomski model portan iz web verzije: deterministično pakiranje nukleona
(LCG PRNG — isti prikaz za isti element), protoni crveni, neutroni sivi.
"""

import math
from core import elements as E
from core.svgkit import SvgDoc
from core.i18n import t, element_name, element_name_other, category_name, state_name

PROTON = '#E24B4A'
NEUTRON = '#888780'


# ---------------------------------------------------------------------------
#  Atomski model
# ---------------------------------------------------------------------------
def _draw_atom(doc, cx, cy, el, box=300):
    """Nacrtaj Bohrov model u doc, centriran na (cx, cy)."""
    shells = el.shells
    maxR = box * 0.44
    inner = box * 0.085
    nsh = len(shells)
    radii = [inner + (i * (maxR - inner)) / max(nsh - 1, 1) for i in range(nsh)]

    # ljuske + elektroni
    for i, n in enumerate(shells):
        r = radii[i]
        color = E.SHELL_COLORS[i] if i < len(E.SHELL_COLORS) else '#888'
        doc.circle(cx, cy, r, fill='none', stroke=color, sw=0.8, opacity=0.6)
        eR = 4 if i < 2 else (3.5 if i < 4 else 3)
        for e in range(n):
            ang = 2 * math.pi * e / n - math.pi / 2
            ex = cx + r * math.cos(ang)
            ey = cy + r * math.sin(ang)
            doc.circle(ex, ey, eR, fill=color, opacity=0.9)

    # jezgra
    Z = el.z
    A = round(E.parse_mass(el.mass))
    N = max(A - Z, 0)
    nucR = max(14, 5 + Z * 1.6) if Z <= 16 else 20
    doc.circle(cx, cy, nucR, fill='#0a0a14', stroke='#333344', sw=1)

    # LCG PRNG — deterministično
    seed = (Z * 1664525 + N * 1013904223 + 42) & 0xFFFFFFFF or 1

    def rnd():
        nonlocal seed
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        return seed / 0x100000000

    if Z <= 16:
        total = Z + N
        nR = 3.2
        pos = []
        for i in range(total):
            r = (nucR - nR - 2) * math.sqrt((i + 0.5) / total)
            a = i * 2.399963  # zlatni kut
            pos.append((r * math.cos(a), r * math.sin(a)))
        for i in range(len(pos) - 1, 0, -1):
            j = int(rnd() * (i + 1))
            pos[i], pos[j] = pos[j], pos[i]
        types = [PROTON] * Z + [NEUTRON] * N
        for i in range(len(types) - 1, 0, -1):
            j = int(rnd() * (i + 1))
            types[i], types[j] = types[j], types[i]
        for (px, py), col in zip(pos, types):
            doc.circle(cx + px, cy + py, nR, fill=col, opacity=0.92)
    else:
        sym_count = 9
        symR = nucR - 4.5
        pos = []
        for i in range(sym_count):
            r = symR * math.sqrt((i + 0.5) / sym_count)
            a = i * 2.399963
            pos.append((r * math.cos(a), r * math.sin(a)))
        for i in range(len(pos) - 1, 0, -1):
            j = int(rnd() * (i + 1))
            pos[i], pos[j] = pos[j], pos[i]
        ratio = Z / (Z + max(N, 1))
        for i, (px, py) in enumerate(pos):
            col = PROTON if rnd() < ratio else NEUTRON
            doc.circle(cx + px, cy + py, 3.5, fill=col, opacity=0.95 - i * 0.04)


def atom_svg(el, theme_name=None, box=300):
    """Samo atomski model kao samostalni SVG (za umetanje kao slika)."""
    doc = SvgDoc(box, box, theme_name)
    _draw_atom(doc, box / 2, box / 2, el, box)
    return doc.tostring()


# ---------------------------------------------------------------------------
#  Podaci kartice (za uređivo umetanje)
# ---------------------------------------------------------------------------
def card_data(el):
    """
    Sekcije kao [(section_id, [(label, value), ...]), ...]. section_id je
    stabilan engleski ključ (za lookup); labeli i vrijednosti su već lokalizirani
    preko t(). Izvor i za SVG tablicu i za native (uređivo) umetanje.
    """
    A = round(E.parse_mass(el.mass))
    N = A - el.z
    grp = str(el.group) if el.group is not None else t('f-block')
    basic = [
        (t('Atomic number'), str(el.z)),
        (t('Atomic mass'), '%s u' % el.mass),
        (t('Period / group'), '%d / %s' % (el.period, grp)),
        (t('State'), state_name(el.state)),
        (t('Electronegativity'), ('%.2f' % el.eneg) if el.eneg is not None else '—'),
    ]
    structure = [
        (t('Protons'), str(el.z)),
        (t('Neutrons (most common)'), str(N) if N >= 0 else '—'),
        (t('Electrons'), str(el.z)),
        (t('Atomic radius'), ('%d pm' % el.radius) if el.radius else '—'),
        (t('Oxidation states'), el.oxid),
    ]
    config = [
        (t('Configuration'), el.config),
        (t('Shells'), ' · '.join('%s=%d' % (E.SHELL_NAMES[i], n)
                                 for i, n in enumerate(el.shells))),
    ]
    isotopes = [(iso, pct) for iso, pct, _major in el.isotopes]
    return [
        ('BASIC', basic),
        ('ATOM STRUCTURE', structure),
        ('ELECTRON CONFIGURATION', config),
        ('ISOTOPES', isotopes),
    ]


# ---------------------------------------------------------------------------
#  Cijela kartica kao slika
# ---------------------------------------------------------------------------
def render_card(el, theme_name=None):
    """Kartica: zaglavlje + atomski model lijevo + podaci desno, kao SVG."""
    box = 300
    info_w = 320
    W = box + info_w + 20
    H = 420
    doc = SvgDoc(W, H, theme_name)
    th = doc.th
    cat = E.CATEGORY_COLORS.get(el.category, '#888')
    cat_name = category_name(el.category)
    other = element_name_other(el)

    # atom lijevo, centriran vertikalno
    _draw_atom(doc, box / 2, H / 2, el, box)

    # zaglavlje desno
    ix = box + 16
    doc.text(ix, 46, el.sym, size=42, weight='700', fill=cat)
    doc.text(ix + 70, 34, element_name(el), size=16, weight='500', fill=th['text'])
    sub = ('%s · %s' % (other, cat_name)) if other else cat_name
    doc.text(ix + 70, 52, sub, size=9, fill=th['muted'])

    # podaci: dvije glavne sekcije u tablicu, pa konfiguracija i izotopi tekstom
    sections = dict(card_data(el))
    y = 74
    w, h = doc.table(ix, y, sections['BASIC'], col1=150, col2=138, row_h=18,
                     size=10, header=t('BASIC'))
    y += h + 10
    w, h = doc.table(ix, y, sections['ATOM STRUCTURE'], col1=150, col2=138,
                     row_h=18, size=10, header=t('ATOM STRUCTURE'))
    y += h + 12

    doc.text(ix, y, t('ELECTRON CONFIGURATION'), size=11, weight='700', fill=th['accent'])
    y += 16
    doc.rect(ix, y - 12, info_w - 8, 20, fill=th['surface'], stroke=th['line'],
             sw=0.6, rx=4)
    doc.text(ix + 6, y + 2, el.config, size=10, fill=th['text'])
    y += 22

    doc.text(ix, y, t('ISOTOPES'), size=11, weight='700', fill=th['accent'])
    y += 15
    iso_txt = '   '.join('%s %s' % (iso, pct) for iso, pct in sections['ISOTOPES'])
    doc.text(ix, y, iso_txt, size=9, fill=th['muted'])

    return doc.tostring()


if __name__ == "__main__":
    import os
    outdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_preview'))
    os.makedirs(outdir, exist_ok=True)
    for z in (8, 26, 1, 92):
        el = E.by_z(z)
        with open(os.path.join(outdir, 'kartica_%s.svg' % el.sym), 'w',
                  encoding='utf-8') as f:
            f.write(render_card(el, 'light'))
        with open(os.path.join(outdir, 'atom_%s.svg' % el.sym), 'w',
                  encoding='utf-8') as f:
            f.write(atom_svg(el, 'light'))
    # provjere (default engleski)
    d = card_data(E.by_z(8))
    assert d[0][0] == 'BASIC'
    assert ('Protons', '8') in dict(d)['ATOM STRUCTURE']
    assert render_card(E.by_z(26), 'light').startswith('<svg')
    # hrvatski prijevod
    from core.i18n import set_locale
    set_locale('hr')
    dh = dict(card_data(E.by_z(8)))
    assert ('Protoni', '8') in dh['ATOM STRUCTURE']
    set_locale('en')
    print("card.py OK — kartice i atomski modeli (en+hr) u", outdir)
