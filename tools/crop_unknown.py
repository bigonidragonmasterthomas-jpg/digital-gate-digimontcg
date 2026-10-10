#!/usr/bin/env python3
"""Fogli di controllo con l'angolo in basso a destra (ingrandito) per le carte da verificare a mano."""
import io, sys, pathlib, urllib.request, concurrent.futures as cf
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
ids = (root / "tools" / "unknown_ids.txt").read_text().split()
SRC = ["https://web-garage.takaotaku.de/{}.webp", "https://world.digimoncard.com/images/cardlist/card/{}.png"]
def get(i):
    best = None
    for t in SRC:
        try:
            b = urllib.request.urlopen(urllib.request.Request(t.format(i), headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
            im = Image.open(io.BytesIO(b)).convert("RGB")
            if best is None or im.size[0] > best.size[0]: best = im
        except Exception:
            pass
    return i, best
with cf.ThreadPoolExecutor(10) as ex:
    res = list(ex.map(get, ids))
CW, CH, COLS, ROWS = 380, 470, 5, 3
crops = []
for i, im in res:
    if im is None: crops.append((i, None)); continue
    W, H = im.size
    c = im.crop((int(W * 0.56), int(H * 0.62), W, H)).resize((CW - 6, CH - 22), Image.LANCZOS)
    crops.append((i, c))
per = COLS * ROWS
for n in range(0, len(crops), per):
    S = Image.new("RGB", (CW * COLS, CH * ROWS), "white"); d = ImageDraw.Draw(S)
    for k, (i, c) in enumerate(crops[n:n + per]):
        X, Y = (k % COLS) * CW, (k // COLS) * CH
        d.text((X + 3, Y + 3), "%d %s" % (n + k, i), fill="black")
        if c is not None: S.paste(c, (X + 3, Y + 18))
    S.save(out / ("unk_%02d.png" % (n // per)))
print(len(ids), "carte;", sum(1 for _, c in crops if c is None), "senza immagine")
