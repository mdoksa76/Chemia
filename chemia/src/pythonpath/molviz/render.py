# -*- coding: utf-8 -*-
"""
molviz/render.py — prikaz molekule kao SVG (port MolViz jezgre).

Radi na strukturi molekule neovisnoj o izvoru:
    mol = {
        'atoms': [{'sym','x','y','z'}, ...],   # koordinate u ångströmima
        'bonds': [(i, j, order), ...],         # indeksi atoma + red veze
    }
pubchem.py pretvara PubChem JSON u ovu strukturu; ovdje je samo geometrija.

Tri stila:
    ball    ball & stick (atomi + sive veze, dvostruke udvojene)
    wire    žičani model (obojene veze, bez kugli, oznake elemenata)
    space   space-filling (van der Waalsove kugle, bez veza)

Statična slika pod zadanim kutom (molekula se ne vrti u dokumentu); kut se
bira preko rotX/rotY. Zadana tema svijetla/prozirna.
"""

import math
from core import elements as E
from core.svgkit import SvgDoc, lighten

FOV = 2200.0  # veći FOV = blaža perspektiva (bliže ortografskoj)
MOL_PANEL_LIGHT = '#e9e9f0'  # blijedosiva podloga da bijeli atomi ne nestanu
MOL_PANEL_DARK = '#15151d'


# ---------------------------------------------------------------------------
#  Struktura molekule
# ---------------------------------------------------------------------------
def build_molecule(symbols, coords, bonds=None):
    """
    Sklopi i centriraj molekulu.
      symbols  ['O','H','H']
      coords   [(x,y,z), ...] u ångströmima
      bonds    [(i,j,order), ...] ili None
    """
    atoms = [{'sym': s, 'x': float(x), 'y': float(y), 'z': float(z)}
             for s, (x, y, z) in zip(symbols, coords)]
    n = len(atoms) or 1
    cx = sum(a['x'] for a in atoms) / n
    cy = sum(a['y'] for a in atoms) / n
    cz = sum(a['z'] for a in atoms) / n
    for a in atoms:
        a['x'] -= cx
        a['y'] -= cy
        a['z'] -= cz
    return {'atoms': atoms, 'bonds': list(bonds or [])}


# ---------------------------------------------------------------------------
#  3D → 2D
# ---------------------------------------------------------------------------
def _rot_matrix(rx, ry):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    return (cy, 0.0, sy,
            sx * sy, cx, -sx * cy,
            -cx * sy, sx, cx * cy)


def _apply(m, x, y, z):
    return (m[0] * x + m[1] * y + m[2] * z,
            m[3] * x + m[4] * y + m[5] * z,
            m[6] * x + m[7] * y + m[8] * z)


def _radius_A(sym, style):
    """Polumjer atoma u ångströmima po stilu."""
    if style == 'space':
        return (E.VDW.get(sym, E.VDW_DEFAULT)) / 100.0
    # ball / wire koriste kovalentni
    cov = (E.COV.get(sym, E.COV_DEFAULT)) / 100.0
    return cov * (0.52 if style == 'ball' else 0.30)


# ---------------------------------------------------------------------------
#  Render
# ---------------------------------------------------------------------------
def render_molecule(mol, style='ball', theme_name=None, rot_x=0.35, rot_y=0.6,
                    size=440, labels=True):
    atoms = mol['atoms']
    bonds = mol['bonds']
    if not atoms:
        raise ValueError("Prazna molekula")

    m = _rot_matrix(rot_x, rot_y)

    # rotiraj, izračunaj opseg (uključi polumjere za space-fill da stane)
    rot = []
    maxext = 1e-6
    for a in atoms:
        x, y, z = _apply(m, a['x'], a['y'], a['z'])
        rA = _radius_A(a['sym'], style)
        rot.append({'sym': a['sym'], 'x': x, 'y': y, 'z': z, 'rA': rA})
        maxext = max(maxext, math.hypot(x, y) + rA)

    world = (size * 0.46) / maxext  # px po ångströmu

    # projekcija (blaga perspektiva po dubini)
    proj = []
    for r in rot:
        zpx = r['z'] * world
        s = FOV / (FOV + zpx)
        proj.append({
            'sym': r['sym'],
            'px': r['x'] * world * s,
            'py': r['y'] * world * s,
            'pz': zpx,
            'ps': s,
            'r': r['rA'] * world * s,
        })

    doc = SvgDoc(size, size, theme_name, x0=-size / 2, y0=-size / 2)
    th = doc.th

    # blijedosiva podloga da se bijeli atomi (H, odsjaji) ne izgube na bijelom;
    # transparentnu temu poštujemo (bez podloge)
    if th['bg'] is not None:
        panel = MOL_PANEL_DARK if th['bg'] == '#0a0a0f' else MOL_PANEL_LIGHT
        doc.rect(-size / 2, -size / 2, size, size, fill=panel, rx=size * 0.03)

    # objekti za dubinsko sortiranje (daleko prvo)
    objs = []
    if style != 'space':
        for (i, j, order) in bonds:
            if i >= len(proj) or j >= len(proj):
                continue
            a1, a2 = proj[i], proj[j]
            objs.append(('bond', (a1['pz'] + a2['pz']) / 2, a1, a2, order))
    for p in proj:
        objs.append(('atom', p['pz'], p, None, None))
    objs.sort(key=lambda o: o[1])

    bond_line = th['muted']
    for kind, _z, a, b, order in objs:
        if kind == 'bond':
            w = max(1.5, 3 * (a['ps'] + b['ps']) / 2)
            if style == 'ball':
                doc.line(a['px'], a['py'], b['px'], b['py'], stroke=bond_line,
                         sw=w * 0.5, cap='round')
                if order == 2:
                    dx, dy = b['py'] - a['py'], -(b['px'] - a['px'])
                    ln = math.hypot(dx, dy) or 1
                    ox, oy = dx / ln * 3, dy / ln * 3
                    doc.line(a['px'] + ox, a['py'] + oy, b['px'] + ox, b['py'] + oy,
                             stroke=bond_line, sw=w * 0.3, cap='round', opacity=0.7)
            else:  # wire
                doc.line(a['px'], a['py'], b['px'], b['py'],
                         stroke=E.cpk_color(a['sym']), sw=w, cap='round', opacity=0.85)
        else:
            sym = a['sym']
            color = E.cpk_color(sym)
            r = a['r']
            if style != 'wire':
                gid = doc.radial_gradient('g_%s' % sym, color)
                doc.circle(a['px'] + r * 0.15, a['py'] + r * 0.15, r,
                           fill='rgba(0,0,0,0.22)')
                doc.circle(a['px'], a['py'], r, fill='url(#%s)' % gid)
            if labels and (style == 'wire' or (r > 8 and len(atoms) < 30)):
                fs = max(9, r * 0.75)
                lbl = '#ffffff' if style != 'wire' else color
                doc.text(a['px'], a['py'] + fs * 0.34, sym, size=round(fs),
                         weight='600', fill=lbl, anchor='middle')
    return doc.tostring()


# ---------------------------------------------------------------------------
#  Testne molekule (sintetičke koordinate, za rad bez mreže)
# ---------------------------------------------------------------------------
def _tetra(bond=1.09):
    u = bond / math.sqrt(3)
    return [(u, u, u), (-u, -u, u), (-u, u, -u), (u, -u, -u)]


TEST = {
    'voda': build_molecule(
        ['O', 'H', 'H'],
        [(0, 0, 0), (0.757, 0.586, 0), (-0.757, 0.586, 0)],
        [(0, 1, 1), (0, 2, 1)]),
    'metan': build_molecule(
        ['C'] + ['H'] * 4, [(0, 0, 0)] + _tetra(),
        [(0, 1, 1), (0, 2, 1), (0, 3, 1), (0, 4, 1)]),
    'co2': build_molecule(
        ['C', 'O', 'O'], [(0, 0, 0), (1.16, 0, 0), (-1.16, 0, 0)],
        [(0, 1, 2), (0, 2, 2)]),
}


def _benzene():
    atoms, coords, bonds = [], [], []
    R = 1.39
    for i in range(6):
        a = math.pi / 3 * i
        coords.append((R * math.cos(a), R * math.sin(a), 0))
        atoms.append('C')
    for i in range(6):
        a = math.pi / 3 * i
        rr = R + 1.09
        coords.append((rr * math.cos(a), rr * math.sin(a), 0))
        atoms.append('H')
    for i in range(6):
        bonds.append((i, (i + 1) % 6, 2 if i % 2 == 0 else 1))
        bonds.append((i, 6 + i, 1))
    return build_molecule(atoms, coords, bonds)


TEST['benzen'] = _benzene()


if __name__ == "__main__":
    import os
    outdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_preview'))
    os.makedirs(outdir, exist_ok=True)
    count = 0
    for name, mol in TEST.items():
        for style in ('ball', 'wire', 'space'):
            svg = render_molecule(mol, style, 'light')
            assert svg.startswith('<svg') and svg.endswith('</svg>')
            with open(os.path.join(outdir, 'mol_%s_%s.svg' % (name, style)), 'w',
                      encoding='utf-8') as f:
                f.write(svg)
            count += 1
    # prozirna varijanta nema podlogu
    assert render_molecule(TEST['voda'], 'ball', 'transparent').count('<rect') == 0
    print("render.py OK — %d prikaza (voda/metan/co2/benzen × 3 stila) u %s" % (count, outdir))
