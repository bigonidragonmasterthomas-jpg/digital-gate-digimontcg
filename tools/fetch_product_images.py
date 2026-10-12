#!/usr/bin/env python3
"""Immagini delle confezioni per la scheda prodotto e loghi per l'elenco dei prodotti; confezioni: dal sito ufficiale (indirizzo in "pk" di src/products.json) a www/prod/CODICE.webp."""
import io, json, pathlib, sys, urllib.parse, urllib.request
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "www" / "prod"
outdir.mkdir(parents=True, exist_ok=True)
prod = json.load(open(root / "src" / "products.json", encoding="utf-8"))
done = 0
for k, path in sorted({(p["k"], p["pk"]) for p in prod.values() if p.get("pk")}):
    try:
        data = urllib.request.urlopen(urllib.request.Request(path, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read()
        im = Image.open(io.BytesIO(data)); im.load()
    except Exception as e:
        print("manca", k, e); continue
    im = im.convert("RGBA")
    box = im.getbbox()
    if box: im = im.crop(box)
    if im.size[1] > 340: im = im.resize((round(im.size[0] * 340 / im.size[1]), 340), Image.LANCZOS)
    im.save(outdir / (k + ".webp"), "WEBP", quality=88, method=5)
    done += 1
print("confezioni:", done)
# loghi per l'elenco dei prodotti: dal ramo "set-assets" (percorso in "lg") a www/prod/logo/CODICE.webp
BASE = "https://raw.githubusercontent.com/knightofgemini/digital-gate-digimontcg/set-assets/"
(outdir / "logo").mkdir(exist_ok=True)
done = 0
for k, path in sorted({(p["k"], p["lg"]) for p in prod.values() if p.get("lg")}):
    try:
        data = urllib.request.urlopen(urllib.request.Request(BASE + urllib.parse.quote(path), headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read()
        im = Image.open(io.BytesIO(data)); im.load()
    except Exception as e:
        print("manca logo", k, e); continue
    im = im.convert("RGBA")
    box = im.getbbox()
    if box: im = im.crop(box)
    if im.size[1] > 110: im = im.resize((round(im.size[0] * 110 / im.size[1]), 110), Image.LANCZOS)
    im.save(outdir / "logo" / (k + ".webp"), "WEBP", quality=86, method=5)
    done += 1
print("loghi:", done)
