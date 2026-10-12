#!/usr/bin/env python3
"""Prova: ingrandimento AI 2x di 4 bustine vecchie, due modelli Real-ESRGAN:
 A = RealESRGAN_x2plus (nativo 2x, generico)
 B = RealESRGAN_x4plus_anime_6B (per illustrazioni) e poi riportato a 2x
Confronto: originale come lo ingrandisce il browser / A / B."""
import subprocess, sys, pathlib, io, functools, urllib.request
sys.stderr = sys.stdout
subprocess.run = functools.partial(subprocess.run, stderr=subprocess.STDOUT)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--index-url", "https://download.pytorch.org/whl/cpu", "torch", "torchvision"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "spandrel", "numpy", "pillow"], check=True)
import numpy as np, torch
from spandrel import ModelLoader
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "analysis" / "ai2x"; out.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", "set-assets"], check=True, cwd=root)
M = {"A": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
     "B": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"}
models = {}
for k, u in M.items():
    f = pathlib.Path.home() / (k + ".pth"); urllib.request.urlretrieve(u, f)
    models[k] = ModelLoader().load_from_file(str(f)).eval()


def ai2x(im, k):
    rgba = im.convert("RGBA"); w, h = rgba.size
    x = torch.from_numpy(np.asarray(rgba.convert("RGB"), dtype=np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0)
    with torch.inference_mode():
        y = models[k](x).clamp(0, 1)[0].permute(1, 2, 0).numpy()
    o = Image.fromarray((y * 255 + 0.5).astype(np.uint8), "RGB").resize((w * 2, h * 2), Image.LANCZOS)
    o.putalpha(rgba.split()[-1].resize((w * 2, h * 2), Image.LANCZOS))
    return o


codes = ["BT5", "BT10", "EX2", "ST1"]
rows = []
for c in codes:
    b = subprocess.run(["git", "show", "FETCH_HEAD:%s/confezione.png" % c], capture_output=True, cwd=root).stdout
    o = Image.open(io.BytesIO(b)).convert("RGBA")
    ims = [o.resize((o.size[0] * 2, o.size[1] * 2), Image.BILINEAR)]
    for k in "AB":
        r = ai2x(o, k); r.save(out / ("%s-confezione-ai2x-%s.webp" % (c, k)), "WEBP", quality=92, method=6); ims.append(r)
    print(c, o.size, "->", ims[1].size)
    rows.append((c, ims))
W = sum(sum(i.size[0] for i in ims) + 50 for _, ims in rows)
S = Image.new("RGBA", (W, 740), (40, 40, 48, 255)); d = ImageDraw.Draw(S); x = 0
for c, ims in rows:
    d.text((x + 5, 5), c + ":  originale (browser)  |  AI A  |  AI B", fill=(255, 255, 255))
    for i in ims:
        S.alpha_composite(i, (x, 30)); x += i.size[0] + 8
    x += 26
S.convert("RGB").save(root / "analysis" / "confronto_ai2x.jpg", quality=90)
# zoom sul logo di BT5
c, ims = rows[0]
box = (0.08, 0.6, 0.92, 0.82)
crops = [i.crop((int(box[0] * i.size[0]), int(box[1] * i.size[1]), int(box[2] * i.size[0]), int(box[3] * i.size[1]))) for i in ims]
crops = [cr.resize((cr.size[0] * 3, cr.size[1] * 3), Image.LANCZOS) for cr in crops]
Z = Image.new("RGBA", (crops[0].size[0], sum(cr.size[1] + 10 for cr in crops)), (40, 40, 48, 255)); y = 0
for cr in crops: Z.alpha_composite(cr, (0, y)); y += cr.size[1] + 10
Z.convert("RGB").save(root / "analysis" / "zoom_ai2x.jpg", quality=90)
