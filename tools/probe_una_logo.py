#!/usr/bin/env python3
"""Sonda: dove prende unacollezione.it il logo dell'espansione nella scheda carta? (html grezzo + bundle js)"""
import re, json, pathlib, urllib.request, urllib.parse
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
def get(u, b=False):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read(); return r if b else r.decode("utf-8", "replace")
    except Exception as e:
        print("ERR", u, e); return None
pages = ["https://unacollezione.it/carta/b64_NDkyMTY1X0JUMTItMDAx", "https://unacollezione.it/set/digimon_across_time"]
res = {}
for p in pages:
    h = get(p) or ""
    (out / (re.sub(r"\W+", "_", p)[-40:] + ".html")).write_text(h)
    urls = sorted(set(re.findall(r'https?://[^"\'\s)<>\\]+', h)))
    res[p] = {"len": len(h), "img": [u for u in urls if re.search(r"img\.unacollezione|logo|LOGO|IMGSET|\.(png|webp|svg|jpg)", u)],
              "ctx": [h[max(0, m.start() - 200):m.end() + 200] for m in re.finditer(r"logo|LOGO|IMGSET|img\.unacollezione", h)][:30]}
    scripts = sorted(set(urllib.parse.urljoin(p, s) for s in re.findall(r'<script[^>]+src="([^"]+)"', h)))
    res[p]["scripts"] = scripts
    for s in scripts:
        if "unacollezione" not in s: continue
        js = get(s) or ""
        hits = [js[max(0, m.start() - 250):m.end() + 250] for m in re.finditer(r"[Ll][Oo][Gg][Oo]|IMGSET|img\.unacollezione", js)]
        res[p].setdefault("js", {})[s] = hits[:40]
json.dump(res, open(out / "una_logo.json", "w"), indent=1, ensure_ascii=False)
for p, r in res.items():
    print("PAGE", p, r["len"]); [print("  IMG", u) for u in r["img"]]
    for c in r["ctx"]: print("  CTX", c.replace("\n", " ")[:450])
    for s, hs in r.get("js", {}).items():
        print("  JS", s, len(hs))
        for x in hs[:25]: print("     ", x.replace("\n", " ")[:520])
