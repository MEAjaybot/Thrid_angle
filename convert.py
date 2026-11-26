import os
import re
import time
import TechDrawGui
import FreeCADGui as Gui
from PySide import QtGui, QtSvg, QtCore, QtWidgets

LINE_BOOST = 2.0    # multiply line widths (try 1.5 to 4)
MIN_WIDTH = 0.5     # thinnest allowed line, in SVG units
KEEP_SVG = False    # keep the .svg next to the .png while testing
WAIT_SECONDS = 3.0  # time for view geometry to finish before export


def get_page(doc):
    return next((o for o in doc.Objects
                 if o.TypeId == "TechDraw::DrawPage"), None)


def refresh_and_wait(doc, page, seconds=WAIT_SECONDS):
    for v in page.Views:
        v.touch()
    doc.recompute()
    page.ViewObject.doubleClicked()
    end = time.time() + seconds
    while time.time() < end:
        QtWidgets.QApplication.processEvents()
        Gui.updateGui()
        time.sleep(0.05)
    doc.recompute()
    Gui.updateGui()


def page_to_svg(doc, svg_path):
    """Step 1: TechDraw page -> SVG file."""
    page = get_page(doc)
    if page is None:
        return False
    os.makedirs(os.path.dirname(svg_path), exist_ok=True)
    refresh_and_wait(doc, page)
    TechDrawGui.exportPageAsSvg(page, svg_path)
    return os.path.isfile(svg_path)


def _thicken(text):
    def fix(m):
        w = max(float(m.group(2)) * LINE_BOOST, MIN_WIDTH)
        return m.group(1) + ("%.3f" % w)
    text = re.sub(r'(stroke-width\s*:\s*)([\d.]+)', fix, text)
    text = re.sub(r'(stroke-width\s*=\s*")([\d.]+)', fix, text)
    return text


def svg_to_png(svg_path, png_path, dpi=300):
    """Step 2: SVG file -> PNG file."""
    with open(svg_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    tmp = svg_path + ".tmp.svg"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(_thicken(text))

    try:
        renderer = QtSvg.QSvgRenderer(tmp)
        if not renderer.isValid():
            raise RuntimeError("SVG could not be loaded: " + svg_path)

        size = renderer.defaultSize()
        scale = dpi / 96.0
        w = max(int(size.width() * scale), 1)
        h = max(int(size.height() * scale), 1)

        img = QtGui.QImage(w, h, QtGui.QImage.Format_ARGB32)
        img.fill(QtGui.QColor("white"))

        p = QtGui.QPainter(img)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        renderer.render(p, QtCore.QRectF(0, 0, w, h))
        p.end()

        if not img.save(png_path):
            raise RuntimeError("Could not save PNG: " + png_path)
    finally:
        os.remove(tmp)


def page_to_png(doc, png_path, dpi=300):
    """Both steps together. Keeps the SVG if KEEP_SVG is True."""
    svg_path = os.path.splitext(png_path)[0] + ".svg"
    os.makedirs(os.path.dirname(png_path), exist_ok=True)

    if not page_to_svg(doc, svg_path):
        return False
    svg_to_png(svg_path, png_path, dpi)
    if not KEEP_SVG:
        os.remove(svg_path)
    return True