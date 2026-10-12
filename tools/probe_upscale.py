#!/usr/bin/env python3
"""Prova: ingrandisce 5 bustine vecchie e crea un confronto (Lanczos semplice / Real-ESRGAN)."""
import subprocess, sys, pathlib, shutil
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--index-url", "https://download.pytorch.org/whl/cpu", "torch"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "spandrel", "numpy", "pillow"], check=True)
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
work = root / "analysis" / "sa"; work.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", "set-assets"], check=True, cwd=root)
subprocess.run("git archive FETCH_HEAD | tar -x -C %s" % work, shell=True, check=True, cwd=root)
codes = ["BT1-3_v1.0", "BT5", "BT10", "EX2", "ST1", "RB1"]
subprocess.run([sys.executable, str(root / "tools" / "upscale_packs.py"), str(work)] + codes, check=True)
rows = []
for c in codes:
    o = Image.open(work / c / "confezione.png").convert("RGBA"); hd = Image.open(work / c / "confezione-hd.webp").convert("RGBA")
    H = 700; l = o.resize((round(o.size[0] * H / o.size[1]), H), Image.LANCZOS); r = hd.resize((round(hd.size[0] * H / hd.size[1]), H), Image.LANCZOS)
    rows.append((c, l, r))
W = sum(l.size[0] + r.size[0] + 40 for _, l, r in rows)
S = Image.new("RGBA", (W, 740), (40, 40, 48, 255)); d = ImageDraw.Draw(S); x = 0
for c, l, r in rows:
    d.text((x + 5, 5), c + "  prima / dopo", fill=(255, 255, 255)); S.alpha_composite(l, (x, 30)); S.alpha_composite(r, (x + l.size[0] + 10, 30)); x += l.size[0] + r.size[0] + 40
S.convert("RGB").save(root / "analysis" / "upscale_confronto.jpg", quality=88)
# zoom di dettaglio su BT5
o = Image.open(work / "BT5" / "confezione.png").convert("RGBA"); hd = Image.open(work / "BT5" / "confezione-hd.webp").convert("RGBA")
box = (0.1, 0.55, 0.9, 0.85)
def crop(im, s): w, h = im.size; return im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))).resize(s, Image.LANCZOS)
s = (900, int(900 * (box[3] - box[1]) * o.size[1] / ((box[2] - box[0]) * o.size[0])))
Z = Image.new("RGBA", (s[0], s[1] * 2 + 10), (40, 40, 48, 255)); Z.alpha_composite(crop(o, s), (0, 0)); Z.alpha_composite(crop(hd, s), (0, s[1] + 10))
Z.convert("RGB").save(root / "analysis" / "upscale_zoom.jpg", quality=88)
shutil.rmtree(work)
