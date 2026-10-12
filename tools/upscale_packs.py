#!/usr/bin/env python3
"""Ingrandisce con AI (Real-ESRGAN, modello per illustrazioni) le immagini "confezione" piccole del branch set-assets.

Uso:  python3 tools/upscale_packs.py CARTELLA_SET_ASSETS [CODICE ...]
Per ogni espansione con confezione larga meno di MIN_W px crea CODICE/confezione-hd.webp (circa 4x, max HD_H px di altezza)
e aggiorna index.json. Il colore passa dal modello AI, la trasparenza viene ingrandita a parte con Lanczos.
Gira su CPU (GitHub Actions): le immagini sono piccole, bastano pochi secondi l'una."""
import json, pathlib, sys, urllib.request
import numpy as np
import torch
from PIL import Image
from spandrel import ModelLoader

MIN_W, HD_H = 400, 1400
MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
root = pathlib.Path(sys.argv[1]).resolve()
only = set(sys.argv[2:])
cache = pathlib.Path.home() / ".cache" / "realesrgan_anime6b.pth"
if not cache.exists():
    cache.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(MODEL_URL, cache)
torch.set_num_threads(max(1, torch.get_num_threads()))
model = ModelLoader().load_from_file(str(cache)).eval()


def upscale(im):
    rgba = im.convert("RGBA")
    rgb = np.asarray(rgba.convert("RGB"), dtype=np.float32) / 255.0
    with torch.inference_mode():
        t = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0)
        y = model(t).clamp(0, 1)[0].permute(1, 2, 0).numpy()
    out = Image.fromarray((y * 255 + 0.5).astype(np.uint8), "RGB")
    alpha = rgba.split()[-1]
    if alpha.getextrema() != (255, 255):
        out.putalpha(alpha.resize(out.size, Image.LANCZOS))
    if out.size[1] > HD_H:
        out = out.resize((round(out.size[0] * HD_H / out.size[1]), HD_H), Image.LANCZOS)
    return out


index = json.load(open(root / "index.json", encoding="utf-8"))
done = 0
for p in index:
    f = p["file"].get("confezione")
    if not f or (only and p["codice"] not in only) or f["w"] >= MIN_W:
        continue
    src = root / f["file"]
    hd = upscale(Image.open(src))
    name = "%s/confezione-hd.webp" % p["codice"]
    hd.save(root / name, "WEBP", quality=90, method=6)
    p["file"]["confezione-hd"] = {"file": name, "url": f["url"], "fonte": f["fonte"] + " + Real-ESRGAN",
                                  "w": hd.size[0], "h": hd.size[1], "kb": round((root / name).stat().st_size / 1024)}
    done += 1
    print(p["codice"], f["w"], "x", f["h"], "->", hd.size[0], "x", hd.size[1], flush=True)
json.dump(index, open(root / "index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("bustine ingrandite:", done)
