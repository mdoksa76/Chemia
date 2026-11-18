# -*- coding: utf-8 -*-
"""
core/ui.py — minimalni UNO dijalozi (unos teksta, poruke).

Za prvu verziju .oxt-a dovoljan je jednostavan unos (simbol/naziv/broj) i
poruka o grešci. Bogati dijalozi (presetovi kuta, candidate dropdown, tema,
izbor detalja) dolaze kasnije kao zasebni moduli.

Radi samo unutar LibreOfficea (UNO).
"""


from core.i18n import t


def _smgr(ctx):
    return ctx.getServiceManager()


def ask_text(ctx, title, prompt, default=""):
    """Mali modalni dijalog s jednim poljem. Vrati tekst ili None (Odustani)."""
    smgr = _smgr(ctx)
    dm = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx)
    dm.Width, dm.Height, dm.Title = 190, 78, title

    lbl = dm.createInstance("com.sun.star.awt.UnoControlFixedTextModel")
    lbl.PositionX, lbl.PositionY, lbl.Width, lbl.Height = 6, 6, 178, 24
    lbl.Label, lbl.MultiLine = prompt, True
    dm.insertByName("lbl", lbl)

    ed = dm.createInstance("com.sun.star.awt.UnoControlEditModel")
    ed.PositionX, ed.PositionY, ed.Width, ed.Height = 6, 34, 178, 14
    ed.Text = default
    dm.insertByName("ed", ed)

    ok = dm.createInstance("com.sun.star.awt.UnoControlButtonModel")
    ok.PositionX, ok.PositionY, ok.Width, ok.Height = 96, 56, 42, 16
    ok.Label, ok.PushButtonType, ok.DefaultButton = t("OK"), 1, True  # OK
    dm.insertByName("ok", ok)

    ca = dm.createInstance("com.sun.star.awt.UnoControlButtonModel")
    ca.PositionX, ca.PositionY, ca.Width, ca.Height = 142, 56, 42, 16
    ca.Label, ca.PushButtonType = t("Cancel"), 2  # CANCEL
    dm.insertByName("ca", ca)

    dlg = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialog", ctx)
    dlg.setModel(dm)
    tk = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    dlg.setVisible(False)
    dlg.createPeer(tk, None)
    try:
        if dlg.execute() == 1:  # OK
            return (dlg.getControl("ed").getModel().Text or "").strip() or None
        return None
    finally:
        dlg.dispose()


def message(ctx, text, title="Chemia", kind="INFOBOX"):
    """Poruka korisniku (kind: 'INFOBOX' | 'ERRORBOX' | 'WARNINGBOX')."""
    try:
        import uno
        smgr = _smgr(ctx)
        desktop = smgr.createInstanceWithContext(
            "com.sun.star.frame.Desktop", ctx)
        frame = desktop.getCurrentFrame()
        parent = frame.getContainerWindow() if frame else None
        tk = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
        box = tk.createMessageBox(
            parent,
            uno.Enum("com.sun.star.awt.MessageBoxType", kind),
            1,  # gumbi: OK
            title, text)
        box.execute()
    except Exception:
        pass


def error(ctx, text, title="Chemia — greška"):
    message(ctx, text, title, kind="ERRORBOX")
