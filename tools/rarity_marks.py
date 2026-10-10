#!/usr/bin/env python3
"""Analisi delle versioni alternative: individua la riga della rarità (accanto al tag del numero di set)
e prepara fogli di controllo con le strisce ingrandite, più una stima automatica del simbolo (★, ★★, SP)."""
import json, io, sys, pathlib, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
D = json.load(open(root / "src" / "data.json", encoding="utf-8"))
C = D["cards"]
ids = []
for s in D["sets"]:
    for x in s.get("v", []):
        if isinstance(x, list) and x[1]:
            i = C[x[0]][0] + x[1]
            if i not in ids: ids.append(i)
SRC = ["https://world.digimoncard.com/images/cardlist/card/{}.png", "https://web-garage.takaotaku.de/{}.webp"]
def get(i):
    for t in SRC:
        try:
            b = urllib.request.urlopen(urllib.request.Request(t.format(i), headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
            im = Image.open(io.BytesIO(b)).convert("RGB")
            if im.size[0] != 430: im = im.resize((430, round(im.size[1] * 430 / im.size[0])), Image.LANCZOS)
            return im
        except Exception:
            pass
    return None
def find_tag(a):
    H = a.shape[0]; y0 = int(H * 0.55)
    reg = a[y0:int(H * 0.97), 360:415]
    bright = (reg.min(axis=2) > 170) & (reg.max(axis=2) - reg.min(axis=2) < 90)
    lab, n = ndi.label(bright); best = None
    for k, sl in enumerate(ndi.find_objects(lab), 1):
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        if 7 <= h <= 15 and 15 <= w <= 32:
            sub = reg[sl]; dark = int((sub.max(axis=2) < 110).sum())
            # il tag è isolato: attorno (cornice di 3 px) pochi pixel chiari
            ys, ye = max(0, sl[0].start - 3), sl[0].stop + 3; xs, xe = max(0, sl[1].start - 3), sl[1].stop + 3
            ring = bright[ys:ye, xs:xe].sum() - (lab[sl] == k).sum()
            if dark >= 6 and (best is None or dark > best[3]): best = (sl[0].start + y0, sl[1].start + 360, h, dark)
    return best
def guess(a, t):
    y, x, h, _ = t
    z = a[y:y + h, 330:x - 12]
    med = np.median(z.reshape(-1, 3), axis=0)
    fg = (np.abs(z - med).sum(axis=2) > 120)
    lab, n = ndi.label(fg)
    comps = [sl for k, sl in enumerate(ndi.find_objects(lab), 1) if (lab[sl] == k).sum() >= 4]
    if not comps: return ""
    wide = max(sl[1].stop - sl[1].start for sl in comps)
    if wide >= 9: return "SP"
    return "★★" if len(comps) >= 2 else "★"
res = {}
def work(i):
    im = get(i)
    if im is None: return i, None, None
    a = np.asarray(im).astype(int); t = find_tag(a)
    if t is None:
        strip = im.crop((290, int(im.size[1] * 0.60), 430, int(im.size[1] * 0.97)))
        return i, "?", strip
    y, x, h, _ = t
    strip = im.crop((318, max(0, y - 16), x + 30, y + h + 3))
    return i, guess(a, t), strip
with cf.ThreadPoolExecutor(12) as ex:
    done = list(ex.map(work, ids))
strips = []
for i, g, s in done:
    res[i] = g
    if s is not None: strips.append((i, g, s))
json.dump(res, open(out / "guess.json", "w"), ensure_ascii=False, indent=0)
# fogli: 6 colonne, strisce ingrandite x3
CW, CH, PER = 330, 120, 66
for n in range(0, len(strips), PER):
    chunk = strips[n:n + PER]
    W = Image.new("RGB", (CW * 6, CH * ((len(chunk) + 5) // 6)), "white"); d = ImageDraw.Draw(W)
    for k, (i, g, s) in enumerate(chunk):
        s3 = s.resize((min(CW - 4, s.size[0] * 3), min(CH - 18, s.size[1] * 3)), Image.LANCZOS)
        X, Y = (k % 6) * CW, (k // 6) * CH
        W.paste(s3, (X + 2, Y + 16)); d.text((X + 3, Y + 2), "%d %s [%s]" % (n + k, i, (g or "-").replace("\u2605", "*")), fill="black")
    W.save(out / ("sheet_%02d.png" % (n // PER)))
print(len(ids), "versioni;", sum(1 for v in res.values() if v is None), "senza immagine;", sum(1 for v in res.values() if v == "?"), "senza riga")
from collections import Counter; print(Counter(res.values()))
