#!/usr/bin/env python3
"""Ristampe in AD1: confronta ogni versione con la carta base.
- arte diversa dalla base -> nuova arte (Alternative Art)
- stessa arte, cornice diversa (dorata) -> Ristampa Alternative Art
- stessa arte e cornice -> Ristampa"""
import json, io, pathlib, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
D = json.load(open(root / "src" / "data.json", encoding="utf-8")); C = D["cards"]
ad = [s for s in D["sets"] if s["id"] == "ad1"][0]
ids = [C[x[0]][0] + x[1] for x in ad["v"] if isinstance(x, list) and x[1] and C[x[0]][16] != "ad1"]
bases = sorted({i.split("_P")[0] for i in ids})
SRC = ["https://web-garage.takaotaku.de/{}.webp", "https://world.digimoncard.com/images/cardlist/card/{}.png", "https://en.digimoncard.com/images/cardlist/card/{}.png"]
def get(i):
    for _ in range(3):
        for t in SRC:
            try:
                b = urllib.request.urlopen(urllib.request.Request(t.format(i), headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
                return i, Image.open(io.BytesIO(b)).convert("RGB").resize((215, 300))
            except Exception:
                pass
    return i, None
with cf.ThreadPoolExecutor(12) as ex:
    imgs = dict(ex.map(get, ids + bases))
def arr(im, box): return np.asarray(im.crop(box).filter(ImageFilter.GaussianBlur(2))).astype(float)
ART = (45, 50, 170, 170)
info = {}
for i in ids:
    v, b = imgs.get(i), imgs.get(i.split("_P")[0])
    if v is None or b is None: info[i] = None; continue
    art = float(np.abs(arr(v, ART) - arr(b, ART)).mean())
    fv = np.concatenate([np.asarray(v)[2:8, 30:185].reshape(-1, 3), np.asarray(v)[40:260, 2:7].reshape(-1, 3)]).astype(float)
    fb = np.concatenate([np.asarray(b)[2:8, 30:185].reshape(-1, 3), np.asarray(b)[40:260, 2:7].reshape(-1, 3)]).astype(float)
    fr = float(np.abs(fv.mean(axis=0) - fb.mean(axis=0)).sum())
    cls = "new" if art > 28 else ("gold" if fr > 60 else "same")
    info[i] = {"art": round(art, 1), "frame": round(fr, 1), "cls": cls}
json.dump(info, open(out / "ad1_border.json", "w"), indent=0)
COLS, W, H = 10, 215, 300
items = [(i, imgs.get(i)) for i in ids]
for part in range(0, len(items), 60):
    sub = items[part:part + 60]
    S = Image.new("RGB", (COLS * W, ((len(sub) + COLS - 1) // COLS) * (H + 16)), "white"); d = ImageDraw.Draw(S)
    for k, (i, im) in enumerate(sub):
        X, Y = (k % COLS) * W, (k // COLS) * (H + 16); g = info.get(i)
        d.text((X + 2, Y + 2), "%d %s %s" % (part + k, i, ("%s a%.0f f%.0f" % (g["cls"].upper(), g["art"], g["frame"])) if g else "NONE"), fill="black")
        if im: S.paste(im, (X, Y + 16))
    S.save(out / ("ad1_%02d.png" % (part // 60)))
from collections import Counter
print(len(ids), Counter((v or {}).get("cls") for v in info.values()))
