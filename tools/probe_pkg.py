#!/usr/bin/env python3
"""Sonda: dimensioni delle immagini confezione (img_pkg e point/*/pkg*) sui tre siti ufficiali, per trovare le più grandi."""
import re, io, json, pathlib, urllib.request, concurrent.futures as cf
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis"; (out / "pkg").mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read()
    except Exception: return None
H = ["https://world.digimoncard.com", "https://en.digimoncard.com", "https://digimoncard.com"]
P = ["pack/ver%d/img_pkg.png" % i for i in range(1, 28)] + ["pack/ex-%02d/img_pkg.png" % i for i in range(1, 14)] + \
    ["deck/st-%d/img_pkg.png" % i for i in range(1, 27)] + ["pack/rb-01/img_pkg.png", "pack/ad-01/img_pkg.png", "pack/ver18-19/img_pkg.png", "pack/ver19-20/img_pkg.png"]
X = """pack/ex-06/point/06/pkg.png pack/ex-07/point/07/pkg.png pack/ex-08/point/05/pkg.png pack/ex-08/point/05/pkg_upgrade.png pack/ex-09/point/05/pkg.png
pack/ex-10/point/04/pkg.png pack/ex-11/point/05/pkg.png pack/ex-12/point/04/pkg.png pack/ex-13/point/04/pkg.webp pack/ver17/point/08/pkg_01.png pack/ver17/point/08/pkg_02.png
pack/ver17/point/08/pkg_03.png pack/ver18-19/point/05/pkg_01.png pack/ver18-19/point/05/pkg_02.png pack/ver19-20/point/06/pkg_01.png pack/ver19-20/point/06/pkg_02.png
pack/ver21/point/05/pkg.png pack/ver21/point/05/pkg2.png pack/ver22/point/05/pkg.png pack/ver23/point/05/pkg.png pack/ver24/point/04/pkg.png pack/ver25/point/06/pkg.png
pack/ver26/point/05/pkg.webp deck/st18-19/point/05/pkg.png deck/st20-21/point/06/pkg.png pack/ex-01/img_box.png pack/ver4/img_box.png pack/ver8/img_box.png
pack/ver18/point/05/pkg.png pack/ver19/point/04/pkg.png pack/ver20/point/04/pkg.png""".split()
urls = [h + "/images/products/" + p for h in H for p in P + X]
def one(u):
    b = get(u)
    if not b: return u, None
    try:
        im = Image.open(io.BytesIO(b)); return u, [im.size[0], im.size[1], len(b) // 1024]
    except Exception: return u, None
res = {}
with cf.ThreadPoolExecutor(16) as ex:
    for u, r in ex.map(one, urls):
        if r: res[u] = r
json.dump(res, open(out / "pkg_sizes.json", "w"), indent=1)
for u, r in sorted(res.items(), key=lambda x: -x[1][0] * x[1][1]): print(r, u)
# salva qualche esempio grande
for u, r in sorted(res.items(), key=lambda x: -x[1][0] * x[1][1])[:6]:
    (out / "pkg" / re.sub(r"\W+", "_", u.split("//")[1])[:80]).with_suffix(".png").write_bytes(get(u))
