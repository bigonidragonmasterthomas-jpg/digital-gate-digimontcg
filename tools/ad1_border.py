#!/usr/bin/env python3
"""Per le ristampe in AD1: misura il colore del bordo esterno della carta (dorato = alternative art) e crea un foglio di controllo."""
import json, io, pathlib, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
D = json.load(open(root / "src" / "data.json", encoding="utf-8")); C = D["cards"]
ad = [s for s in D["sets"] if s["id"] == "ad1"][0]
ids = [C[x[0]][0] + x[1] for x in ad["v"] if isinstance(x, list) and x[1] and C[x[0]][16] != "ad1"]
SRC = ["https://web-garage.takaotaku.de/{}.webp", "https://world.digimoncard.com/images/cardlist/card/{}.png"]
def get(i):
    for t in SRC:
        try:
            b = urllib.request.urlopen(urllib.request.Request(t.format(i), headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
            im = Image.open(io.BytesIO(b)).convert("RGB").resize((215, 300))
            return i, im
        except Exception:
            pass
    return i, None
with cf.ThreadPoolExecutor(12) as ex:
    res = list(ex.map(get, ids))
info = {}
for i, im in res:
    if im is None: info[i] = None; continue
    a = np.asarray(im).astype(int)
    strip = np.concatenate([a[60:240, 2:7].reshape(-1, 3), a[60:240, -7:-2].reshape(-1, 3)])
    r, g, b = strip.mean(axis=0)
    gold = (r - b) > 45 and r > 120
    info[i] = {"rgb": [int(r), int(g), int(b)], "gold": bool(gold)}
json.dump(info, open(out / "ad1_border.json", "w"), indent=0)
COLS = 10; W, H = 215, 300
rows = (len(res) + COLS - 1) // COLS
for part in range(0, rows, 6):
    sub = res[part * COLS:(part + 6) * COLS]
    S = Image.new("RGB", (COLS * W, ((len(sub) + COLS - 1) // COLS) * (H + 16)), "white"); d = ImageDraw.Draw(S)
    for k, (i, im) in enumerate(sub):
        X, Y = (k % COLS) * W, (k // COLS) * (H + 16)
        g = info.get(i)
        d.text((X + 2, Y + 2), "%d %s %s" % (part * COLS + k, i, "GOLD" if g and g["gold"] else "-"), fill="black")
        if im: S.paste(im, (X, Y + 16))
    S.save(out / ("ad1_%02d.png" % (part // 6)))
print(len(ids), "versioni;", sum(1 for v in info.values() if v and v["gold"]), "dorate;", sum(1 for v in info.values() if v is None), "senza immagine")
