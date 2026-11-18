# -*- coding: utf-8 -*-
"""
chemia_addon.py — UNO ulazna komponenta Chemia ekstenzije.

Registrirana kao XJobExecutor; stavke izbornika (Addons.xcu) je zovu preko
URL-a  service:hr.mdoksa.chemia.Handler?<naredba>.  LO pozove trigger(naredba).

Paketi (core/pse/molviz) žive u  pythonpath/  pa ih LO sam stavi na sys.path.
"""

import traceback
import uno
import unohelper
from com.sun.star.task import XJobExecutor

from core import insert, source, ui, i18n
from core.i18n import t
from core import elements as E
from pse import grid, card
from pse import dialog_pse
from molviz import render, pubchem
from molviz import dialog_mol

IMPL_NAME = "hr.mdoksa.chemia.Handler"
THEME = "light"  # zadano: svijetlo/za papir (kasnije biranje u dijalogu)


class Handler(unohelper.Base, XJobExecutor):
    def __init__(self, ctx):
        self.ctx = ctx

    # -- UNO ulaz ----------------------------------------------------------
    def trigger(self, arg):
        try:
            i18n.detect_locale(self.ctx)  # jezik iz LO sučelja
            self._run((arg or "").split(":")[0])
        except LookupError as e:
            ui.message(self.ctx, str(e), "Chemia", "WARNINGBOX")
        except Exception:
            ui.error(self.ctx, traceback.format_exc())

    # -- pomoćno -----------------------------------------------------------
    def _doc(self):
        desktop = self.ctx.getServiceManager().createInstanceWithContext(
            "com.sun.star.frame.Desktop", self.ctx)
        return desktop.getCurrentComponent()

    def _place(self, doc, svg, name, src, width_mm):
        shape = insert.insert_image(doc, svg, name, width_mm=width_mm)
        source.attach(shape, src)
        return shape

    # -- naredbe -----------------------------------------------------------
    def _run(self, cmd):
        ctx = self.ctx
        doc = self._doc()
        if doc is None:
            ui.message(ctx, t("No document open."), "Chemia", "WARNINGBOX")
            return

        full = insert.FULL_W_MM  # 17.0 cm

        if cmd == "edit":
            # Uredi/Replot označeni Chemia prikaz
            shp, rec = insert.selected_chemia(doc)
            if shp is None:
                ui.message(ctx, t("Select a Chemia graphic first."), "Chemia", "INFOBOX")
                return
            if rec.get("kind") == "molecule":
                dialog_mol.run(ctx, init=rec, shape=shp)
            else:
                dialog_pse.run(ctx, init=rec, shape=shp)

        elif cmd == "pse_dialog":
            # bogati PT dijalog (kartica / perioda / grupa / cijeli sustav)
            dialog_pse.run(ctx)

        elif cmd == "pse_table":
            svg = grid.render_table(THEME, title=t("Periodic table of elements"))
            self._place(doc, svg, t("Periodic table"),
                        source.make_source("pse", theme=THEME), full)

        elif cmd == "pse_period":
            p = ui.ask_text(ctx, t("Period"), t("Period number (1-7):"))
            if not p:
                return
            pn = int(p)
            svg = grid.render_period(pn, THEME)
            self._place(doc, svg, t("Period %d") % pn,
                        source.make_source("period", p=pn, theme=THEME), full)

        elif cmd == "pse_group":
            g = ui.ask_text(ctx, t("Group"), t("Group number (1-18):"))
            if not g:
                return
            gn = int(g)
            svg = grid.render_group(gn, THEME)
            # jedan uski stupac — ne širiti na punu širinu
            self._place(doc, svg, t("Group %d") % gn,
                        source.make_source("group", g=gn, theme=THEME), 28)

        elif cmd == "element":
            q = ui.ask_text(ctx, t("Element"), t("Symbol or name (e.g. Fe, oxygen):"))
            if not q:
                return
            el = E.by_symbol(q) or E.by_name(q)
            if el is None:
                raise LookupError(t("Unknown element: %s") % q)
            svg = card.render_card(el, THEME)
            self._place(doc, svg, t("Element card %s") % el.sym,
                        source.make_source("card", symbol=el.sym, theme=THEME), full)

        elif cmd == "molecule":
            # bogati dijalog (unos+traži, candidate lista, stil/kut/tema,
            # panel+veličine, pretpregled); sam umeće i sprema recept
            dialog_mol.run(ctx)

        # nepoznate naredbe tiho ignoriramo


# passive registration
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(Handler, IMPL_NAME, (IMPL_NAME,))
