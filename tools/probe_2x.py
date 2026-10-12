#!/usr/bin/env python3
"""Prova: ingrandimento 2x classico (Lanczos + leggera nitidezza, senza AI) di 4 bustine vecchie, con confronto."""
import subprocess, sys, pathlib, io, functools
sys.stderr = sys.stdout
from PIL import Image, ImageDraw, ImageFilter
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis" / "2x"; out.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", "set-assets"], check=True, cwd=root)
codes = ["BT5", "BT10", "EX2", "ST1"]


def up2(im):
    im = im.convert("RGBA")
    w, h = im.size
    rgb = im.convert("RGB").resize((w * 2, h * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    a = im.split()[-1].resize((w * 2, h * 2), Image.LANCZOS)
    rgb.putalpha(a)
    return rgb


rows = []
for c in codes:
    b = subprocess.run(["git", "show", "FETCH_HEAD:%s/confezione.png" % c], capture_output=True, cwd=root).stdout
    o = Image.open(io.BytesIO(b)).convert("RGBA")
    big = up2(o)
    big.save(out / ("%s-confezione-2x.webp" % c), "WEBP", quality=92, method=6)
    o.save(out / ("%s-confezione.png" % c))
    print(c, o.size, "->", big.size)
    H = 700
    rows.append((c, o.resize((round(o.size[0] * H / o.size[1]), H), Image.BILINEAR), big.resize((round(big.size[0] * H / big.size[1]), H), Image.LANCZOS)))
W = sum(l.size[0] + r.size[0] + 40 for _, l, r in rows)
S = Image.new("RGBA", (W, 740), (40, 40, 48, 255)); d = ImageDraw.Draw(S); x = 0
for c, l, r in rows:
    d.text((x + 5, 5), c + "  originale come lo ingrandisce il browser  /  file 2x", fill=(255, 255, 255))
    S.alpha_composite(l, (x, 30)); S.alpha_composite(r, (x + l.size[0] + 10, 30)); x += l.size[0] + r.size[0] + 40
S.convert("RGB").save(root / "analysis" / "confronto_2x.jpg", quality=90)
