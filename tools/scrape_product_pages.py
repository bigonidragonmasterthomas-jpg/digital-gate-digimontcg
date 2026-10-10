#!/usr/bin/env python3
"""Per ogni pagina prodotto: immagini /images/products/ con dimensioni + testo con la data di uscita."""
import re, io, json, pathlib, urllib.request, urllib.parse
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
W = "https://world.digimoncard.com"; J = "https://digimoncard.com"
PAGES = [W + p for p in ["/products/pack/ver27/", "/products/deck/st-25/", "/products/deck/st-26/", "/products/goods/limited-lm-09.php",
  "/products/goods/nexus-of-digimon/", "/products/goods/selection-box-verx-antibody.php", "/products/goods/story-time-stranger-set.php",
  "/products/goods/royal-knights.php", "/products/goods/seven-great-demon-lords.php", "/products/pack/ex-13/", "/products/pack/ver26/",
  "/products/pack/ex-12/", "/products/pack/ver25/", "/products/pack/ad-01/", "/products/deck/st-24/", "/products/deck/st-23/", "/products/deck/st-22/",
  "/products/pack/ver24/", "/products/pack/ex-11/", "/products/goods/limited-lm-08.php", "/products/goods/limited-lm-07.php",
  "/products/goods/premium-heroines-set-02.php", "/products/goods/liberator-debuggers-set.php", "/products/pack/ver23/", "/products/pack/ex-10/"]] + \
  [J + p for p in ["/products/", "/products/pack/ex-14/", "/products/pack/ver28/", "/products/pack/ver27/"]]
def get(u, binary=False):
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=12).read()
        return b if binary else b.decode("utf-8", "replace")
    except Exception as e:
        return None
res = {}
for p in PAGES:
    h = get(p)
    if h is None: res[p] = "ERR"; continue
    imgs = []
    for s in dict.fromkeys(re.findall(r'(?:src|data-src|href)="([^"]+\.(?:png|jpg|jpeg|webp)[^"]*)"', h)):
        u = urllib.parse.urljoin(p, s)
        if "/images/products/" not in u: continue
        imgs.append([u, None])
    txt = re.sub(r"<[^>]+>", " ", h); txt = re.sub(r"\s+", " ", txt)
    dates = re.findall(r"[^.]{0,80}(?:Release|release|発売|Date|date|Ship|ship)[^.]{0,120}", txt)[:8]
    title = re.search(r"<title>(.*?)</title>", h, re.S)
    print(p, len(imgs), flush=True)
    res[p] = {"title": title.group(1).strip() if title else "", "dates": dates, "imgs": imgs}
json.dump(res, open(out / "pages.json", "w"), indent=1, ensure_ascii=False)
print("ok")
