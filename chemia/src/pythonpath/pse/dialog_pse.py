# -*- coding: utf-8 -*-
"""
pse/dialog_pse.py — bogati dijalog PT sloja (isti obrazac kao dialog_mol).

Kontrole: što umetnuti (kartica elementa / perioda / grupa / cijeli sustav),
unos (simbol-naziv ili broj), tema, Pretpregled (desni stupac), Umetni/Odustani.

Radi samo u LibreOfficeu (UNO).
"""

from pse import grid, card
from core import elements as E
from core import insert, source, ui
from core.i18n import t
from molviz.dialog_mol import _Click, _ctl, _svg_to_url  # dijeljeni helperi

MODES = [("Element card", "card"), ("Period", "period"),
         ("Group", "group"), ("Full table", "table")]
THEMES = [("Light", "light"), ("Transparent", "transparent"), ("Dark", "dark")]
ALIGN = [("Left", "left"), ("Center", "center"), ("Right", "right")]


def _pick_color(ctx, cur_hex):
    """Otvori LO color picker; vrati '#rrggbb' ili None (odustao/greška)."""
    try:
        from com.sun.star.beans import PropertyValue
        cp = ctx.getServiceManager().createInstanceWithContext(
            "com.sun.star.cui.ColorPicker", ctx)
        p = PropertyValue()
        p.Name, p.Value = "Color", int((cur_hex or "#5b4bd6").lstrip("#"), 16)
        cp.setPropertyValues((p,))
        if cp.execute() == 1:  # OK
            for pv in cp.getPropertyValues():
                if pv.Name == "Color":
                    return "#%06x" % (int(pv.Value) & 0xFFFFFF)
    except Exception:
        pass
    return None


def _resolve(mode, q, theme, title=None, align="left", color=None):
    """Vrati (svg, name, src, width_mm) za zadani mod; ili baci grešku."""
    if mode == "table":
        ttl = title or t("Periodic table of elements")
        svg = grid.render_table(theme, title=ttl, title_align=align, title_color=color)
        return (svg, t("Periodic table"),
                source.make_source("pse", theme=theme, title=ttl, align=align,
                                   color=color), insert.FULL_W_MM)
    if mode == "period":
        pn = int(q)
        return (grid.render_period(pn, theme), t("Period %d") % pn,
                source.make_source("period", p=pn, theme=theme), insert.FULL_W_MM)
    if mode == "group":
        gn = int(q)
        return (grid.render_group(gn, theme), t("Group %d") % gn,
                source.make_source("group", g=gn, theme=theme), 28)
    # card
    el = E.by_symbol(q) or E.by_name(q)
    if el is None:
        raise ValueError(t("Unknown element or number: %s") % q)
    return (card.render_card(el, theme), t("Element card %s") % el.sym,
            source.make_source("card", symbol=el.sym, theme=theme), insert.FULL_W_MM)


_KIND_TO_MODE = {"pse": "table", "period": "period", "group": "group", "card": "card"}


def run(ctx, init=None, shape=None):
    smgr = ctx.getServiceManager()
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    doc = desktop.getCurrentComponent()
    if doc is None:
        ui.message(ctx, t("No document open."), "Chemia", "WARNINGBOX")
        return

    dm = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialogModel", ctx)
    dm.Width, dm.Height, dm.Title = 430, 250, t("Periodic table / element")

    _ctl(dm, "FixedText", "l_mode", 6, 8, 150, 9, Label=t("What to insert:"))
    _ctl(dm, "ListBox", "mode", 6, 19, 180, 14, Dropdown=True,
         StringItemList=tuple(t(m[0]) for m in MODES))
    _ctl(dm, "FixedText", "l_in", 6, 40, 200, 9, Label=t("Symbol, name, or number:"))
    _ctl(dm, "Edit", "q", 6, 51, 180, 14)
    _ctl(dm, "FixedText", "l_t", 6, 74, 150, 9, Label=t("Theme:"))
    _ctl(dm, "ListBox", "theme", 6, 85, 150, 14, Dropdown=True,
         StringItemList=tuple(t(x[0]) for x in THEMES))

    # kontrole naslova (koriste se za "Cijeli sustav")
    _ctl(dm, "FixedText", "l_ti", 6, 106, 200, 9, Label=t("Title:"))
    _ctl(dm, "Edit", "title", 6, 117, 180, 14, Text=t("Periodic table of elements"))
    _ctl(dm, "FixedText", "l_al", 6, 137, 90, 9, Label=t("Align:"))
    _ctl(dm, "ListBox", "align", 6, 148, 90, 14, Dropdown=True,
         StringItemList=tuple(t(a[0]) for a in ALIGN))
    _ctl(dm, "Button", "color", 104, 148, 82, 14, Label=t("Font color…"))

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
    dlg.getControl("mode").getModel().SelectedItems = (0,)
    dlg.getControl("theme").getModel().SelectedItems = (0,)
    dlg.getControl("align").getModel().SelectedItems = (0,)

    state = {"result": None, "tmp": [], "color": None}

    # prefill (Uredi/Replot)
    if init:
        mode = _KIND_TO_MODE.get(init.get("kind"), "table")
        mi = next((i for i, m in enumerate(MODES) if m[1] == mode), 0)
        dlg.getControl("mode").getModel().SelectedItems = (mi,)
        ti = next((i for i, x in enumerate(THEMES) if x[1] == init.get("theme")), 0)
        dlg.getControl("theme").getModel().SelectedItems = (ti,)
        qv = {"period": init.get("p"), "group": init.get("g"),
              "card": init.get("symbol")}.get(mode)
        if qv is not None:
            dlg.getControl("q").getModel().Text = str(qv)
        if init.get("title"):
            dlg.getControl("title").getModel().Text = init["title"]
        ai = next((i for i, a in enumerate(ALIGN) if a[1] == init.get("align")), 0)
        dlg.getControl("align").getModel().SelectedItems = (ai,)
        state["color"] = init.get("color")

    def _pick():
        mi = (list(dlg.getControl("mode").getModel().SelectedItems) or [0])[0]
        ti = (list(dlg.getControl("theme").getModel().SelectedItems) or [0])[0]
        ai = (list(dlg.getControl("align").getModel().SelectedItems) or [0])[0]
        mode, theme, align = MODES[mi][1], THEMES[ti][1], ALIGN[ai][1]
        q = (dlg.getControl("q").getModel().Text or "").strip()
        title = (dlg.getControl("title").getModel().Text or "").strip() or None
        return _resolve(mode, q, theme, title=title, align=align, color=state["color"])

    def on_color():
        c = _pick_color(ctx, state["color"])
        if c:
            state["color"] = c

    def on_preview():
        try:
            svg, name, src, width = _pick()
        except Exception as e:
            ui.message(ctx, str(e), "Chemia", "WARNINGBOX")
            return
        state["result"] = (svg, name, src, width)
        path, url = _svg_to_url(svg)
        state["tmp"].append(path)
        img = dlg.getControl("img").getModel()
        img.ScaleImage = True
        try:
            img.ScaleMode = 1
        except Exception:
            pass
        img.ImageURL = url

    dlg.getControl("prev").addActionListener(_Click(on_preview))
    dlg.getControl("color").addActionListener(_Click(on_color))

    try:
        rc = dlg.execute()
        if rc == 1:
            res = state["result"]
            if res is None:
                res = _pick()  # nije bilo pretpregleda — renderiraj sad
            svg, name, src, width = res
            if shape is not None:          # Uredi: ažuriraj isti objekt
                insert.replace_image(shape, svg)
                source.attach(shape, src)
            else:
                sh = insert.insert_image(doc, svg, name, width_mm=width)
                source.attach(sh, src)
    except Exception as e:
        ui.message(ctx, str(e), "Chemia", "WARNINGBOX")
    finally:
        dlg.dispose()
        for p in state["tmp"]:
            try:
                import os
                os.remove(p)
            except OSError:
                pass
