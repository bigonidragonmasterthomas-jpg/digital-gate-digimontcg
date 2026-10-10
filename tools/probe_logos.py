import re, urllib.request, urllib.parse, json, pathlib, io
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent; out = root / "analysis"; (out / "logo").mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
def get(u, b=False):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=12).read(); return r if b else r.decode("utf-8", "replace")
    except Exception: return None
res = {}
# 1) tutte le immagini nelle pagine prodotto (sito JP e world) per alcuni set
for base in ["https://digimoncard.com", "https://world.digimoncard.com", "https://en.digimoncard.com"]:
    for slug in ["pack/ver26/", "pack/ex-13/", "pack/ver25/", "pack/ver27/", "pack/ex-12/", "pack/ad-01/", "pack/ver24/"]:
        h = get(base + "/products/" + slug)
        if not h: continue
        imgs = sorted(set(urllib.parse.urljoin(base + "/products/" + slug, s) for s in re.findall(r'(?:src|data-src|href|srcset)="([^"\s]+\.(?:png|jpe?g|webp|svg)[^"\s]*)"', h)))
        res[base + slug] = [u for u in imgs if re.search(r"logo|tit|title|kv|mv|key|main|visual", u, re.I)]
# 2) prova nomi comuni
cands = ["logo.png", "logo.webp", "img_logo.png", "img_logo.webp", "point/pc/logo.png", "point/logo.png", "point/pc/logo.webp", "img_title.png", "title.png", "point/pc/mv_logo.png", "kv.jpg", "kv.png", "img_kv.jpg", "point/pc/kv.jpg", "point/pc/mv_bg.jpg", "point/pc/bg.jpg", "point/sp/mv.jpg", "point/sp/mv.webp"]
hits = []
for base in ["https://world.digimoncard.com", "https://digimoncard.com"]:
    for slug in ["pack/ver26/", "pack/ex-13/", "pack/ver25/", "pack/ver27/", "pack/ad-01/"]:
        for c in cands:
            u = base + "/images/products/" + slug + c
            b = get(u, True)
            if b:
                try:
                    im = Image.open(io.BytesIO(b)); hits.append([u, im.size, im.mode])
                    (out / "logo" / re.sub(r"\W+", "_", u.split("products/")[1])).write_bytes(b)
                except Exception: pass
json.dump({"pages": res, "hits": hits}, open(out / "logos.json", "w"), indent=1)
print(json.dumps(hits, indent=0)); print(json.dumps(res, indent=0)[:6000])
