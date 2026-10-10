#!/usr/bin/env python3
"""AD1: individua le versioni con bordo dorato (= ristampe alternative art) misurando il colore della cornice."""
import json, io, pathlib, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
D = json.load(open(root / "src" / "data.json", encoding="utf-8")); C = D["cards"]
ad = [s for s in D["sets"] if s["id"] == "ad1"][0]
ids = [C[x[0]][0] + x[1] for x in ad["v"] if isinstance(x, list) and x[1]]
SRC = ["https://world.digimoncard.com/images/cardlist/card/{}.png", "https://web-garage.takaotaku.de/{}.webp"]
def get(i):
    for t in SRC:
        try:
            b = urllib.request.urlopen(urllib.request.Request(t.format(i), headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
            im = Image.open(io.BytesIO(b)).convert("RGB")
            return im.resize((430, 600))
        except Exception:
            pass
    return None
def score(im):
    a = np.asarray(im).astype(int)
    # cornice: fasce laterali tra il 30% e il 70% dell'altezza, 4..14 px dal bordo
    strips = np.concatenate([a[180:420, 4:14].reshape(-1, 3), a[180:420, 416:426].reshape(-1, 3)])
    r, g, b = strips[:, 0], strips[:, 1], strips[:, 2]
    gold = (r > 150) & (g > 110) & (b < 0.75 * g) & (r >= g) & (r - b > 60)
    return float(gold.mean())
res = {}; ims = {}
def work(i):
    im = get(i); return i, im, (score(im) if im else None)
with cf.ThreadPoolExecutor(12) as ex:
    for i, im, sc in ex.map(work, ids): res[i] = sc; ims[i] = im
json.dump(res, open(out / "gold.json", "w"), indent=0)
order = sorted(ids, key=lambda i: -(res[i] or 0))
TW, TH, COLS = 130, 182, 10
for n in range(0, len(order), 60):
    ch = order[n:n + 60]
    S = Image.new("RGB", (TW * COLS, (TH + 14) * ((len(ch) + COLS - 1) // COLS)), "white"); d = ImageDraw.Draw(S)
    for k, i in enumerate(ch):
        X, Y = (k % COLS) * TW, (k // COLS) * (TH + 14)
        d.text((X + 2, Y), "%d %s %.2f" % (n + k, i, res[i] or -1), fill="black")
        if ims[i]: S.paste(ims[i].resize((TW - 4, TH - 4)), (X + 2, Y + 12))
    S.save(out / ("gold_%02d.png" % (n // 60)))
print(len(ids), sorted(res.values(), key=lambda v: -(v or 0))[:5])
