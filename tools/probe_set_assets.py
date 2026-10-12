#!/usr/bin/env python3
"""Sonda: elenca tutte le pagine prodotto ufficiali (world, en, jp) e le immagini di ciascuna, per capire
dove stanno loghi e key visual delle espansioni. Output in analysis/."""
import re, io, json, pathlib, urllib.request, urllib.parse, concurrent.futures as cf
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; (out / "html").mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
def get(u, binary=False, t=15):
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        return b if binary else b.decode("utf-8", "replace")
    except Exception as e:
        return None
SITES = ["https://world.digimoncard.com", "https://en.digimoncard.com", "https://digimoncard.com"]
LIST = ["/products/", "/products/pack/", "/products/deck/", "/products/goods/", "/products/?category=pack",
        "/products/index.php?cat=pack", "/products/pack.php", "/products/deck.php", "/products/goods.php"]
IMG_RE = r'(?:src|data-src|data-original|href|content|srcset|data-bg)=["\']([^"\']+?\.(?:png|jpe?g|webp|svg|gif)(?:\?[^"\'\s]*)?)'
def imgs_of(page, h):
    s = set()
    for m in re.findall(IMG_RE, h, re.I):
        for part in m.split(","):
            p = part.strip().split(" ")[0]
            if p: s.add(urllib.parse.urljoin(page, p))
    for m in re.findall(r'url\(\s*["\']?([^"\')]+\.(?:png|jpe?g|webp|svg))', h, re.I):
        s.add(urllib.parse.urljoin(page, m))
    return sorted(s)
listing = {}; prod = set()
for site in SITES:
    for l in LIST:
        u = site + l; h = get(u)
        if not h: listing[u] = None; continue
        (out / "html" / (re.sub(r"\W+", "_", u)[8:80] + ".html")).write_text(h)
        links = sorted(set(urllib.parse.urljoin(u, x) for x in re.findall(r'href=["\']([^"\']+)["\']', h)))
        pl = [x for x in links if re.search(r"/products/(pack|deck|goods|other|premium)[^\"']*", x) and x.split("#")[0].rstrip("/") != u.rstrip("/")]
        listing[u] = {"len": len(h), "links": pl, "imgs": imgs_of(u, h)}
        for x in pl:
            x = x.split("#")[0].split("?")[0]
            if re.search(r"/products/(pack|deck|goods)/.+", x): prod.add(x)
print("pagine prodotto:", len(prod), flush=True)
def page(u):
    h = get(u)
    if not h: return u, None
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    og = re.findall(r'property=["\']og:image["\']\s+content=["\']([^"\']+)', h)
    return u, {"title": t.group(1).strip() if t else "", "og": og, "imgs": imgs_of(u, h)}
pages = {}
with cf.ThreadPoolExecutor(10) as ex:
    for u, r in ex.map(page, sorted(prod)): pages[u] = r
# salva l'html di qualche pagina d'esempio
for u in [p for p in sorted(prod) if re.search(r"(ver27|bt-?01|ex-01|ex-13|st-1/|st-01|rb-01|ad-01|lm-0)", p)][:8]:
    h = get(u)
    if h: (out / "html" / ("p_" + re.sub(r"\W+", "_", u)[8:90] + ".html")).write_text(h)
# dimensioni delle immagini che sembrano loghi / key visual
cand = sorted({i for r in pages.values() if r for i in r["imgs"] + r["og"]
               if re.search(r"logo|tit|kv|mv|bnr|banner|key|main|visual|img_0?1|image_product|ogp", i, re.I) and "/images/" in i})
def size(u):
    b = get(u, True, 12)
    if not b: return u, None
    try:
        im = Image.open(io.BytesIO(b)); return u, [im.size[0], im.size[1], im.mode, len(b)]
    except Exception:
        return u, ["?", len(b)]
sizes = {}
with cf.ThreadPoolExecutor(12) as ex:
    for u, r in ex.map(size, cand): sizes[u] = r
json.dump({"listing": listing, "pages": pages, "sizes": sizes}, open(out / "set_assets_probe.json", "w"), indent=1, ensure_ascii=False)
for u, l in listing.items(): print("LIST", u, None if l is None else (l["len"], len(l["links"]), len(l["imgs"])))
for u, r in pages.items():
    if r is None: print("ERR", u); continue
    loc = [i.split("/images/")[-1] for i in r["imgs"] if "/images/products/" in i]
    print("PAGE", u, "|", r["title"][:60], "|", len(r["imgs"]), "|", " ".join(loc)[:400])
print("candidati", len(cand))
for u, s in sizes.items(): print("SIZE", u, s)
