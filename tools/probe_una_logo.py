#!/usr/bin/env python3
"""Sonda 2: cerca nei bundle js di unacollezione.it come costruisce l'URL del logo del set, e prova nomi plausibili."""
import re, json, pathlib, urllib.request, urllib.parse, io
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
def get(u, b=False):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read(); return r if b else r.decode("utf-8", "replace")
    except Exception as e:
        return None
h = get("https://unacollezione.it/carta/b64_NDkyMTY1X0JUMTItMDAx") or ""
main = [urllib.parse.urljoin("https://unacollezione.it/", s) for s in re.findall(r'src="(/assets/index-[^"]+\.js)"', h)]
js = get(main[0]) if main else ""
chunks = sorted(set(re.findall(r'assets/[A-Za-z0-9_\-]+\.js', js or "")))
print("chunks", len(chunks))
pat = re.compile(r"[Ll]ogo|LOGO|IMGSET|img\.unacollezione\.it/[A-Za-z_]+|_imgset|imgset")
seen = {}
for c in chunks:
    t = get("https://unacollezione.it/" + c) or ""
    for m in pat.finditer(t):
        ctx = t[max(0, m.start() - 160):m.end() + 160].replace("\n", " ")
        if re.search(r"tierbadge|LogOut|logout|Logout|TcgLogoSelector\"|adminLogos\"", ctx): continue
        seen.setdefault(c, []).append(ctx)
for c, l in seen.items():
    print("== ", c, len(l))
    for x in l[:12]: print("    ", x[:340])
folders = sorted(set(re.findall(r"img\.unacollezione\.it/([A-Za-z_]+)/", " ".join(sum(seen.values(), [])))))
print("cartelle img:", folders)
# tentativi
names = ["digimon_across_time"]
tries = []
for f in set(folders + ["LOGO", "LOGOSET", "SETLOGO", "LOGHI", "logo", "IMGLOGO", "ICONSET", "SETICON"]):
    for n in names:
        for suf in ["_logo.webp", "_logo.png", ".webp", ".png", "_setlogo.webp", "_icon.webp"]:
            tries.append("https://img.unacollezione.it/%s/%s%s" % (f, n, suf))
for u in tries:
    b = get(u, True)
    if b:
        try:
            im = Image.open(io.BytesIO(b)); print("HIT", u, im.size, im.mode)
            (out / re.sub(r"\W+", "_", u.split("it/")[1])).write_bytes(b)
        except Exception:
            print("HIT?", u, len(b))
