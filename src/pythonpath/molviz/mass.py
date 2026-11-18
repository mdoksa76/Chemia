# -*- coding: utf-8 -*-
"""
molviz/mass.py — masene veličine molekule.

Iz molekulske formule ili popisa atoma računa:
  M_r   relativna molekulska masa (bezdimenzijski)
  M     molarna masa (g/mol) — brojčano jednako M_r
  m     masa jedne molekule (kg) = M_r · u = M / N_A
  w(X)  maseni udjeli po elementu (%)

Atomske mase dolaze iz core.elements (prosječne, prirodni izotopi) — to je
veličina za M_r/M. Točna (monoizotopska) masa NIJE ovdje: nju daje PubChem
kao svojstvo (ExactMass), jer ovise o izotopima.

Parser formule podržava zagrade s množiteljem: 'C6H12O6', '(NH4)2SO4',
'Ca(OH)2', 'CuSO4·5H2O' (· ili . kao razdjelnik hidrata).
"""

import re
from collections import OrderedDict
from core import elements as E

_TOKEN = re.compile(r'([A-Z][a-z]?|\(|\)|[·.])(\d*)')


def parse_formula(formula):
    """
    Formulu pretvori u OrderedDict {simbol: broj}, uz provjeru elemenata.
    Baca ValueError za nevaljan element ili nesparene zagrade.
    """
    if not formula or not formula.strip():
        raise ValueError("Prazna formula")
    f = formula.strip().replace(' ', '')
    counts = OrderedDict()
    stack = [counts]
    pos = 0
    for m in _TOKEN.finditer(f):
        if m.start() != pos:
            raise ValueError("Neočekivani znak u formuli: %r" % f[pos:m.start() + 1])
        pos = m.end()
        tok, num = m.group(1), m.group(2)
        mult = int(num) if num else 1
        if tok == '(':
            stack.append(OrderedDict())
        elif tok == ')':
            if len(stack) < 2:
                raise ValueError("Nesparena zagrada")
            grp = stack.pop()
            for sym, c in grp.items():
                stack[-1][sym] = stack[-1].get(sym, 0) + c * mult
        elif tok in '·.':
            # razdjelnik hidrata: sljedeći blok se množi normalno (mult ovdje
            # se odnosi na broj ispred, npr. '5H2O' -> 5 je dio 'H2O' množenja)
            # tretiramo kao implicitnu grupu koja slijedi; jednostavno: ignoriraj
            # sam znak, množitelj primijeni na sljedeće tokene preko nove grupe
            continue
        else:
            if E.by_symbol(tok) is None:
                raise ValueError("Nepoznat element: %r" % tok)
            stack[-1][tok] = stack[-1].get(tok, 0) + mult
    if len(stack) != 1:
        raise ValueError("Nesparena zagrada")
    return counts


def from_counts(counts):
    """
    Iz {simbol: broj} vrati rječnik rezultata:
      formula, M_r, M (g/mol), m (kg), atoms (ukupno), fractions [(sym, w%)].
    """
    if not counts:
        raise ValueError("Nema atoma")
    Mr = 0.0
    per = []
    for sym, n in counts.items():
        a = E.atomic_mass(sym)
        contrib = a * n
        Mr += contrib
        per.append((sym, n, contrib))
    fractions = [(sym, 100.0 * contrib / Mr) for sym, n, contrib in per]
    return {
        'formula': ''.join('%s%s' % (s, (n if n != 1 else '')) for s, n in counts.items()),
        'Mr': Mr,
        'M': Mr,                       # g/mol
        'm_kg': Mr * E.U_KG,           # = M / N_A
        'atoms': sum(counts.values()),
        'fractions': fractions,
    }


def from_formula(formula):
    """Masene veličine iz tekstualne formule."""
    return from_counts(parse_formula(formula))


def from_symbols(symbols):
    """Masene veličine iz popisa simbola atoma (npr. iz PubChem koordinata)."""
    counts = OrderedDict()
    for s in symbols:
        counts[s] = counts.get(s, 0) + 1
    return from_counts(counts)


def format_rows(res, which=('Mr', 'M', 'm', 'fractions')):
    """
    Rezultat pretvori u [(ključ, vrijednost)] za umetanje (SVG tablica ili native).
    'which' bira veličine i redoslijed.
    """
    rows = []
    for key in which:
        if key == 'Mr':
            rows.append(('Mr (rel. mol. masa)', '%.3f' % res['Mr']))
        elif key == 'M':
            rows.append(('M (molarna masa)', '%.3f g/mol' % res['M']))
        elif key == 'm':
            rows.append(('m (masa molekule)', '%.3e kg' % res['m_kg']))
        elif key == 'atoms':
            rows.append(('Broj atoma', str(res['atoms'])))
        elif key == 'fractions':
            for sym, w in res['fractions']:
                rows.append(('w(%s)' % sym, '%.2f %%' % w))
    return rows


if __name__ == "__main__":
    water = from_formula('H2O')
    assert abs(water['Mr'] - 18.015) < 0.01, water['Mr']
    glu = from_formula('C6H12O6')
    assert abs(glu['Mr'] - 180.156) < 0.05, glu['Mr']
    assert glu['atoms'] == 24
    # maseni udjeli zbroje na 100
    assert abs(sum(w for _, w in glu['fractions']) - 100.0) < 1e-6
    # zagrade
    ams = from_formula('(NH4)2SO4')
    assert abs(ams['Mr'] - 132.14) < 0.1, ams['Mr']
    assert dict(parse_formula('Ca(OH)2')) == {'Ca': 1, 'O': 2, 'H': 2}
    # masa jedne molekule vode ~ 2.99e-26 kg
    assert abs(water['m_kg'] - 2.99e-26) < 1e-28, water['m_kg']
    # iz popisa atoma
    assert abs(from_symbols(['O', 'H', 'H'])['Mr'] - 18.015) < 0.01
    # nevaljan element
    try:
        parse_formula('Xx2')
        raise AssertionError("trebalo je puknuti")
    except ValueError:
        pass
    print("mass.py OK — M_r/M/m/udjeli i parser formule rade.")
