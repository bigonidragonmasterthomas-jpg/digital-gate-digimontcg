#!/usr/bin/env python3
"""Sonda 5: vista elenco dei set Digimon di unacollezione.it: quali immagini usa e da quale API le prende."""
import re, json, pathlib, urllib.request, io
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; out.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
def get(u, b=False, hdr=None):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={**UA, **(hdr or {})}), timeout=25).read(); return r if b else r.decode("utf-8", "replace")
    except Exception as e:
        print("ERR", u[:120], e); return None
P = "https://unacollezione.it/tutti-i-set?category=tcg&subcategory=digimon&view=list"
h = get(P) or ""
(out / "list.html").write_text(h)
urls = sorted(set(re.findall(r'https://img\.unacollezione\.it/[^"\'\s&<>)]+', h)))
print("img nella pagina:", len(urls)); [print("  ", u) for u in urls[:200]]
main = re.findall(r'src="(/assets/index-[^"]+\.js)"', h)
js = get("https://unacollezione.it" + main[0]) if main else ""
for c in sorted(set(re.findall(r'assets/(?:sets|AllSetsPage|adminLogos|upcomingSets)[A-Za-z0-9_\-]*\.js', js or ""))):
    t = get("https://unacollezione.it/" + c) or ""
    print("==", c, len(t))
    for m in re.finditer(r"https?://[a-z0-9.\-]+\.[a-z]{2,}[^\"'`\s]*|from\(\"[a-z_]+\"\)|\.select\(\"[^\"]+\"\)|rpc\(\"[^\"]+\"|logo[A-Za-z_]*|imgset", t):
        print("   ", t[max(0, m.start() - 80):m.end() + 120].replace("\n", " ")[:260])
# chiavi supabase nel bundle principale
for m in re.finditer(r'https://[a-z0-9]+\.supabase\.co|eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}|https://api\.unacollezione\.it[^"\'`\s]*', js or ""):
    print("KEY", m.group(0)[:200])
