# -*- coding: utf-8 -*-
"""
core/i18n.py — lokalizacija.

Baza je engleski: u kodu se pišu engleski stringovi, omotani u t(). Prijevodi su
sloj preko toga (zasad hrvatski). Jezik se bira automatski iz jezika LO sučelja
(detect_locale), ili ručno (set_locale). Nepoznat prijevod → vrati se engleski.

Nazivi elemenata dolaze iz dataseta koji je dvojezičan:
  Element.latin  = engleski naziv (Hydrogen, Sodium, Iron…)  — baza
  Element.name   = hrvatski naziv (Vodik, Natrij, Željezo…)
element_name(el) vrati pravi po trenutnom jeziku.
"""

LOCALE = "en"          # baza; mijenja se preko set_locale / detect_locale
# Zasad SAMO engleski. Katalozi (npr. hr) ostaju kao podloga; za uvođenje
# jezika dodaj kod ovdje (npr. "de", "it", "es", "fr") i pripadni katalog.
_SUPPORTED = ("en",)


def set_locale(code):
    global LOCALE
    code = (code or "en").split("-")[0].split("_")[0].lower()
    LOCALE = code if code in _SUPPORTED else "en"
    return LOCALE


def get_locale():
    return LOCALE


def detect_locale(ctx):
    """Pročitaj jezik LO sučelja iz konfiguracije; fallback engleski."""
    try:
        smgr = ctx.getServiceManager()
        cp = smgr.createInstanceWithContext(
            "com.sun.star.configuration.ConfigurationProvider", ctx)
        from com.sun.star.beans import PropertyValue
        arg = PropertyValue()
        arg.Name = "nodepath"
        arg.Value = "/org.openoffice.Setup/L10N"
        node = cp.createInstanceWithArguments(
            "com.sun.star.configuration.ConfigurationAccess", (arg,))
        loc = node.getByName("ooLocale") or "en-US"
        return set_locale(loc)
    except Exception:
        return set_locale("en")


# ---------------------------------------------------------------------------
#  Katalog: engleski ključ -> prijevodi. Nedostaje li ključ, vraća se engleski.
# ---------------------------------------------------------------------------
_HR = {
    # gumbi / općenito
    "OK": "U redu", "Cancel": "Odustani", "Search": "Traži",
    "Preview": "Pretpregled", "Insert": "Umetni",
    "Chemia — error": "Chemia — greška",
    "No document open.": "Nema otvorenog dokumenta.",
    # dijalog molekule
    "MolViz — molecule": "MolViz — molekula",
    "Molecule (name or SMILES):": "Molekula (naziv ili SMILES):",
    "Candidates:": "Kandidati:",
    "Style:": "Stil:", "Angle:": "Kut:", "Theme:": "Tema:",
    "Data panel": "Podatkovni panel", "Preview:": "Pretpregled:",
    "Wireframe": "Žičani",
    "Native (from PubChem)": "Native (iz PubChema)", "Front": "Sprijeda",
    "Side": "Sa strane", "Top": "Odozgo", "Isometric": "Izometrija",
    "Light": "Svijetla", "Transparent": "Prozirna", "Dark": "Tamna",
    "Mass fractions": "Maseni udjeli", "Exact mass": "Egzaktna masa",
    "First find and select a molecule.": "Prvo pronađi i odaberi molekulu.",
    "Search error: %s": "Greška pri traženju: %s",
    "Nothing found.": "Ništa nađeno.", "Suggestions: ": "Prijedlozi: ",
    "Unknown element: %s": "Nepoznat element: %s",
    # prompti
    "Element": "Element",
    "Symbol or name (e.g. Fe, oxygen):": "Simbol ili naziv (npr. Fe, kisik):",
    "Period": "Perioda", "Period number (1-7):": "Broj periode (1–7):",
    "Group": "Grupa", "Group number (1-18):": "Broj grupe (1–18):",
    # PT dijalog
    "Periodic table / element": "Periodni sustav / element",
    "What to insert:": "Što umetnuti:",
    "Element card": "Kartica elementa", "Full table": "Cijeli sustav",
    "Symbol, name, or number:": "Simbol, naziv ili broj:",
    "Unknown element or number: %s": "Nepoznat element ili broj: %s",
    # kontrole naslova (cijeli sustav)
    "Title:": "Naslov:", "Align:": "Poravnanje:",
    "Left": "Lijevo", "Center": "Sredina", "Right": "Desno",
    "Font color…": "Boja fonta…",
    "Select a Chemia graphic first.": "Prvo označi Chemia prikaz.",
    "Transition metals": "Prijelazni metali",
    # naslovi / nazivi oblika
    "Periodic table of elements": "Periodni sustav elemenata",
    "Periodic table": "Periodni sustav",
    "Period %d": "Perioda %d", "Group %d": "Grupa %d",
    "Element card %s": "Kartica %s", "Molecule %s": "Molekula %s",
    # kartica elementa — sekcije
    "BASIC": "OSNOVNO", "ATOM STRUCTURE": "STRUKTURA ATOMA",
    "ELECTRON CONFIGURATION": "ELEKTRONSKA KONFIGURACIJA", "ISOTOPES": "IZOTOPI",
    # kartica elementa — polja
    "Atomic number": "Atomski broj", "Atomic mass": "Atomska masa",
    "Period / group": "Perioda / grupa", "State": "Agregatno stanje",
    "Electronegativity": "Elektronegativnost", "Protons": "Protoni",
    "Neutrons (most common)": "Neutroni (najčešći)", "Electrons": "Elektroni",
    "Atomic radius": "Atomski polumjer", "Oxidation states": "Oksidacijski br.",
    "Configuration": "Konfiguracija", "Shells": "Ljuske",
    "f-block": "f-blok",
    # molekula — panel
    "QUANTITIES": "VELIČINE", "COMPOSITION (mass fractions)": "SASTAV (maseni udjeli)",
    "Mr (rel. molecular mass)": "Mr (rel. mol. masa)",
    "M (molar mass)": "M (molarna masa)", "m (molecule mass)": "m (masa molekule)",
}

_CATALOGS = {"hr": _HR}


def t(s):
    """Prevedi engleski string na trenutni jezik (fallback: engleski)."""
    if LOCALE == "en":
        return s
    return _CATALOGS.get(LOCALE, {}).get(s, s)


# ---------------------------------------------------------------------------
#  Nazivi vezani uz podatke
# ---------------------------------------------------------------------------
_CATEGORY_EN = {
    "alkali": "Alkali metal", "alkaline": "Alkaline earth metal",
    "transition": "Transition metal", "post": "Post-transition metal",
    "metalloid": "Metalloid", "nonmetal": "Nonmetal", "halogen": "Halogen",
    "noble": "Noble gas", "lanthanide": "Lanthanide", "actinide": "Actinide",
}
_CATEGORY_HR = {
    "alkali": "Alkalijski metal", "alkaline": "Zemnoalkalijski metal",
    "transition": "Prijelazni metal", "post": "Post-prijelazni metal",
    "metalloid": "Metaloid", "nonmetal": "Nemetal", "halogen": "Halogeni element",
    "noble": "Plemeniti plin", "lanthanide": "Lantanoid", "actinide": "Aktinoid",
}
# agregatno stanje: kod koristi 'kruto'/'kaplj'/'plin'
_STATE_EN = {"kruto": "solid", "kaplj": "liquid", "plin": "gas"}
_STATE_HR = {"kruto": "kruto", "kaplj": "tekuće", "plin": "plinovito"}


def element_name(el):
    """Naziv elementa po jeziku (HR: el.name, EN: el.latin)."""
    return el.name if LOCALE == "hr" else el.latin


def element_name_other(el):
    """
    Naziv na drugom jeziku za podnaslov. Samo u hrvatskom (engleski kao koristan
    cross-ref). U engleskom se ne prikazuje (bez hrvatskog u EN kartici).
    """
    if LOCALE != "hr":
        return None
    other = el.latin
    return other if other != element_name(el) else None


def category_name(cat):
    table = _CATEGORY_HR if LOCALE == "hr" else _CATEGORY_EN
    return table.get(cat, cat)


def state_name(state):
    table = _STATE_HR if LOCALE == "hr" else _STATE_EN
    return table.get(state, state)


# nazivi grupa po svojstvima (3–12 kolektivno "prijelazni metali")
_GROUP_EN = {1: "Alkali metals", 2: "Alkaline earth metals", 13: "Boron group",
             14: "Carbon group", 15: "Pnictogens", 16: "Chalcogens",
             17: "Halogens", 18: "Noble gases"}
_GROUP_HR = {1: "Alkalijski metali", 2: "Zemnoalkalijski metali",
             13: "Borova skupina", 14: "Ugljikova skupina", 15: "Pniktogeni",
             16: "Halkogeni", 17: "Halogeni", 18: "Plemeniti plinovi"}


def group_name(g):
    """Naziv grupe po svojstvima; None ako ga nema. 3–12 → 'prijelazni metali'."""
    g = int(g)
    if 3 <= g <= 12:
        return t("Transition metals")
    table = _GROUP_HR if LOCALE == "hr" else _GROUP_EN
    return table.get(g)


if __name__ == "__main__":
    assert set_locale("en") == "en"
    assert t("Search") == "Search"
    assert category_name("noble") == "Noble gas"
    assert state_name("kaplj") == "liquid"
    # zasad samo engleski: hr se mapira na en (fallback)
    assert set_locale("hr-HR") == "en"
    assert t("Search") == "Search"
    assert category_name("noble") == "Noble gas"
    assert t("Nonexistent key") == "Nonexistent key"  # fallback
    # hr katalog i dalje postoji kao podloga za buduće jezike
    assert "Traži" in _HR.values()
    set_locale("en")
    print("i18n.py OK — samo engleski aktivan; hr katalog ostaje kao podloga.")
