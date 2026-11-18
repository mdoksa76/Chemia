# -*- coding: utf-8 -*-
"""
molviz/pubchem.py — PubChem dohvat + pretvorba u 'mol' strukturu.

Dva dijela:
  Parser (bez mreže, testiran na uzorku):
    parse_record(data)      PubChem PC_Compounds JSON -> mol (atoms/bonds)
    parse_properties(data)  property JSON -> rječnik svojstava
    looks_like_structure(q) heuristika: liči li upit na SMILES/formulu

  Mreža (PUG REST; ovdje se ne može testirati jer PubChem nije na allowlisti):
    resolve(query)          lookup kaskada name -> smiles -> formula -> autocomplete
    fetch_record(cid)       3D zapis (fallback na 2D)
    fetch_properties(cid)   svojstva
    load(query)             sve zajedno -> (mol, props, meta)

Orijentacija: 3D conformer se uzima kakav jest (native). Nikakva rotacija ni
skaliranje ovdje — render.py centrira i bira kut.
"""

import re
import json
import urllib.request
import urllib.parse

from core import elements as E
from molviz.render import build_molecule

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
AUTOCOMPLETE = "https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound"
_UA = "ChemiaLO/0.1 (LibreOffice extension)"
_TIMEOUT = 12

PROPS = "MolecularFormula,MolecularWeight,IUPACName,ExactMass,Charge,ConnectivitySMILES,InChIKey"


# ===========================================================================
#  Parser (bez mreže)
# ===========================================================================
def _symbol(atomic_number):
    el = E.by_z(atomic_number)
    return el.sym if el else 'X'


def parse_record(data):
    """
    PubChem PC_Compounds JSON -> mol {'atoms','bonds','cid'}.
    Robusno mapira koordinate po aid-u (ne oslanja se na isti redoslijed polja).
    """
    comps = data.get("PC_Compounds") or []
    if not comps:
        raise ValueError("Nema PC_Compounds u zapisu")
    c = comps[0]

    cid = (c.get("id", {}).get("id", {}) or {}).get("cid")

    atoms = c.get("atoms", {})
    aids = atoms.get("aid") or []
    elements = atoms.get("element") or []
    if not aids or len(aids) != len(elements):
        raise ValueError("Neispravan atoms blok")

    coords = c.get("coords") or []
    if not coords:
        raise ValueError("Zapis nema koordinata (nema coords bloka)")
    coord0 = coords[0]
    conformers = coord0.get("conformers") or []
    if not conformers:
        raise ValueError("Zapis nema conformera")
    conf = conformers[0]
    caids = coord0.get("aid") or aids
    xs = conf.get("x") or []
    ys = conf.get("y") or []
    zs = conf.get("z") or [0.0] * len(xs)
    if not xs or len(xs) != len(caids):
        raise ValueError("Neispravan conformer (x ne odgovara aid)")

    # aid -> (x,y,z)
    pos = {aid: (xs[i], ys[i], zs[i]) for i, aid in enumerate(caids)}

    symbols, clist = [], []
    for i, aid in enumerate(aids):
        symbols.append(_symbol(elements[i]))
        p = pos.get(aid, (0.0, 0.0, 0.0))
        clist.append(p)

    # aid (1-based) -> indeks u našoj listi
    idx = {aid: i for i, aid in enumerate(aids)}

    bonds = []
    b = c.get("bonds") or {}
    a1 = b.get("aid1") or []
    a2 = b.get("aid2") or []
    order = b.get("order") or [1] * len(a1)
    for k in range(len(a1)):
        i = idx.get(a1[k])
        j = idx.get(a2[k])
        if i is None or j is None:
            continue
        bonds.append((i, j, order[k] if k < len(order) else 1))

    mol = build_molecule(symbols, clist, bonds)
    mol['cid'] = cid
    return mol


def parse_properties(data):
    """property JSON -> rječnik; tolerira string/broj i polja koja fale."""
    try:
        p = data["PropertyTable"]["Properties"][0]
    except (KeyError, IndexError, TypeError):
        return {}

    def num(v):
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return {
        'cid': p.get('CID'),
        'formula': p.get('MolecularFormula'),
        'mw': num(p.get('MolecularWeight')),     # često string u izvoru
        'exact_mass': num(p.get('ExactMass')),
        'iupac': p.get('IUPACName'),
        'charge': p.get('Charge'),
        'smiles': p.get('ConnectivitySMILES') or p.get('CanonicalSMILES') or p.get('SMILES'),
        'inchikey': p.get('InChIKey'),
    }


_STRUCT_RE = re.compile(r'^[A-Za-z0-9()\[\]=#@+\-./\\%]+$')


def looks_like_structure(q):
    """
    Gruba heuristika: liči li upit na formulu/SMILES (pa probati smiles/formula
    namespace) umjesto čistog imena. Imena imaju razmake/dijakritike/duge riječi.
    """
    s = q.strip()
    if not s or ' ' in s:
        return False
    if not _STRUCT_RE.match(s):
        return False
    # mora sadržavati barem jedan znak tipičan za strukturu, ili veliko+broj
    if any(ch.isdigit() for ch in s) or any(ch in s for ch in '()[]=#+-'):
        return True
    # npr. 'CCO' (SMILES) — same velika slova elemenata
    return s[:1].isupper() and len(s) <= 12 and s.isalpha()


# ===========================================================================
#  Mreža (PUG REST) — nije testabilno u ovom okruženju
# ===========================================================================
def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": _UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _cids_from(url):
    try:
        d = _get_json(url)
        return d.get("IdentifierList", {}).get("CID", []) or []
    except Exception:
        return []


def find_cids_by_name(name):
    return _cids_from("%s/compound/name/%s/cids/JSON" % (BASE, urllib.parse.quote(name)))


def find_cids_by_smiles(smiles):
    return _cids_from("%s/compound/smiles/%s/cids/JSON" % (BASE, urllib.parse.quote(smiles)))


def find_cids_by_formula(formula):
    # formula pretraga zna biti spora i vraća više izomera
    return _cids_from("%s/compound/formula/%s/cids/JSON" % (BASE, urllib.parse.quote(formula)))


def autocomplete(term, limit=10):
    try:
        d = _get_json("%s/%s/json?limit=%d" % (AUTOCOMPLETE, urllib.parse.quote(term), limit))
        return d.get("dictionary_terms", {}).get("compound", []) or []
    except Exception:
        return []


def resolve(query):
    """
    Lookup kaskada. Vraća rječnik:
      {'cids': [...], 'source': 'name|smiles|formula', 'suggestions': [...]}
    'cids' s više članova = korisnik bira (izomeri/kandidati). Prazan 'cids' +
    'suggestions' = vjerojatan tipfeler; ponudi prijedloge.
    """
    q = query.strip()
    cids = find_cids_by_name(q)
    if cids:
        return {'cids': cids, 'source': 'name', 'suggestions': []}

    if looks_like_structure(q):
        cids = find_cids_by_smiles(q)
        if cids:
            return {'cids': cids, 'source': 'smiles', 'suggestions': []}
        cids = find_cids_by_formula(q)
        if cids:
            return {'cids': cids, 'source': 'formula', 'suggestions': []}

    sugg = autocomplete(q)
    if sugg:
        # probaj prvi prijedlog kao ime
        cids = find_cids_by_name(sugg[0])
        return {'cids': cids, 'source': 'autocomplete', 'suggestions': sugg}

    return {'cids': [], 'source': None, 'suggestions': []}


def fetch_record(cid):
    """3D zapis; fallback na 2D ako 3D nema/prazan."""
    try:
        d = _get_json("%s/compound/cid/%d/record/JSON?record_type=3d" % (BASE, cid))
        comps = d.get("PC_Compounds") or []
        if comps and (comps[0].get("coords") or [{}])[0].get("conformers"):
            return d
    except Exception:
        pass
    return _get_json("%s/compound/cid/%d/record/JSON" % (BASE, cid))


def fetch_title(cid):
    """
    Prijateljski naziv spoja (PubChem "Title": Water, Aspirin, Ethanol…) —
    za razliku od IUPAC polja koje za vodu daje "oxidane".
    """
    try:
        d = _get_json("%s/compound/cid/%d/description/JSON" % (BASE, cid))
        for info in d.get("InformationList", {}).get("Information", []):
            if info.get("Title"):
                return info["Title"]
    except Exception:
        pass
    return None


def fetch_properties(cid):
    try:
        d = _get_json("%s/compound/cid/%d/property/%s/JSON" % (BASE, cid, PROPS))
        p = parse_properties(d)
    except Exception:
        p = {}
    p["title"] = fetch_title(cid)
    return p


def load(query):
    """
    Visoki ulaz: query -> (mol, props, meta).
    meta sadrži 'source' i 'candidates' (ako ih je više). Baca LookupError ako
    ništa nije nađeno (uz eventualne 'suggestions' u poruci).
    """
    res = resolve(query)
    if not res['cids']:
        msg = "Molekula nije nađena: %r" % query
        if res['suggestions']:
            msg += " — možda: " + ", ".join(res['suggestions'][:5])
        raise LookupError(msg)
    cid = res['cids'][0]
    mol = parse_record(fetch_record(cid))
    props = fetch_properties(cid)
    meta = {'source': res['source'],
            'candidates': res['cids'][:10],
            'suggestions': res['suggestions']}
    return mol, props, meta


if __name__ == "__main__":
    import os
    here = os.path.dirname(__file__)
    sample = os.path.join(here, '..', 'tests', 'ethanol_3d.json')
    with open(sample, encoding='utf-8') as f:
        data = json.load(f)

    mol = parse_record(data)
    syms = [a['sym'] for a in mol['atoms']]
    assert syms == ['O', 'C', 'C', 'H', 'H', 'H', 'H', 'H', 'H'], syms
    assert mol['cid'] == 702
    assert len(mol['bonds']) == 8
    # OH veza: O (indeks 0) — H (aid 9 -> indeks 8)
    assert (0, 8, 1) in mol['bonds'], mol['bonds']
    # centrirano
    cx = sum(a['x'] for a in mol['atoms']) / 9
    assert abs(cx) < 1e-9

    # heuristika
    assert looks_like_structure('CCO') is True
    assert looks_like_structure('C2H5OH') is True
    assert looks_like_structure('(NH4)2SO4') is True
    assert looks_like_structure('ethanol') is False
    assert looks_like_structure('sumporna kiselina') is False

    # parse_properties na STVARNOM uzorku (string MW/ExactMass)
    with open(os.path.join(here, '..', 'tests', 'ethanol_props.json'), encoding='utf-8') as f:
        pp = parse_properties(json.load(f))
    assert pp['formula'] == 'C2H6O' and abs(pp['mw'] - 46.07) < 1e-6
    assert abs(pp['exact_mass'] - 46.041864811) < 1e-6
    assert pp['smiles'] == 'CCO' and pp['charge'] == 0
    # a kad polja fale -> None, ne pada
    pp2 = parse_properties({"PropertyTable": {"Properties": [
        {"CID": 702, "MolecularFormula": "C2H6O", "MolecularWeight": "46.07"}]}})
    assert pp2['exact_mass'] is None

    # render iz stvarnih koordinata radi
    from molviz.render import render_molecule
    svg = render_molecule(mol, 'ball', 'light', rot_x=0.0, rot_y=0.0)
    assert svg.startswith('<svg')
    outdir = os.path.abspath(os.path.join(here, '..', '_preview'))
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'mol_etanol_ball.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)
    print("pubchem.py OK — parser na stvarnom etanol uzorku radi; render u", outdir)
