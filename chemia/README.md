# Chemia — LibreOffice chemistry extension

Insert a periodic table, element cards and 3D molecules straight at the cursor
in **Writer, Calc, Impress and Draw**. Built for teaching materials: clean,
print-friendly (light/transparent by default), consistent look across both
layers. Image inserts identically in all four apps; data reads from a shared
core. Croatian author; English UI (more languages planned).

**Version 0.9.0 · GPL-3.0**

Two layers over a shared core:

- **Periodic table** — full table, a single group (with its property name), a
  single period, or an element card (Bohr atom model + atomic number, mass,
  period/group, state, electronegativity, protons/neutrons/electrons, radius,
  oxidation states, electron configuration, isotopes).
- **MolViz** — 3D molecule from PubChem (ball & stick / wireframe /
  space-filling), with an optional data panel (Mr, M, m, exact mass, mass
  fractions) whose element legend uses the same CPK atom colours.

## Menu

**Tools ▸ Add-Ons ▸ Chemistry**

- *Periodic table / element…* — dialog: pick table / period / group / element
  card, theme, title (text, alignment, font colour for the full table), preview.
- *Periodic table (full, quick)* — one-click full table.
- *Molecule (PubChem)…* — dialog: search by name or SMILES, pick from candidates
  (isomers / typo suggestions), style, angle, theme, data panel, preview.
- *Edit selected…* — select an inserted Chemia graphic and re-open its dialog
  pre-filled; updates the same object in place.

Inserted graphics span 17 cm (A4 text width) and keep their aspect ratio when
resized. Each carries a recipe so it can be edited/replotted later.

## File layout

Extension files live in `src/` (that is what becomes the `.oxt`). LibreOffice
auto-adds `src/pythonpath/` to `sys.path`; `chemia_addon.py` is the registered
UNO component; `Addons.xcu` adds the menu.

```
src/
  chemia_addon.py    UNO entry component (XJobExecutor)
  Addons.xcu         menu
  description.xml    extension metadata + icon
  description/       store descriptions (hr/en)
  icons/             icon.svg / icon.png / logo-150.png
  META-INF/manifest.xml
  pythonpath/
    core/   elements.py  svgkit.py  i18n.py  insert.py  source.py  ui.py
    pse/    grid.py  card.py  dialog_pse.py
    molviz/ render.py  mass.py  pubchem.py  card.py  dialog_mol.py
    tests/  PubChem JSON samples (ethanol) for the parser test
README.md  LICENSE  .gitignore  dev-install.sh  CATALOG_LISTING.txt
logo.svg  logo-150.png  Chemia.oxt
```

## Build & install

```
./dev-install.sh          # build Chemia.oxt and (if unopkg present) install
# or: Tools ▸ Extension Manager ▸ Add… ▸ Chemia.oxt, then restart LibreOffice
```

## Developing / tests

Pure-Python core runs standalone (no LibreOffice); each module self-checks:

```
cd src/pythonpath
python3 -m core.elements     python3 -m core.svgkit     python3 -m core.i18n
python3 -m molviz.mass       python3 -m molviz.render   python3 -m molviz.pubchem
python3 -m molviz.card       python3 -m pse.grid        python3 -m pse.card
```

`pse.grid`, `pse.card`, `molviz.*` write SVG samples to `src/pythonpath/_preview/`
(scratch). The UNO layer (`insert.py`, `ui.py`, dialogs, `chemia_addon.py`) runs
only inside LibreOffice.

## Languages

English only for now. The i18n layer (`core/i18n.py`) keeps English as the base
and translations as an overlay; the element dataset is bilingual groundwork.
Adding a language = extend `_SUPPORTED` + a catalog; a language dropdown per
dialog (Auto + remembered) comes with the first translation.

## Roadmap (post-0.9)

- Translations by tier: European Latin (de/fr/es/it/pt/nl/pl) → CJK (zh/ja/ko)
  → Arabic (needs RTL layout for the SVG cards) → Swahili (optional)
- Editable native data mode (wire `insert.insert_data` into the dialogs)
- School/condensed formulas (C₂H₅OH) via a curated InChIKey table (optional)
- Contact sheet (several molecule angles in one image)
