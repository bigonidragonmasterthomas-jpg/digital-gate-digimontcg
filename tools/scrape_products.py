#!/usr/bin/env python3
"""Scarica le pagine elenco prodotti ufficiali e salva link + immagini (per i banner della home)."""
import re, json, pathlib, urllib.request, urllib.parse
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
PAGES = ["https://world.digimoncard.com/products/", "https://en.digimoncard.com/products/", "https://digimoncard.com/products/",
         "https://world.digimoncard.com/", "https://digimoncard.com/"]
def get(u):
    try:
        return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR " + str(e)
res = {}
for p in PAGES:
    h = get(p); (out / (re.sub(r"\W+", "_", p) + ".html")).write_text(h)
    items = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        href, inner = m.group(1), m.group(2)
        imgs = re.findall(r'<img[^>]+src="([^"]+)"', inner)
        txt = re.sub(r"<[^>]+>", " ", inner); txt = re.sub(r"\s+", " ", txt).strip()
        if imgs: items.append({"href": urllib.parse.urljoin(p, href), "img": [urllib.parse.urljoin(p, i) for i in imgs], "text": txt[:160]})
    res[p] = items
json.dump(res, open(out / "products.json", "w"), indent=1, ensure_ascii=False)
for p, it in res.items(): print(p, len(it))
