"""Confronta le immagini post-errata ufficiali con quelle attuali del sito (stessa arte? testo diverso?)."""
import json, io, pathlib, urllib.request
from PIL import Image
import numpy as np
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
M = json.load(open("tools/errata_images.json"))
SITE = "https://knightofgemini.github.io/digital-gate-digimontcg/img/f/{}.webp"
def get(u):
    return Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read())).convert("RGB")
res = {}
for k, u in sorted(M.items()):
    try:
        a = get(u).resize((300, 420)); b = get(SITE.format(k)).resize((300, 420))
    except Exception as e:
        res[k] = {"err": str(e)}; print(k, "err", e); continue
    A, B = np.asarray(a, float), np.asarray(b, float)
    art = float(np.abs(A[40:230] - B[40:230]).mean()); txt = float(np.abs(A[230:] - B[230:]).mean()); tot = float(np.abs(A - B).mean())
    res[k] = {"art": round(art, 1), "txt": round(txt, 1), "tot": round(tot, 1), "w": a.size}
    print(k, res[k])
    s = Image.new("RGB", (600, 420)); s.paste(a, (0, 0)); s.paste(b, (300, 0)); s.save(out / (k + ".jpg"), quality=70)
json.dump(res, open(out / "errata_check.json", "w"), indent=0)
