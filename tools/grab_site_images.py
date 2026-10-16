"""Copia dal sito pubblicato le immagini (grandi e miniature) delle carte di un prodotto, per le anteprime locali.
Uso: python3 tools/grab_site_images.py EX13"""
import json, os, sys, urllib.request

SITE = "https://knightofgemini.github.io/digital-gate-digimontcg/img/"
code = sys.argv[1].upper()
d = json.load(open("src/data.json"))
s = [x for x in d["sets"] if x["code"].upper() == code][0]
keys = set()
for v in s["v"]:
    c = d["cards"][v if isinstance(v, int) else v[0]]
    keys.add(c[0] if isinstance(v, int) else c[0] + v[1])
n = 0
for kind in ("f", "t"):
    os.makedirs(f"analysis/img/{kind}", exist_ok=True)
    for k in sorted(keys):
        try:
            with urllib.request.urlopen(SITE + f"{kind}/{k}.webp", timeout=30) as r:
                open(f"analysis/img/{kind}/{k}.webp", "wb").write(r.read()); n += 1
        except Exception as e:
            print("errore", kind, k, e)
print("immagini", n)
