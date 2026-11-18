# -*- coding: utf-8 -*-
"""
molviz/card.py — "molekula + podatkovni panel" (pandan pse/card.py).

Slaže render molekule i podatkovni panel u jedan SVG, istim jezikom kao kartica
elementa (isti mono font, iste veličine, ista tablica). Legenda su mini-kugle u
CPK boji s istim gradijentom kao atomi, pa panel vizualno pripada molekuli.

  molecule_card(mol, name, formula=None, props=None, theme='light',
                details=('Mr','M','m','exact','fractions'), mol_px=280)

details bira veličine; 'exact' se prikaže samo ako props ima exact_mass.
Bez panela se koristi render.render_molecule izravno (samo slika).
"""

import re
from molviz.render import render_molecule
from molviz import mass
from core import elements as E
from core.svgkit import SvgDoc
from core.i18n import t

# veličine teksta (malo manje od prototipa)
_NAME = 16
_FORMULA = 13
_H = 10        # naslov sekcije
_ROW = 10      # redak tablice
_ROWH = 18


def hill(counts):
    """Hillov zapis formule iz {simbol: broj}."""
    out = []
    if 'C' in counts:
        out.append('C')
        if 'H' in counts:
            out.append('H')
    for k in sorted(s for s in counts if s not in out):
        out.append(k)
    return ''.join('%s%s' % (k, counts[k] if counts[k] != 1 else '') for k in out)


def _counts(mol):
    c = {}
    for a in mol['atoms']:
        c[a['sym']] = c.get(a['sym'], 0) + 1
    return c


def molecule_card(mol, name, formula=None, props=None, theme='light',
                  details=('Mr', 'M', 'm', 'exact', 'fractions'),
                  style='ball', rot_x=0.0, rot_y=0.0, mol_px=280):
    counts = _counts(mol)
    res = mass.from_symbols([a['sym'] for a in mol['atoms']])
    formula = formula or (props or {}).get('formula') or hill(counts)
    props = props or {}

    panel_w = 280
    W, H = mol_px + 18 + panel_w, max(mol_px, 272)
    doc = SvgDoc(W, H, theme)
    th = doc.th

    # molekula kao ugniježđeni SVG (ima vlastitu sivu podlogu)
    msvg = render_molecule(mol, style, theme, size=mol_px, rot_x=rot_x, rot_y=rot_y)
    inner = re.sub(r'^<svg[^>]*>', '', msvg)[:-6]
    doc.raw('<svg x="0" y="%g" width="%d" height="%d" viewBox="%g %g %d %d">%s</svg>'
            % ((H - mol_px) / 2, mol_px, mol_px, -mol_px / 2, -mol_px / 2,
               mol_px, mol_px, inner))

    ix = mol_px + 16
    doc.text(ix, 34, name, size=_NAME, weight='700', fill=th['text'])
    doc.formula(ix, 54, formula, size=_FORMULA, fill=th['accent'], weight='700')

    # tablica veličina
    rows = []
    if 'Mr' in details:
        rows.append((t('Mr (rel. molecular mass)'), '%.3f' % res['Mr']))
    if 'M' in details:
        rows.append((t('M (molar mass)'), '%.2f g/mol' % res['M']))
    if 'm' in details:
        rows.append((t('m (molecule mass)'), '%.3e kg' % res['m_kg']))
    if 'exact' in details and props.get('exact_mass'):
        rows.append((t('Exact mass'), '%.4f' % props['exact_mass']))
    y = 68
    if rows:
        _w, h = doc.table(ix, y, rows, col1=140, col2=124, row_h=_ROWH,
                          size=_ROW, header=t('QUANTITIES'))
        y += h + 10

    # sastav: mini-kugle u CPK boji (isti gradijent kao atomi) + w%, pa CPK traka
    if 'fractions' in details:
        doc.text(ix, y, t('COMPOSITION (mass fractions)'), size=_H, weight='700',
                 fill=th['accent'])
        y += 18
        for sym, w in res['fractions']:
            col = E.cpk_color(sym)
            gid = doc.radial_gradient('leg_%s' % sym, col)
            doc.circle(ix + 6, y - 3, 6, fill='url(#%s)' % gid,
                       stroke=th['line'] if sym == 'H' else 'none', sw=0.8)
            doc.text(ix + 18, y, sym, size=_ROW, weight='600', fill=th['text'])
            doc.text(ix + panel_w - 8, y, '%.2f %%' % w, size=_ROW,
                     fill=th['muted'], anchor='end')
            y += 17
        bx, bw, bh = ix, panel_w - 8, 11
        cx = bx
        for sym, w in res['fractions']:
            seg = bw * w / 100.0
            doc.rect(cx, y, seg, bh, fill=E.cpk_color(sym),
                     stroke=th['line'] if sym == 'H' else 'none', sw=0.6)
            cx += seg
        doc.rect(bx, y, bw, bh, fill='none', stroke=th['line'], sw=0.8, rx=3)

    return doc.tostring()


if __name__ == "__main__":
    import os
    from molviz.render import TEST
    outdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_preview'))
    os.makedirs(outdir, exist_ok=True)
    svg = molecule_card(TEST['voda'], 'Voda', formula='H2O', theme='light',
                        props={'exact_mass': 18.0106})
    with open(os.path.join(outdir, 'card_voda.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)
    assert svg.startswith('<svg')
    # bez panela redaka
    svg2 = molecule_card(TEST['metan'], 'Metan', formula='CH4', theme='light',
                         details=('Mr', 'M'))
    assert 'COMPOSITION' not in svg2
    print("card.py OK — molecule_card u", outdir)
