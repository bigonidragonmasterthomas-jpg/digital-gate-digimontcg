"""Confronta le immagini post-errata ufficiali con quelle attuali del sito (stessa arte? testo diverso?)."""
import json, io, pathlib, urllib.request
from PIL import Image
import numpy as np
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
M = json.load(open("tools/errata_images.json"))
SITE = "https://knightofgemini.github.io/digital-gate-digimontcg/img/f/{}.webp"
def get(u):
    return Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read())).convert("RGBA")
def trim(im):
    """ritaglia i bordi vuoti/trasparenti o di colore uniforme attorno alla carta"""
    a = np.asarray(im).astype(int)
    if a[..., 3].min() < 250:
        m = a[..., 3] > 30
    else:
        bg = a[0, 0, :3]; m = np.abs(a[..., :3] - bg).sum(-1) > 40
    ys, xs = np.where(m)
    if len(xs) < 100: return im.convert("RGB")
    bb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3])
    return bg.crop(bb)
res = {}
for k, u in sorted(M.items()):
    try:
        ra = trim(get(u)); a = ra.resize((300, 420)); b = trim(get(SITE.format(k))).resize((300, 420))
        ra.save(out / (k + "_errata.png"))
    except Exception as e:
        res[k] = {"err": str(e)}; print(k, "err", e); continue
    A, B = np.asarray(a, float), np.asarray(b, float)
    art = float(np.abs(A[40:230] - B[40:230]).mean()); txt = float(np.abs(A[230:] - B[230:]).mean()); tot = float(np.abs(A - B).mean())
    res[k] = {"art": round(art, 1), "txt": round(txt, 1), "tot": round(tot, 1), "w": a.size}
    print(k, res[k])
    s = Image.new("RGB", (600, 420)); s.paste(a, (0, 0)); s.paste(b, (300, 0)); s.save(out / (k + ".jpg"), quality=70)
json.dump(res, open(out / "errata_check.json", "w"), indent=0)
