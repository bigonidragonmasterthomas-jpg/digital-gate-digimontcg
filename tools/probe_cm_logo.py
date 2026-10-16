"""Cerca il logo/icona ufficiale di Cardmarket sui loro server (per indicare la fonte dei prezzi). Salva in analysis/cmlogo/."""
import os, re, urllib.parse, urllib.request

OUT = "analysis/cmlogo"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36", "Accept": "*/*"}


def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r:
        return r.read(), r.headers.get("Content-Type", "")


cands = [
    "https://www.cardmarket.com/favicon.ico",
    "https://www.cardmarket.com/apple-touch-icon.png",
    "https://www.cardmarket.com/en/Digimon",
    "https://news.cardmarket.com/en/Magic/were-making-the-price-guide-and-product-catalogue-available-for-download",
    "https://help.cardmarket.com/en/cardmarket-api",
    "https://insight.cardmarket.com/en/Insight/Articles/whats-new-on-cardmarket-7-2025",
]
found = set()
for u in cands:
    try:
        b, ct = get(u)
    except Exception as e:
        print("errore", u, e); continue
    print("ok", u, ct, len(b))
    if "html" in ct:
        h = b.decode("utf-8", "replace")
        for m in re.finditer(r'(?:href|src|content)="([^"]+?\.(?:svg|png|ico|webp)(?:\?[^"]*)?)"', h):
            v = urllib.parse.urljoin(u, m.group(1))
            if re.search(r"logo|icon|favicon|apple-touch|cardmarket", v, re.I):
                found.add(v)
    else:
        open(f"{OUT}/" + re.sub(r"\W+", "_", u)[-50:], "wb").write(b)
for v in sorted(found):
    try:
        b, ct = get(v)
        open(f"{OUT}/" + re.sub(r"\W+", "_", v)[-70:], "wb").write(b); print("salvato", v, ct, len(b))
    except Exception as e:
        print("errore", v, e)
