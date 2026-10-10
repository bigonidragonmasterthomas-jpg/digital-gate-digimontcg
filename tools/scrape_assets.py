#!/usr/bin/env python3
"""Raccoglie materiali promozionali e loghi: unacollezione.it (Digimon) e pagine prodotto ufficiali. Salva immagini e un foglio di anteprima."""
import re, io, json, pathlib, urllib.request, urllib.parse, hashlib
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; (out / "img").mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
def get(u, binary=False):
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=15).read()
        return b if binary else b.decode("utf-8", "replace")
    except Exception as e:
        print("ERR", u, e); return None
pages = ["https://unacollezione.it/tutti-i-set?category=tcg&subcategory=digimon", "https://unacollezione.it/", "https://unacollezione.it/nuove-uscite"]
found = {}
for p in pages:
    h = get(p)
    if not h: continue
    (out / ("una_" + re.sub(r"\W+", "_", p)[-40:] + ".html")).write_text(h)
    for s in re.findall(r'(?:src|data-src|srcset|href|content)="([^"]+)"', h):
        for part in s.split(","):
            u = part.strip().split(" ")[0]
            if re.search(r"\.(png|jpe?g|webp|avif)(\?|$)", u, re.I):
                found[urllib.parse.urljoin(p, u)] = p
    for u in re.findall(r'https?://[^"\'\s)]+\.(?:png|jpe?g|webp|avif)', h): found.setdefault(u, p)
# link alle pagine dei set digimon su unacollezione
links = set()
for p in pages[:1]:
    h = get(p) or ""
    for l in re.findall(r'href="([^"]+)"', h):
        if "digimon" in l.lower(): links.add(urllib.parse.urljoin(p, l))
for l in sorted(links)[:80]:
    h = get(l)
    if not h: continue
    for u in re.findall(r'https?://[^"\'\s)]+\.(?:png|jpe?g|webp|avif)', h): found.setdefault(u, l)
    for s in re.findall(r'(?:src|data-src)="([^"]+)"', h):
        if re.search(r"\.(png|jpe?g|webp|avif)", s, re.I): found.setdefault(urllib.parse.urljoin(l, s), l)
json.dump({"links": sorted(links), "imgs": found}, open(out / "una.json", "w"), indent=1)
print(len(links), "pagine,", len(found), "immagini")
# scarica quelle digimon/bandai/digimoncard
sheet = []
for u, pg in found.items():
    if not re.search(r"digimon|bt-?\d|ex-?\d|st-?\d|bandai", u, re.I): continue
    b = get(u, True)
    if not b: continue
    try:
        im = Image.open(io.BytesIO(b)); im.load()
    except Exception:
        continue
    name = hashlib.md5(u.encode()).hexdigest()[:10] + "_" + re.sub(r"\W+", "_", u.split("/")[-1])[:40]
    (out / "img" / name).write_bytes(b)
    sheet.append((name, u, im.size))
json.dump(sheet, open(out / "una_downloaded.json", "w"), indent=1)
print(len(sheet), "scaricate")
