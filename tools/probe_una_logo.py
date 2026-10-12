#!/usr/bin/env python3
"""Sonda 6: elenco set Digimon (stessi dati che la pagina "tutti i set" carica dal sito) con mainImage e imgset;
scarica gli imgset, controlla la trasparenza e crea un foglio di prova."""
import re, json, pathlib, urllib.request, urllib.parse, io, concurrent.futures as cf
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; (out / "una").mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
def get(u, b=False, hdr=None):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={**UA, **(hdr or {})}), timeout=30).read(); return r if b else r.decode("utf-8", "replace")
    except Exception as e:
        print("ERR", u[:140], e); return None
h = get("https://unacollezione.it/tutti-i-set") or ""
js = get("https://unacollezione.it" + re.findall(r'src="(/assets/index-[^"]+\.js)"', h)[0]) or ""
key = re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}', js).group(0)
q = "https://api.unacollezione.it/rest/v1/AllSets?select=id,name,subcategory,setCode,year,mainImage,imgset&subcategory=eq.digimon"
rows = json.loads(get(q, hdr={"apikey": key, "Authorization": "Bearer " + key}) or "[]")
print("set:", len(rows))
def one(r):
    res = {"id": r["id"], "name": r["name"], "code": r.get("setCode"), "imgset": r.get("imgset"), "main": r.get("mainImage")}
    u = r.get("imgset")
    if u:
        b = get(u, True)
        if b:
            im = Image.open(io.BytesIO(b)); im.load()
            a = im.convert("RGBA").split()[-1]
            res.update(size=im.size, mode=im.mode, transp=round(sum(1 for v in a.getdata() if v < 20) / (im.size[0] * im.size[1]), 2))
            im.convert("RGBA").save(out / "una" / (re.sub(r"\W+", "_", str(r["id"])) + ".png"))
    return res
with cf.ThreadPoolExecutor(10) as ex:
    res = list(ex.map(one, rows))
json.dump(res, open(out / "una_api.json", "w"), indent=1, ensure_ascii=False)
for r in res: print(r)
ok = sorted(out.glob("una/*.png"))
cw, ch, cols = 300, 150, 5
S = Image.new("RGB", (cols * cw, max(1, (len(ok) + cols - 1) // cols) * ch), (40, 40, 48)); d = ImageDraw.Draw(S)
for k, p in enumerate(ok):
    im = Image.open(p); im.thumbnail((cw - 10, ch - 22)); x, y = (k % cols) * cw, (k // cols) * ch
    bg = Image.new("RGBA", im.size, (255, 0, 255, 255)); bg.alpha_composite(im)
    S.paste(bg.convert("RGB"), (x + 5, y + 5)); d.text((x + 5, y + ch - 15), p.stem[:40], fill=(255, 255, 255))
S.save(out / "una_sheet.jpg", quality=75)
import shutil; shutil.rmtree(out / "una")
