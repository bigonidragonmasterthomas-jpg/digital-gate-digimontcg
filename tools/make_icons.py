#!/usr/bin/env python3
"""Rigenera tutte le icone (sito, PWA, iOS, favicon, risorse Capacitor/Android) dai master SVG in src/icons/.

Unica sorgente: src/icons/digital-gate-mark.svg (variante "Cornice ciano").
Richiede Playwright con Chromium (solo in locale, non serve in GitHub Actions: i PNG sono già nel repository).
"""
import base64, io, pathlib
from PIL import Image
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).resolve().parent.parent
ic = root / "src" / "icons"
mark = (ic / "digital-gate-mark.svg").read_text(encoding="utf-8")
body = mark.split(">", 1)[1].rsplit("</svg>", 1)[0]          # contenuto del marchio (viewBox 320)
NAVY = "#0b1120"


def canvas(size, bg=None, scale=1.0, rx=0):
    """SVG quadrato `size`, marchio centrato che occupa `scale` del lato, fondo opzionale."""
    s = size / 320 * scale
    off = (size - 320 * s) / 2
    rect = f'<rect width="{size}" height="{size}" rx="{rx}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" fill="none" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'{rect}<g transform="translate({off:.3f} {off:.3f}) scale({s:.5f})">{body}</g></svg>')


def file_svg(name):
    return (ic / name).read_text(encoding="utf-8")


def render(page, svg, w, h=None):
    h = h or w
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(f'<html><body style="margin:0;background:transparent">'
                     f'<img src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}" width="{w}" height="{h}" style="display:block"></body></html>')
    page.wait_for_load_state("load")
    return Image.open(io.BytesIO(page.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h}))).convert("RGBA")


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    app, mask, comp = file_svg("digital-gate-app.svg"), file_svg("digital-gate-maskable.svg"), file_svg("digital-gate-compact.svg")
    # sito / PWA
    render(pg, app, 192).save(root / "src" / "icon-192.png", optimize=True)
    render(pg, app, 512).save(root / "src" / "icon-512.png", optimize=True)
    render(pg, mask, 512).save(root / "src" / "icon-maskable-512.png", optimize=True)
    # iOS: quadrato pieno (gli angoli li arrotonda il sistema), stesso margine dell'icona dell'app
    render(pg, canvas(180, NAVY, 0.7734), 180).convert("RGB").save(root / "src" / "apple-touch-icon.png", optimize=True)
    # favicon: glifo compatto (D + Digi-Egg), leggibile a 16 px
    favs = [render(pg, comp, n) for n in (16, 32, 48)]
    favs[1].save(root / "src" / "favicon-32.png", optimize=True)
    favs[2].save(root / "src" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=favs[:2])
    # Capacitor (@capacitor/assets): icone e splash nativo; le icone adattive vere sono in android-res/
    a = root / "assets"
    render(pg, canvas(1024, NAVY, 0.7734), 1024).convert("RGB").save(a / "icon-only.png", optimize=True)
    render(pg, canvas(1024, None, 0.704), 1024).save(a / "icon-foreground.png", optimize=True)
    Image.new("RGB", (1024, 1024), NAVY).save(a / "icon-background.png", optimize=True)
    sp = render(pg, canvas(2732, NAVY, 0.235), 2732).convert("RGB")
    sp.save(a / "splash.png", optimize=True)
    sp.save(a / "splash-dark.png", optimize=True)
    b.close()
print("icone rigenerate")
