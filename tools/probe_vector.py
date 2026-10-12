#!/usr/bin/env python3
"""Prova: vettorializza alcuni loghi del branch set-assets con vtracer e crea un confronto originale / SVG."""
import subprocess, sys, os, io, pathlib
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "vtracer", "cairosvg"], check=True)
import vtracer, cairosvg
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis" / "vec"; out.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", "set-assets"], check=True, cwd=root)
codes = ["BT26", "EX13", "BT9", "ST1", "EX6", "BT13"]
rows = []
for c in codes:
    b = subprocess.run(["git", "show", "FETCH_HEAD:%s/logo.webp" % c], capture_output=True, cwd=root).stdout
    im = Image.open(io.BytesIO(b)).convert("RGBA"); png = out / (c + ".png"); im.save(png)
    svg = out / (c + ".svg")
    vtracer.convert_image_to_svg_py(str(png), str(svg), colormode="color", hierarchical="stacked", mode="spline",
                                    filter_speckle=4, color_precision=7, layer_difference=10, corner_threshold=60,
                                    length_threshold=4.0, max_iterations=10, splice_threshold=45, path_precision=2)
    W = 900; H = round(im.size[1] * W / im.size[0])
    r = Image.open(io.BytesIO(cairosvg.svg2png(url=str(svg), output_width=W, output_height=H))).convert("RGBA")
    o = im.resize((W, H), Image.LANCZOS)
    print(c, "webp %d KB -> svg %d KB, tracciati %d" % (len(b) // 1024, os.path.getsize(svg) // 1024, svg.read_text().count("<path")))
    rows.append((c, o, r))
    # dettaglio ingrandito 3x della parte centrale
    cx, cy = im.size[0] // 2, im.size[1] // 2
    z = im.crop((cx - 120, cy - 60, cx + 120, cy + 60)).resize((720, 360), Image.NEAREST)
    zr = Image.open(io.BytesIO(cairosvg.svg2png(url=str(svg), output_width=im.size[0] * 3, output_height=im.size[1] * 3))).convert("RGBA")
    zr = zr.crop((cx * 3 - 360, cy * 3 - 180, cx * 3 + 360, cy * 3 + 180))
    rows.append((c + " zoom", z, zr))
bgc = (40, 40, 48, 255)
S = Image.new("RGBA", (1830, sum(max(o.size[1], r.size[1]) + 30 for _, o, r in rows)), bgc); d = ImageDraw.Draw(S); y = 0
for n, o, r in rows:
    d.text((10, y + 4), n + "   originale (sinistra)  /  vettoriale (destra)", fill=(255, 255, 255)); y += 20
    for x, im in ((10, o), (920, r)):
        S.alpha_composite(im, (x, y))
    y += max(o.size[1], r.size[1]) + 10
S.convert("RGB").save(root / "analysis" / "vec_confronto.jpg", quality=82)
