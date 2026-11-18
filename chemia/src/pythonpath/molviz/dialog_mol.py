# -*- coding: utf-8 -*-
"""
molviz/dialog_mol.py — bogati dijalog MolViz sloja.

Kontrole: unos (naziv/SMILES) + Traži, candidate lista (izomeri/prijedlozi),
stil (ball/wire/space), kut (presetovi), tema, checkbox panela + izbor veličina,
Pretpregled (prikaz prije umetanja), Umetni / Odustani.

Radi samo u LibreOfficeu (UNO). run(ctx) otvori dijalog i, na Umetni, umetne
sliku na kursor/stranicu i spremi recept za re-edit.
"""

import os
import tempfile

import uno
import unohelper
from com.sun.star.awt import XActionListener

from molviz import pubchem, render, card
from core import insert, source, ui
from core.i18n import t

# (engleski prikaz, interni ključ); prikaz se lokalizira kroz t()
STYLES = [("Ball & stick", "ball"), ("Wireframe", "wire"), ("Space-filling", "space")]
THEMES = [("Light", "light"), ("Transparent", "transparent"), ("Dark", "dark")]
ANGLES = [
    ("Native (from PubChem)", 0.0, 0.0),
    ("Front", 0.0, 0.0),
    ("Side", 0.0, 1.5708),
    ("Top", 1.5708, 0.0),
    ("Isometric", 0.6, 0.78),
]
DETAILS = [("Mr", "Mr"), ("M", "M"), ("m", "m"), ("exact", "Exact mass"),
           ("fractions", "Mass fractions")]


class _Click(unohelper.Base, XActionListener):
    def __init__(self, fn):
        self.fn = fn

    def actionPerformed(self, ev):
        self.fn()

    def disposing(self, ev):
        pass


def _ctl(dm, kind, name, x, y, w, h, **props):
    m = dm.createInstance("com.sun.star.awt.UnoControl%sModel" % kind)
    m.PositionX, m.PositionY, m.Width, m.Height = x, y, w, h
    for k, v in props.items():
        setattr(m, k, v)
    dm.insertByName(name, m)
    return m


def _svg_to_url(svg):
    fd, path = tempfile.mkstemp(suffix=".svg")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(svg)
    return path, unohelper.systemPathToFileUrl(path)


def run(ctx, init=None, shape=None):
    smgr = ctx.getServiceManager()
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    doc = desktop.getCurrentComponent()
    if doc is None:
        ui.message(ctx, t("No document open."), "Chemia", "WARNINGBOX")
        return

    dm = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialogModel", ctx)
    dm.Width, dm.Height, dm.Title = 430, 250, t("MolViz — molecule")

    # --- unos + traži ---
    _ctl(dm, "FixedText", "l_q", 6, 6, 180, 10, Label=t("Molecule (name or SMILES):"))
    _ctl(dm, "Edit", "q", 6, 17, 180, 14)
    _ctl(dm, "Button", "find", 190, 17, 56, 14, Label=t("Search"))
    _ctl(dm, "FixedText", "l_c", 6, 35, 150, 9, Label=t("Candidates:"))
    _ctl(dm, "ListBox", "cand", 6, 45, 240, 44, Dropdown=False, MultiSelection=False)

    # --- stil / kut / tema (dropdown) ---
    _ctl(dm, "FixedText", "l_s", 6, 94, 60, 9, Label=t("Style:"))
    _ctl(dm, "ListBox", "style", 6, 104, 110, 14, Dropdown=True,
         StringItemList=tuple(t(s[0]) for s in STYLES))
    _ctl(dm, "FixedText", "l_a", 128, 94, 60, 9, Label=t("Angle:"))
    _ctl(dm, "ListBox", "angle", 128, 104, 118, 14, Dropdown=True,
         StringItemList=tuple(t(a[0]) for a in ANGLES))
    _ctl(dm, "FixedText", "l_t", 6, 122, 60, 9, Label=t("Theme:"))
    _ctl(dm, "ListBox", "theme", 6, 132, 110, 14, Dropdown=True,
         StringItemList=tuple(t(x[0]) for x in THEMES))

    # --- panel + veličine ---
    _ctl(dm, "CheckBox", "panel", 128, 132, 118, 12, Label=t("Data panel"),
         State=1)
    for i, (key, lbl) in enumerate(DETAILS):
        _ctl(dm, "CheckBox", "d_%s" % key, 6 + (i % 3) * 82, 150 + (i // 3) * 13,
             80, 12, Label=t(lbl), State=1)

    # --- pretpregled (desni stupac) + gumbi ---
    _ctl(dm, "Button", "prev", 6, 180, 80, 16, Label=t("Preview"))
    _ctl(dm, "FixedText", "l_p", 256, 8, 120, 9, Label=t("Preview:"))
    _ctl(dm, "ImageControl", "img", 256, 20, 168, 182, Border=1)
    _ctl(dm, "Button", "ok", 306, 228, 56, 16, Label=t("Insert"), PushButtonType=1,
         DefaultButton=True)
    _ctl(dm, "Button", "cancel", 368, 228, 56, 16, Label=t("Cancel"), PushButtonType=2)

    dlg = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialog", ctx)
    dlg.setModel(dm)
    tk = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    dlg.setVisible(False)
    dlg.createPeer(tk, None)

    # defaulti
    dlg.getControl("style").getModel().SelectedItems = (0,)
    dlg.getControl("angle").getModel().SelectedItems = (0,)
    dlg.getControl("theme").getModel().SelectedItems = (0,)

    state = {"cids": [], "svg": None, "name": None, "tmp": []}

    # prefill (Uredi/Replot) — imamo CID, pa preskačemo pretragu
    if init:
        if init.get("name"):
            dlg.getControl("q").getModel().Text = str(init["name"])
        if init.get("cid"):
            state["cids"] = [init["cid"]]
        si = next((i for i, s in enumerate(STYLES) if s[1] == init.get("style")), 0)
        dlg.getControl("style").getModel().SelectedItems = (si,)
        ti = next((i for i, x in enumerate(THEMES) if x[1] == init.get("theme")), 0)
        dlg.getControl("theme").getModel().SelectedItems = (ti,)
        rx, ry = init.get("rot_x", 0.0), init.get("rot_y", 0.0)
        ai = next((i for i, a in enumerate(ANGLES)
                   if abs(a[1] - rx) < 1e-3 and abs(a[2] - ry) < 1e-3), 0)
        dlg.getControl("angle").getModel().SelectedItems = (ai,)
        dlg.getControl("panel").getModel().State = 1 if init.get("panel", True) else 0
        det = init.get("details")
        if det is not None:
            for key, _ in DETAILS:
                dlg.getControl("d_%s" % key).getModel().State = 1 if key in det else 0

    def _selected_cid():
        pos = dlg.getControl("cand").getSelectedItemPos()
        if state["cids"]:
            return state["cids"][pos if pos >= 0 else 0]
        return None

    def _opts():
        si = lambda n: (list(dlg.getControl(n).getModel().SelectedItems) or [0])[0]
        style = STYLES[si("style")][1]
        aname, rx, ry = ANGLES[si("angle")]
        theme = THEMES[si("theme")][1]
        panel = dlg.getControl("panel").getModel().State == 1
        details = tuple(k for k, _ in DETAILS
                        if dlg.getControl("d_%s" % k).getModel().State == 1)
        return style, rx, ry, theme, panel, details

    def on_find():
        q = (dlg.getControl("q").getModel().Text or "").strip()
        if not q:
            return
        try:
            res = pubchem.resolve(q)
        except Exception as e:
            ui.message(ctx, t("Search error: %s") % e, "MolViz", "ERRORBOX")
            return
        cids = res["cids"]
        state["cids"] = cids
        lb = dlg.getControl("cand")
        lb.getModel().StringItemList = ()
        if not cids:
            sug = res.get("suggestions") or []
            msg = t("Nothing found.") + ((" " + t("Suggestions: ") +
                                          ", ".join(sug[:5])) if sug else "")
            ui.message(ctx, msg, "MolViz", "WARNINGBOX")
            return
        labels = []
        for cid in cids[:10]:
            pp = pubchem.fetch_properties(cid)
            f = pp.get("formula") or ""
            nm = pp.get("title") or pp.get("iupac") or ""
            labels.append("CID %s  %s  %s" % (cid, f, nm[:28]))
        lb.getModel().StringItemList = tuple(labels)
        lb.selectItemPos(0, True)

    def _render_current():
        cid = _selected_cid()
        if cid is None:
            ui.message(ctx, t("First find and select a molecule."), "MolViz", "INFOBOX")
            return None
        style, rx, ry, theme, panel, details = _opts()
        mol = pubchem.parse_record(pubchem.fetch_record(cid))
        props = pubchem.fetch_properties(cid)
        # ako je upisan naziv (ne SMILES/formula), koristi ga; inače IUPAC.
        # (PubChem IUPAC zna biti neprijateljski: voda → "oxidane", aspirin →
        #  "2-acetyloxybenzoic acid")
        q = (dlg.getControl("q").getModel().Text or "").strip()
        if q and not pubchem.looks_like_structure(q):
            name = q                                   # upisani naziv
        else:
            name = props.get("title") or props.get("iupac") or q  # friendly Title
        if panel:
            svg = card.molecule_card(mol, name, props=props, theme=theme,
                                     details=details, style=style, rot_x=rx, rot_y=ry)
        else:
            svg = render.render_molecule(mol, style, theme, rot_x=rx, rot_y=ry)
        state["svg"], state["name"], state["cid"] = svg, name, cid
        return svg

    def on_preview():
        svg = _render_current()
        if not svg:
            return
        path, url = _svg_to_url(svg)
        state["tmp"].append(path)
        img = dlg.getControl("img").getModel()
        img.ScaleImage = True
        try:
            img.ScaleMode = 1  # izotropno — čuva omjer u pretpregledu
        except Exception:
            pass
        img.ImageURL = url

    dlg.getControl("find").addActionListener(_Click(on_find))
    dlg.getControl("prev").addActionListener(_Click(on_preview))

    try:
        rc = dlg.execute()
        if rc == 1:  # Umetni / Ažuriraj
            svg = state["svg"] or _render_current()
            if svg:
                style, rx, ry, theme, panel, details = _opts()
                src = source.make_source(
                    "molecule", cid=state.get("cid"), name=state["name"],
                    style=style, rot_x=rx, rot_y=ry, theme=theme,
                    panel=panel, details=list(details))
                if shape is not None:          # Uredi: ažuriraj isti objekt
                    insert.replace_image(shape, svg)
                    source.attach(shape, src)
                else:
                    # s panelom → puna širina (17 cm); sama molekula → uže
                    width = 90 if not panel else insert.FULL_W_MM
                    sh = insert.insert_image(doc, svg, t("Molecule %s") % state["name"],
                                             width_mm=width)
                    source.attach(sh, src)
    finally:
        dlg.dispose()
        for p in state["tmp"]:
            try:
                os.remove(p)
            except OSError:
                pass
