#!/usr/bin/env python3
"""Sonda 3: scarica l'immagine "imgset" (logo del set) di tutti i set Digimon di unacollezione.it e crea un foglio di prova."""
import re, json, pathlib, urllib.request, io, concurrent.futures as cf
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; (out / "una").mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
def get(u, b=False):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read(); return r if b else r.decode("utf-8", "replace")
    except Exception:
        return None
ids = set()
for p in ["https://unacollezione.it/tutti-i-set?category=tcg&subcategory=digimon", "https://unacollezione.it/category/tcg/digimon", "https://unacollezione.it/tutti-i-set"]:
    h = get(p) or ""
    ids |= set(re.findall(r'/set/(digimon[A-Za-z0-9_\-]*)', h))
print("set digimon:", len(ids))
def one(i):
    h = get("https://unacollezione.it/set/" + i) or ""
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    img = re.search(r'https://img\.unacollezione\.it/IMGSET/[^"\'\s&]+', h)
    u = img.group(0) if img else "https://img.unacollezione.it/IMGSET/%s_imgset.webp" % i
    b = get(u, True)
    if not b: return i, {"title": t.group(1) if t else "", "url": u, "ok": False}
    im = Image.open(io.BytesIO(b)); im.load()
    alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    transp = 0.0
    if alpha:
        a = im.convert("RGBA").split()[-1]; transp = sum(1 for v in a.getdata() if v < 20) / (im.size[0] * im.size[1])
    (out / "una" / (i + ".webp")).write_bytes(b)
    return i, {"title": t.group(1).strip() if t else "", "url": u, "ok": True, "size": im.size, "mode": im.mode, "transp": round(transp, 2)}
res = {}
with cf.ThreadPoolExecutor(10) as ex:
    for i, r in ex.map(one, sorted(ids)): res[i] = r
json.dump(res, open(out / "una_imgset.json", "w"), indent=1, ensure_ascii=False)
for i, r in res.items(): print(i, r)
ok = [i for i, r in res.items() if r["ok"]]
cw, ch, cols = 300, 150, 5
S = Image.new("RGB", (cols * cw, ((len(ok) + cols - 1) // cols) * ch), (40, 40, 48)); d = ImageDraw.Draw(S)
for k, i in enumerate(ok):
    im = Image.open(out / "una" / (i + ".webp")).convert("RGBA"); im.thumbnail((cw - 10, ch - 22))
    x, y = (k % cols) * cw, (k // cols) * ch
    bg = Image.new("RGBA", im.size, (255, 0, 255, 255)); bg.alpha_composite(im)
    S.paste(bg.convert("RGB"), (x + 5, y + 5)); d.text((x + 5, y + ch - 15), i[8:40], fill=(255, 255, 255))
S.save(out / "una_sheet.jpg", quality=75)
import shutil; shutil.rmtree(out / "una")
