#!/usr/bin/env python3
"""Scarica gli artwork promozionali ufficiali (banner) per la home e li salva in www/banners/CODICE.webp.
Le immagini piccole vengono ingrandite (Lanczos) e rese più nitide; tutte ridotte a max 1600 px di larghezza."""
import io, json, pathlib, sys, urllib.request
from PIL import Image, ImageFilter, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "www" / "banners"
outdir.mkdir(parents=True, exist_ok=True)
BASES = ["https://world.digimoncard.com/images/products/", "https://en.digimoncard.com/images/products/", "https://digimoncard.com/images/products/"]
src = json.load(open(root / "tools" / "banners.json"))
info = {}
for code, path in src.items():
    im = None
    for b in BASES:
        try:
            data = urllib.request.urlopen(urllib.request.Request(b + path, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read()
            im = Image.open(io.BytesIO(data)); im.load(); break
        except Exception:
            pass
    if im is None:
        print("manca", code); continue
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (11, 17, 32)); bg.paste(im, mask=im.split()[-1]); im = bg
    else:
        im = im.convert("RGB")
    w0, h0 = im.size
    if w0 < 1200:
        f = min(2.0, 1600 / w0)
        im = im.resize((round(w0 * f), round(h0 * f)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    if im.size[0] > 1600:
        im = im.resize((1600, round(im.size[1] * 1600 / im.size[0])), Image.LANCZOS)
    im.save(outdir / (code + ".webp"), "WEBP", quality=86, method=5)
    info[code] = {"w": im.size[0], "h": im.size[1], "orig": [w0, h0]}
    print(code, (w0, h0), "->", im.size)
json.dump(info, open(outdir / "banners.json", "w"))
