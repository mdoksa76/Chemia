# -*- coding: utf-8 -*-
"""
core/svgkit.py — zajednički SVG alat za oba sloja.

Daje:
  - teme (svijetla=default, prozirna, tamna); za dokument je default svijetla,
    jer tamna na papiru nije ni lijepa ni štedljiva s tonerom
  - SvgDoc: mali graditelj SVG dokumenta (viewBox, defs, tijelo, serijalizacija)
  - escape teksta, tekst elementi, linije/pravokutnici/krugovi
  - formula_tspans(): kemijska formula s indeksima (H₂O, C₆H₁₂O₆) preko <tspan>
  - table(): jednostavna tablica ključ/vrijednost iscrtana linijama + tekstom
  - radial_gradient(): sfera-gradijent za prikaz atoma
  - lighten(): posvjetljivanje hex boje

Sve generira čisti standalone SVG (s xmlns), spreman za umetanje u LibreOffice.
"""

import re

MONO = "'DejaVu Sans Mono', 'JetBrains Mono', monospace"
SANS = "'DejaVu Sans', 'Liberation Sans', sans-serif"

# ---------------------------------------------------------------------------
#  Teme
# ---------------------------------------------------------------------------
# bg = None znači bez podloge (prozirno). Boje atoma/kategorija su fiksne i
# dolaze iz core.elements; tema utječe na tekst, linije i podlogu.
THEMES = {
    'light': {
        'bg': '#ffffff', 'text': '#15151f', 'muted': '#5a5a70',
        'line': '#c4c4d2', 'surface': '#f2f2f7', 'accent': '#5b4bd6',
    },
    'transparent': {
        'bg': None, 'text': '#15151f', 'muted': '#5a5a70',
        'line': '#b4b4c4', 'surface': '#f2f2f7', 'accent': '#5b4bd6',
    },
    'dark': {
        'bg': '#0a0a0f', 'text': '#e8e8f0', 'muted': '#666680',
        'line': '#2a2a3a', 'surface': '#12121a', 'accent': '#7c6aff',
    },
}
DEFAULT_THEME = 'light'


def theme(name=None):
    """Vrati rječnik teme; nepoznato ime -> default (svijetla)."""
    return THEMES.get(name or DEFAULT_THEME, THEMES[DEFAULT_THEME])


# ---------------------------------------------------------------------------
#  Osnovni helperi
# ---------------------------------------------------------------------------
def esc(s):
    """XML escape za tekstualni sadržaj i atribute."""
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def lighten(hex_color, amount=80):
    """Posvijetli #rrggbb za 'amount' po kanalu; vrati 'rgb(r,g,b)'."""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r = min(255, int(h[0:2], 16) + amount)
    g = min(255, int(h[2:4], 16) + amount)
    b = min(255, int(h[4:6], 16) + amount)
    return "rgb(%d,%d,%d)" % (r, g, b)


# ---------------------------------------------------------------------------
#  Formula s indeksima
# ---------------------------------------------------------------------------
_FORMULA_TOKEN = re.compile(r'([A-Z][a-z]?)(\d*)|(\(|\))(\d*)|([+\-]\d*|\d*[+\-])')


def formula_tspans(formula, sub_ratio=0.68, dy=0.18):
    """
    Kemijsku formulu pretvori u niz <tspan> elemenata: brojevi iza simbola ili
    zagrade postaju indeksi (subscript), a naboj na kraju (npr. SO4^2-) ide u
    eksponent. Vraća string koji se umeće unutar <text>...</text>.

    Primjeri: 'H2O' -> H, 2(sub), O ; 'C6H12O6' ; '(NH4)2SO4'.
    """
    out = []
    i = 0
    n = len(formula)
    while i < n:
        c = formula[i]
        if c.isalpha():
            # simbol: veliko slovo + opcionalno malo
            j = i + 1
            if j < n and formula[j].islower():
                j += 1
            out.append('<tspan>%s</tspan>' % esc(formula[i:j]))
            i = j
        elif c.isdigit():
            j = i
            while j < n and formula[j].isdigit():
                j += 1
            out.append(
                '<tspan baseline-shift="-%.2fem" font-size="%d%%">%s</tspan>'
                % (dy, int(sub_ratio * 100), esc(formula[i:j]))
            )
            i = j
        elif c in '()':
            out.append('<tspan>%s</tspan>' % esc(c))
            i += 1
        elif c in '+-':
            out.append(
                '<tspan baseline-shift="%.2fem" font-size="%d%%">%s</tspan>'
                % (0.32, int(sub_ratio * 100), esc(c))
            )
            i += 1
        else:
            out.append('<tspan>%s</tspan>' % esc(c))
            i += 1
    return ''.join(out)


# ---------------------------------------------------------------------------
#  SvgDoc — graditelj
# ---------------------------------------------------------------------------
class SvgDoc(object):
    """
    Minimalni graditelj SVG-a. Elementi se dodaju u 'body', definicije
    (gradijenti) u 'defs'. str(doc) ili doc.tostring() daje gotov SVG.
    """

    def __init__(self, width, height, theme_name=None, x0=0, y0=0):
        self.w = width
        self.h = height
        self.x0 = x0
        self.y0 = y0
        self.th = theme(theme_name)
        self._defs = []
        self._body = []
        self._grad_ids = set()

    # -- primitivi ---------------------------------------------------------
    def raw(self, markup):
        self._body.append(markup)
        return self

    def rect(self, x, y, w, h, fill='none', stroke='none', sw=1, rx=0, opacity=None):
        op = '' if opacity is None else ' opacity="%s"' % opacity
        r = '' if not rx else ' rx="%s"' % rx
        self._body.append(
            '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" '
            'stroke="%s" stroke-width="%s"%s%s/>' % (x, y, w, h, fill, stroke, sw, r, op)
        )
        return self

    def line(self, x1, y1, x2, y2, stroke=None, sw=1, dash=None, cap='butt', opacity=None):
        stroke = stroke or self.th['line']
        d = '' if not dash else ' stroke-dasharray="%s"' % dash
        op = '' if opacity is None else ' opacity="%s"' % opacity
        self._body.append(
            '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
            'stroke-width="%s" stroke-linecap="%s"%s%s/>'
            % (x1, y1, x2, y2, stroke, sw, cap, d, op)
        )
        return self

    def circle(self, cx, cy, r, fill='none', stroke='none', sw=1, opacity=None):
        op = '' if opacity is None else ' opacity="%s"' % opacity
        self._body.append(
            '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" '
            'stroke-width="%s"%s/>' % (cx, cy, r, fill, stroke, sw, op)
        )
        return self

    def text(self, x, y, s, size=12, fill=None, anchor='start', weight='normal',
             family=MONO, raw=False, opacity=None):
        """raw=True: 's' je već SVG markup (npr. iz formula_tspans)."""
        fill = fill or self.th['text']
        content = s if raw else esc(s)
        op = '' if opacity is None else ' opacity="%s"' % opacity
        self._body.append(
            '<text x="%.2f" y="%.2f" font-size="%s" font-family="%s" '
            'font-weight="%s" fill="%s" text-anchor="%s"%s>%s</text>'
            % (x, y, size, family, weight, fill, anchor, op, content)
        )
        return self

    def formula(self, x, y, formula_str, size=14, fill=None, anchor='start', weight='500'):
        """Ispiši formulu s indeksima na (x, y)."""
        return self.text(x, y, formula_tspans(formula_str), size=size, fill=fill,
                         anchor=anchor, weight=weight, raw=True)

    # -- definicije --------------------------------------------------------
    def radial_gradient(self, gid, color):
        """Sfera-gradijent (svijetli vrh -> puna boja). Idempotentno po gid."""
        if gid in self._grad_ids:
            return gid
        self._grad_ids.add(gid)
        self._defs.append(
            '<radialGradient id="%s" cx="38%%" cy="32%%" r="65%%">'
            '<stop offset="0%%" stop-color="%s"/>'
            '<stop offset="100%%" stop-color="%s"/></radialGradient>'
            % (gid, lighten(color), color)
        )
        return gid

    # -- tablica ključ/vrijednost -----------------------------------------
    def table(self, x, y, rows, col1=120, col2=120, row_h=20, size=11,
              header=None, rule=True):
        """
        Dvostupčana tablica (ključ | vrijednost). 'rows' = [(k, v), ...].
        Vraća (ukupna_širina, ukupna_visina) za lakše slaganje ispod slike.
        """
        w = col1 + col2
        cy = y
        if header:
            self.text(x, cy + size, header, size=size + 1, weight='700',
                      fill=self.th['accent'])
            cy += row_h
        top = cy
        for k, v in rows:
            if rule:
                self.line(x, cy, x + w, cy, stroke=self.th['line'], sw=0.6, opacity=0.6)
            ty = cy + row_h * 0.68
            self.text(x + 4, ty, k, size=size, fill=self.th['muted'])
            # vrijednost može sadržavati formula-markup ako je tuple ('raw', markup)
            if isinstance(v, tuple) and v and v[0] == 'raw':
                self.text(x + w - 4, ty, v[1], size=size, fill=self.th['text'],
                          anchor='end', weight='500', raw=True)
            else:
                self.text(x + w - 4, ty, v, size=size, fill=self.th['text'],
                          anchor='end', weight='500')
            cy += row_h
        if rule:
            self.line(x, cy, x + w, cy, stroke=self.th['line'], sw=0.6, opacity=0.6)
        return (w, cy - top + (row_h if header else 0))

    # -- serijalizacija ----------------------------------------------------
    def tostring(self):
        bg = ''
        if self.th['bg'] is not None:
            bg = ('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>'
                  % (self.x0, self.y0, self.w, self.h, self.th['bg']))
        defs = ''
        if self._defs:
            defs = '<defs>%s</defs>' % ''.join(self._defs)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'viewBox="%g %g %g %g" width="%g" height="%g">%s%s%s</svg>'
            % (self.x0, self.y0, self.w, self.h, self.w, self.h,
               defs, bg, ''.join(self._body))
        )

    def __str__(self):
        return self.tostring()


if __name__ == "__main__":
    # Samoprovjera
    assert lighten('#000000', 80) == 'rgb(80,80,80)'
    assert lighten('#ffffff', 80) == 'rgb(255,255,255)'
    t = formula_tspans('H2O')
    assert 'baseline-shift="-0.18em"' in t and '>2<' in t
    d = SvgDoc(200, 100, 'light')
    d.formula(10, 30, 'C6H12O6')
    d.table(10, 40, [('Masa', '180.16 g/mol'), ('Atomi', '24')], col1=80, col2=90)
    out = d.tostring()
    assert out.startswith('<svg') and out.endswith('</svg>')
    assert 'fill="#ffffff"' in out  # svijetla podloga
    # prozirna nema podlogu
    assert SvgDoc(10, 10, 'transparent').tostring().count('<rect') == 0
    print("svgkit.py OK — teme, formule, tablica i serijalizacija rade.")
