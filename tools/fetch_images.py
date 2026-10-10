#!/usr/bin/env python3
"""Scarica le immagini delle carte (fonte ufficiale HD, ripiego Taka) e crea miniature + versione grande in www/img/{t,f}.
Incrementale: salta i file già presenti (la cache di GitHub Actions li conserva fra un'esecuzione e l'altra)."""
import json, io, pathlib, urllib.request, urllib.parse, concurrent.futures as cf, sys
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "www" / "img"
(out / "t").mkdir(parents=True, exist_ok=True); (out / "f").mkdir(parents=True, exist_ok=True)
codes = [c[0] for c in json.load(open(root / "src" / "data.json", encoding="utf-8"))["cards"]]
SRC = ["https://world.digimoncard.com/images/cardlist/card/{}.png", "https://en.digimoncard.com/images/cardlist/card/{}.png",
       "https://web-garage.takaotaku.de/{}.webp"]
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 digimon-set-tracker"})
    return urllib.request.urlopen(req, timeout=30).read()
def one(code):
    t, f = out / "t" / (code + ".webp"), out / "f" / (code + ".webp")
    if t.exists() and f.exists(): return "cache"
    q = urllib.parse.quote(code)
    for tpl in SRC:
        for _ in range(2):
            try:
                im = Image.open(io.BytesIO(get(tpl.format(q)))).convert("RGB")
                a = im.copy(); a.thumbnail((480, 672)); a.save(f, "WEBP", quality=80, method=4)
                b = im.copy(); b.thumbnail((120, 168)); b.save(t, "WEBP", quality=75, method=4)
                return "ok"
            except Exception:
                pass
    return "manca"
res = {}
with cf.ThreadPoolExecutor(12) as ex:
    for code, r in zip(codes, ex.map(one, codes)): res[code] = r
from collections import Counter
cnt = Counter(res.values()); print(cnt)
miss = [c for c, r in res.items() if r == "manca"]
print("::notice title=Immagini::%d carte, %d con immagine, %d senza. Esempi mancanti: %s" % (len(res), len(res) - len(miss), len(miss), " ".join(miss[:25])))
print("senza immagine:", [c for c, r in res.items() if r == "manca"][:40])
