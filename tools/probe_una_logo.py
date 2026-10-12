#!/usr/bin/env python3
"""Sonda 4: nella pagina set di unacollezione.it c'è un logo diverso dall'imgset? Cerca i campi nel bundle della pagina set
e prova nomi tipo *_logoset.webp."""
import re, pathlib, urllib.request, io
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
def get(u, b=False):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read(); return r if b else r.decode("utf-8", "replace")
    except Exception:
        return None
h = get("https://unacollezione.it/set/digimon_chivalrous_xiii") or ""
(out / "set_ex13.html").write_text(h)
main = re.findall(r'src="(/assets/index-[^"]+\.js)"', h)
js = get("https://unacollezione.it" + main[0]) if main else ""
chunks = sorted(set(re.findall(r'assets/(?:Set|Checklist|SetDetail|Catalog)[A-Za-z0-9_\-]*\.js', js or "")))
print("chunk set:", chunks)
for c in chunks:
    t = get("https://unacollezione.it/" + c) or ""
    for m in re.finditer(r"logoset|logo_set|logoSet|setLogo|logo_url|logoUrl|imgset|mainImage|main_image|imglogo|IMGLOGO", t):
        print("  ", c, "|", t[max(0, m.start() - 140):m.end() + 140].replace("\n", " ")[:300])
# campi presenti nel json incorporato nella pagina
for m in re.finditer(r'"(imgset|logoset|logo|mainImage|main_image|image|img)"\s*:\s*"([^"]+)"', h):
    print("FIELD", m.group(1), m.group(2))
for u in sorted(set(re.findall(r'https://img\.unacollezione\.it/[^"\'\s&<>]+', h))): print("URL", u)
base = "digimon_chivalrous_xiii"
tries = []
for d in ["", "IMGSET/", "LOGOSET/", "LOGO/", "logoset/", "SETLOGO/", "IMGLOGO/"]:
    for n in [base + "_logoset.webp", base + "_logoset.png", base + "_logo.webp", base + "_logo.png", base + ".webp", base + "_imgset_logo.webp"]:
        tries.append("https://img.unacollezione.it/" + d + n)
for u in tries:
    b = get(u, True)
    if b:
        try:
            im = Image.open(io.BytesIO(b)); print("HIT", u, im.size, im.mode)
            (out / ("hit_" + re.sub(r"\W+", "_", u[29:]) + ".png")).write_bytes(b)
        except Exception as e: print("HIT?", u, len(b))
print("fine")
