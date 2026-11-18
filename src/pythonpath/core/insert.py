# -*- coding: utf-8 -*-
"""
core/insert.py — umetanje u LibreOffice preko UNO-a.

Dvije razine:
  insert_image(doc, svg, name, width_mm)   SVG slika na kursor/stranicu —
                                            identično u sve 4 aplikacije
  insert_data(doc, title, formula, rows)    naslov + formula + tablica veličina
                                            kao UREĐIVI native sadržaj, po app:
      Writer   paragraf (naziv+formula) + tekst-tablica
      Calc     ćelije (naziv/formula + tablica) uz selekciju
      Impress  tekstualni okvir na slajdu
      Draw     tekstualni okvir na stranici

Napomena: ovaj modul radi SAMO unutar LibreOfficea (treba živi UNO most). Ne
pokreće se u razvojnom okruženju; testira se instalacijom .oxt-a.

Mjere: LO koristi 1/100 mm. SVG dolazi s px dimenzijama (96 dpi pretpostavka).
"""

import re

try:
    import uno  # noqa: F401
    import unohelper
    from com.sun.star.beans import PropertyValue
    from com.sun.star.awt import Size, Point
    from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
    _UNO = True
except Exception:  # izvan LibreOfficea
    _UNO = False


# ---------------------------------------------------------------------------
#  Pomoćno
# ---------------------------------------------------------------------------
PX_TO_MM100 = 2540.0 / 96.0  # px (96 dpi) -> 1/100 mm

# iskoristiva širina teksta na A4 (21 cm) uz 2+2 cm margine → 17.0 cm
FULL_W_MM = 170.0


def _ctx_smgr(doc):
    ctx = uno.getComponentContext()
    return ctx, ctx.getServiceManager()


def _svg_dims(svg):
    """Vrati (width_px, height_px) iz <svg width=.. height=..> ili viewBoxa."""
    mw = re.search(r'\bwidth="([\d.]+)"', svg)
    mh = re.search(r'\bheight="([\d.]+)"', svg)
    if mw and mh:
        return float(mw.group(1)), float(mh.group(1))
    vb = re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', svg)
    if vb:
        return float(vb.group(1)), float(vb.group(2))
    return 400.0, 300.0


def _native_ratio(graphic, svg):
    """
    Omjer (w, h) grafike. Prvo iz LO-ve native veličine (Size100thMM) da se
    poklopi s onim što LO koristi za 'zadrži proporciju'; fallback na px iz SVG-a.
    """
    try:
        s = graphic.Size100thMM
        if s and s.Width and s.Height:
            return float(s.Width), float(s.Height)
    except Exception:
        pass
    return _svg_dims(svg)


def _size_mm100(ratio, width_mm):
    """
    Ciljna veličina u 1/100 mm uz TOČAN native omjer (ratio=(w,h)).
    width_mm=None -> native veličina iz px.
    """
    rw, rh = ratio
    if width_mm:
        w = int(round(width_mm * 100))
        h = int(round(w * rh / rw))
    else:
        w = int(round(rw * PX_TO_MM100))
        h = int(round(rh * PX_TO_MM100))
    return w, h


def app_of(doc):
    """Vrati 'writer' | 'calc' | 'impress' | 'draw' | None."""
    s = doc.supportsService
    if s("com.sun.star.text.TextDocument"):
        return 'writer'
    if s("com.sun.star.sheet.SpreadsheetDocument"):
        return 'calc'
    if s("com.sun.star.presentation.PresentationDocument"):
        return 'impress'
    if s("com.sun.star.drawing.DrawingDocument"):
        return 'draw'
    return None


def _graphic_from_svg(smgr, ctx, svg):
    """Napravi XGraphic iz SVG stringa preko in-memory streama."""
    svc = smgr.createInstanceWithContext
    # upiši SVG u sekvencijalni memorijski stream
    pipe = svc("com.sun.star.io.Pipe", ctx)
    text_out = svc("com.sun.star.io.TextOutputStream", ctx)
    text_out.setOutputStream(pipe)
    text_out.setEncoding("UTF-8")
    text_out.writeString(svg)
    text_out.closeOutput()

    gp = svc("com.sun.star.graphic.GraphicProvider", ctx)
    p = PropertyValue()
    p.Name = "InputStream"
    p.Value = pipe
    return gp.queryGraphic((p,))


# ---------------------------------------------------------------------------
#  Umetanje slike (sve 4 app)
# ---------------------------------------------------------------------------
def insert_image(doc, svg, name="Chemia", width_mm=None):
    """Umetni SVG kao sliku. Writer: na kursor (kao znak). Ostali: na stranicu."""
    if not _UNO:
        raise RuntimeError("UNO nije dostupan (pokreni unutar LibreOfficea)")
    ctx, smgr = _ctx_smgr(doc)
    graphic = _graphic_from_svg(smgr, ctx, svg)
    w, h = _size_mm100(_native_ratio(graphic, svg), width_mm)
    app = app_of(doc)

    if app == 'writer':
        shape = doc.createInstance("com.sun.star.text.TextGraphicObject")
        shape.Graphic = graphic
        shape.AnchorType = AS_CHARACTER
        shape.Width, shape.Height = w, h
        try:
            shape.Title = name
        except Exception:
            pass
        vc = doc.getCurrentController().getViewCursor()
        doc.getText().insertTextContent(vc, shape, False)
        return shape

    # Calc/Impress/Draw: GraphicObjectShape na odgovarajuću draw-stranicu
    shape = doc.createInstance("com.sun.star.drawing.GraphicObjectShape")
    if app == 'calc':
        page = doc.getCurrentController().getActiveSheet().getDrawPage()
    else:
        page = doc.getCurrentController().getCurrentPage()
    page.add(shape)
    shape.Graphic = graphic
    shape.setSize(Size(w, h))
    try:
        vs = doc.getCurrentController().getFrame().getContainerWindow().getPosSize()
        shape.setPosition(Point(int(w * 0.15), int(h * 0.15)))
    except Exception:
        pass
    try:
        shape.Name = name
    except Exception:
        pass
    return shape


def replace_image(shape, svg, width_mm=None):
    """
    Zamijeni grafiku POSTOJEĆEG oblika novim SVG-om (za Uredi/Replot). Zadrži
    trenutnu širinu (osim ako je zadan width_mm), visinu preračunaj po novom
    native omjeru. Radi za Writer TextGraphicObject i drawing GraphicObjectShape.
    """
    if not _UNO:
        raise RuntimeError("UNO nije dostupan (pokreni unutar LibreOfficea)")
    ctx = uno.getComponentContext()
    smgr = ctx.getServiceManager()
    graphic = _graphic_from_svg(smgr, ctx, svg)
    rw, rh = _native_ratio(graphic, svg)

    if width_mm:
        w, h = _size_mm100((rw, rh), width_mm)
    else:
        try:
            cur_w = shape.getSize().Width
        except Exception:
            cur_w = getattr(shape, "Width", 0)
        w = cur_w or _size_mm100((rw, rh), None)[0]
        h = int(round(w * rh / rw))

    shape.Graphic = graphic
    try:
        shape.setSize(Size(w, h))
    except Exception:
        shape.Width, shape.Height = w, h
    return shape


def selected_chemia(doc):
    """
    Vrati (shape, recept) za označeni Chemia oblik u dokumentu, ili (None, None).
    Prepoznaje ga po spremljenom receptu u Description.
    """
    from core import source as _source
    try:
        sel = doc.getCurrentController().getSelection()
    except Exception:
        return None, None
    if sel is None:
        return None, None
    items = []
    if hasattr(sel, "getCount"):
        for i in range(sel.getCount()):
            try:
                items.append(sel.getByIndex(i))
            except Exception:
                pass
    else:
        items.append(sel)
    for it in items:
        rec = _source.read(it)
        if rec:
            return it, rec
    return None, None


# ---------------------------------------------------------------------------
#  Umetanje uređivih podataka (native po app)
# ---------------------------------------------------------------------------
def insert_data(doc, title, formula, rows):
    """
    Umetni naslov + formulu + tablicu [(ključ, vrijednost), ...] kao UREĐIVI
    native sadržaj, prilagođeno aplikaciji.
    """
    if not _UNO:
        raise RuntimeError("UNO nije dostupan (pokreni unutar LibreOfficea)")
    app = app_of(doc)
    if app == 'writer':
        return _data_writer(doc, title, formula, rows)
    if app == 'calc':
        return _data_calc(doc, title, formula, rows)
    return _data_draw(doc, title, formula, rows)  # impress/draw


def _data_writer(doc, title, formula, rows):
    text = doc.getText()
    vc = doc.getCurrentController().getViewCursor()
    cur = text.createTextCursorByRange(vc.getStart())

    if title:
        line = title + ((u"  (%s)" % formula) if formula else u"")
        cur.setPropertyValue("CharWeight", 150.0)  # BOLD
        text.insertString(cur, line, False)
        cur.setPropertyValue("CharWeight", 100.0)  # NORMAL
        text.insertControlCharacter(cur, PARAGRAPH_BREAK, False)

    tbl = doc.createInstance("com.sun.star.text.TextTable")
    tbl.initialize(len(rows), 2)
    text.insertTextContent(cur, tbl, False)
    for i, (k, v) in enumerate(rows):
        tbl.getCellByName("A%d" % (i + 1)).setString(unicode_str(k))
        tbl.getCellByName("B%d" % (i + 1)).setString(unicode_str(v))
    return tbl


def _data_calc(doc, title, formula, rows):
    ctrl = doc.getCurrentController()
    sheet = ctrl.getActiveSheet()
    sel = ctrl.getSelection()
    try:
        addr = sel.getRangeAddress() if hasattr(sel, "getRangeAddress") else sel.getCellAddress()
        r0 = addr.StartRow if hasattr(addr, "StartRow") else addr.Row
        c0 = addr.StartColumn if hasattr(addr, "StartColumn") else addr.Column
    except Exception:
        r0, c0 = 0, 0
    r = r0
    if title:
        sheet.getCellByPosition(c0, r).setString(unicode_str(title))
        if formula:
            sheet.getCellByPosition(c0 + 1, r).setString(unicode_str(formula))
        r += 1
    for k, v in rows:
        sheet.getCellByPosition(c0, r).setString(unicode_str(k))
        sheet.getCellByPosition(c0 + 1, r).setString(unicode_str(v))
        r += 1
    return sheet


def _data_draw(doc, title, formula, rows):
    page = doc.getCurrentController().getCurrentPage()
    shape = doc.createInstance("com.sun.star.drawing.TextShape")
    page.add(shape)
    shape.setSize(Size(12000, 600 + 400 * (len(rows) + 1)))
    shape.setPosition(Point(1000, 1000))
    lines = []
    if title:
        lines.append(title + ((u"  (%s)" % formula) if formula else u""))
    for k, v in rows:
        lines.append(u"%s:  %s" % (k, v))
    shape.setString(u"\n".join(unicode_str(x) for x in lines))
    return shape


# ---------------------------------------------------------------------------
#  Sitnice ovisne o UNO-u (definirane tek kad je UNO prisutan)
# ---------------------------------------------------------------------------
if _UNO:
    from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK

    def unicode_str(x):
        return x if isinstance(x, str) else str(x)
else:
    PARAGRAPH_BREAK = None

    def unicode_str(x):
        return x if isinstance(x, str) else str(x)


if __name__ == "__main__":
    # Izvan LibreOfficea testiramo samo čiste helpere (bez UNO-a).
    assert abs(PX_TO_MM100 - 26.458333) < 1e-4
    assert _svg_dims('<svg width="620" height="420" viewBox="0 0 620 420">') == (620.0, 420.0)
    assert _svg_dims('<svg viewBox="-200 -150 400 300">') == (400.0, 300.0)
    w, h = _size_mm100((600.0, 300.0), width_mm=150)
    assert w == 15000 and h == 7500, (w, h)
    # omjer se čuva točno (ratio 620:420)
    w2, h2 = _size_mm100((620.0, 420.0), width_mm=170)
    assert abs(w2 / h2 - 620.0 / 420.0) < 1e-3, (w2, h2)
    print("insert.py OK — helperi (dimenzije/mjere) rade; UNO dio se testira u LibreOfficeu.")
