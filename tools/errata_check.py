"""Scarica le immagini post-errata ufficiali, separa quelle che contengono più carte affiancate,
le confronta con l'immagine attuale del sito e salva in analysis/ quelle diverse (= il sito ha la versione pre-errata)."""
import json, io, pathlib, urllib.request
from PIL import Image
import numpy as np
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
M = json.load(open("tools/errata_images.json"))
SITE = "https://knightofgemini.github.io/digital-gate-digimontcg/img/f/{}.webp"
def get(u):
    return Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read())).convert("RGBA")
def flat(im):
    bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3]); return bg
def mask(im):
    a = np.asarray(im).astype(int)
    if a[..., 3].min() < 250: return a[..., 3] > 30
    bg = a[0, 0, :3]; return np.abs(a[..., :3] - bg).sum(-1) > 40
def pieces(im):
    m = mask(im); cols = m.mean(0) > 0.05
    runs, start = [], None
    for x, v in enumerate(list(cols) + [False]):
        if v and start is None: start = x
        if not v and start is not None:
            if x - start > im.size[0] * 0.08: runs.append((start, x))
            start = None
    res = []
    for x0, x1 in runs or [(0, im.size[0])]:
        sub = im.crop((x0, 0, x1, im.size[1])); sm = mask(sub); ys = np.where(sm.mean(1) > 0.05)[0]
        if len(ys): sub = sub.crop((0, ys.min(), sub.size[0], ys.max() + 1))
        res.append(flat(sub))
    return res
def diff(a, b):
    A = np.asarray(a.resize((300, 420)), float); B = np.asarray(b.resize((300, 420)), float)
    return float(np.abs(A - B).mean())
res = {}
for k, u in sorted(M.items()):
    try:
        site = get(SITE.format(k)); site = flat(site).crop(Image.fromarray((mask(site) * 255).astype("uint8")).getbbox())
        ps = pieces(get(u))
    except Exception as e:
        res[k] = {"err": str(e)}; print(k, "err", e); continue
    ps = [p for p in ps if 0.55 < p.size[0] / p.size[1] < 0.9] or ps
    ds = [diff(p, site) for p in ps]; i = int(np.argmin(ds)); best = ps[i]
    res[k] = {"n": len(ps), "d": round(ds[i], 1)}
    print(k, res[k])
    best.save(out / (k + ".webp"), "WEBP", quality=88)
    s = Image.new("RGB", (600, 420)); s.paste(best.resize((300, 420)), (0, 0)); s.paste(site.resize((300, 420)), (300, 0)); s.save(out / (k + "_cmp.jpg"), quality=70)
json.dump(res, open(out / "errata_check.json", "w"), indent=0)
