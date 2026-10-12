#!/usr/bin/env python3
"""Sonda 2: html + css delle pagine prodotto recenti (dove sta il logo?) e campioni ridotti delle immagini candidate."""
import re, io, json, pathlib, urllib.request, urllib.parse, concurrent.futures as cf
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; (out / "html").mkdir(parents=True, exist_ok=True); (out / "s").mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
def get(u, binary=False, t=15):
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        return b if binary else b.decode("utf-8", "replace")
    except Exception:
        return None
W, E, J = "https://world.digimoncard.com", "https://en.digimoncard.com", "https://digimoncard.com"
PAGES = [W + "/products/pack/ver26/", W + "/products/pack/ex-13/", W + "/products/deck/st-24/", W + "/products/pack/ver17/",
         W + "/products/pack/ver9.php", E + "/products/pack/ver15.php", J + "/products/pack/ver26/"]
css_hits = {}
for p in PAGES:
    h = get(p)
    if not h: print("ERR", p); continue
    (out / "html" / ("q_" + re.sub(r"\W+", "_", p)[8:90] + ".html")).write_text(h)
    for c in sorted(set(re.findall(r'href=["\']([^"\']+\.css[^"\']*)', h))):
        cu = urllib.parse.urljoin(p, c)
        if "/products/" not in cu: continue
        ch = get(cu)
        if not ch: continue
        (out / "html" / ("css_" + re.sub(r"\W+", "_", cu)[8:100] + ".css")).write_text(ch)
        css_hits[cu] = sorted(set(urllib.parse.urljoin(cu, m) for m in re.findall(r'url\(\s*["\']?([^"\')]+)', ch)))
json.dump(css_hits, open(out / "css_imgs.json", "w"), indent=1)
for k, v in css_hits.items(): print("CSS", k, len(v)); [print("   ", x) for x in v if re.search(r"logo|tit|mv|kv|ttl", x, re.I)]
# campioni
S = []
for slug in ["pack/ver26", "pack/ex-13", "deck/st-24", "pack/ver17", "pack/ad-01", "pack/ex-06"]:
    S += [W + "/images/products/%s/point/pc/mv.%s" % (slug, "webp" if slug in ("pack/ver26", "pack/ex-13") else "jpg"),
          W + "/images/products/%s/img_pkg.png" % slug]
for slug in ["pack/ver1", "pack/ver5", "pack/ver11", "deck/st-1", "pack/ex-02", "deck/st-25", "pack/ver27", "pack/ver2"]:
    S += [W + "/images/products/%s/bnr.jpg" % slug, W + "/images/products/%s/thumb.png" % slug, W + "/images/products/%s/img_pkg.png" % slug]
S += [E + "/images/products/pack/ver15/bnr.jpg", E + "/images/products/pack/ver15/bnr_special.png", E + "/images/products/pack/rb-01/bnr.jpg",
      E + "/images/products/deck/st-17/bnr.jpg", J + "/images/products/pack/ver12/special/tit_snavi_products.png",
      W + "/images/products/deck/st-15/bnr_special.png", W + "/images/products/goods/tamers-evolution-box/logo.png",
      W + "/images/products/goods/limited-lm-09/img_01.jpg", W + "/images/products/goods/special-limited-set/bnr.jpg",
      W + "/images/products/pack/ver26/thumb.png", W + "/images/products/pack/ex-13/thumb.png", W + "/images/products/deck/st-24/thumb.png"]
# nomi di logo plausibili
for slug in ["pack/ver26", "pack/ex-13", "pack/ver25", "pack/ad-01", "pack/ver17", "pack/ver9"]:
    for n in ["point/pc/logo.png", "point/pc/logo.webp", "point/logo.png", "point/logo.webp", "point/pc/ttl.png", "point/pc/title.png",
              "logo.png", "logo.webp", "img_logo.png", "point/pc/mv_logo.png", "point/img_logo.png", "point/sp/logo.png", "title.png"]:
        S.append(W + "/images/products/%s/%s" % (slug, n))
def one(u):
    b = get(u, True, 15)
    if not b: return u, None
    try:
        im = Image.open(io.BytesIO(b)); size = im.size; mode = im.mode
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (128, 128, 128)); bg.paste(im, mask=im.split()[-1]); im = bg
        else:
            im = im.convert("RGB")
        im.thumbnail((900, 900))
        name = re.sub(r"\W+", "_", u.split("//")[1])[:110] + ".jpg"
        im.save(out / "s" / name, quality=78)
        return u, [size[0], size[1], mode, name]
    except Exception as e:
        return u, ["?", str(e)]
res = {}
with cf.ThreadPoolExecutor(12) as ex:
    for u, r in ex.map(one, S): res[u] = r
json.dump(res, open(out / "samples.json", "w"), indent=1)
for u, r in res.items(): print("S", u, r)
