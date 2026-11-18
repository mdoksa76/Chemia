# -*- coding: utf-8 -*-
"""
core/source.py — spremanje "recepta" uz umetnuti objekt (re-edit).

Uz svaku umetnutu sliku spremimo kompaktni opis kako je nastala (sloj, izbor,
tema, kut...) u svojstvo oblika (Description). Kasniji "Uredi/Replot" pročita
taj opis, vrati dijalog u isto stanje i regenerira.

Format: 'chemia:v1:' + JSON. make_source/parse_source su čisti (testirani);
attach/read dotiču UNO oblik (rade unutar LibreOfficea).
"""

import json

MARK = "chemia:v1:"


def make_source(kind, **params):
    """
    kind: 'pse' | 'group' | 'period' | 'card' | 'molecule'
    params: npr. theme='light', symbol='Fe' / name='ethanol' / g=1 / p=2 /
            style='ball', rot_x=0.0, rot_y=0.0, details=['Mr','M']...
    """
    payload = {"kind": kind}
    payload.update({k: v for k, v in params.items() if v is not None})
    return MARK + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_source(s):
    """Vrati rječnik recepta ili None ako string nije Chemia izvor."""
    if not s or not s.startswith(MARK):
        return None
    try:
        d = json.loads(s[len(MARK):])
    except ValueError:
        return None
    return d if isinstance(d, dict) and "kind" in d else None


def attach(shape, src):
    """Spremi izvor u Description oblika (unutar LibreOfficea)."""
    try:
        shape.Description = src
    except Exception:
        pass
    return shape


def read(shape):
    """Pročitaj recept iz oblika ili None."""
    try:
        return parse_source(shape.Description)
    except Exception:
        return None


if __name__ == "__main__":
    s = make_source("card", symbol="Fe", theme="light")
    assert s.startswith(MARK)
    d = parse_source(s)
    assert d == {"kind": "card", "symbol": "Fe", "theme": "light"}, d

    s2 = make_source("molecule", name="ethanol", style="ball",
                     rot_x=0.0, rot_y=0.0, theme="transparent", details=["Mr", "M"])
    d2 = parse_source(s2)
    assert d2["kind"] == "molecule" and d2["details"] == ["Mr", "M"]
    assert d2["name"] == "ethanol"

    # None se preskače
    assert "ignore" not in parse_source(make_source("pse", theme="dark", ignore=None))
    # ne-Chemia stringovi
    assert parse_source("") is None
    assert parse_source("neki opis slike") is None
    assert parse_source("chemia:v1:not-json") is None
    print("source.py OK — make/parse recepta rade.")
