#!/usr/bin/env python3
"""Ingrandisce con AI (Real-ESRGAN, modello per illustrazioni) le immagini "confezione" piccole del branch set-assets.

Uso:  python3 tools/upscale_packs.py CARTELLA_SET_ASSETS [CODICE ...]
Con la variabile PREV=cartella dell'esecuzione precedente riusa le immagini già ingrandite se l'originale non è cambiato.
Per ogni espansione con confezione larga meno di MIN_W px crea CODICE/confezione-hd.webp (circa 4x, max HD_H px di altezza)
e aggiorna index.json. Il colore passa dal modello AI, la trasparenza viene ingrandita a parte con Lanczos.
Gira su CPU (GitHub Actions): le immagini sono piccole, bastano pochi secondi l'una."""
import json, os, pathlib, shutil, sys, urllib.request
import numpy as np
import torch
from PIL import Image
from spandrel import ModelLoader

MIN_W, HD_H = 400, 1400
MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
root = pathlib.Path(sys.argv[1]).resolve()
only = set(sys.argv[2:])
cache = pathlib.Path.home() / ".cache" / "realesrgan_anime6b.pth"
model = None


def upscale(im):
    global model
    if model is None:
        if not cache.exists():
            cache.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(MODEL_URL, cache)
        model = ModelLoader().load_from_file(str(cache)).eval()
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
prev_dir = pathlib.Path(os.environ["PREV"]) if os.environ.get("PREV") else None
prev = {}
if prev_dir and (prev_dir / "index.json").exists():
    prev = {q["codice"]: q for q in json.load(open(prev_dir / "index.json", encoding="utf-8"))}
done = reused = 0
for p in index:
    f = p["file"].get("confezione")
    if not f or (only and p["codice"] not in only) or f["w"] >= MIN_W:
        continue
    name = "%s/confezione-hd.webp" % p["codice"]
    old = prev.get(p["codice"], {}).get("file", {})
    same = old.get("confezione") and old["confezione"]["url"] == f["url"] and (prev_dir / old["confezione"]["file"]).exists() \
        and (prev_dir / old["confezione"]["file"]).read_bytes() == (root / f["file"]).read_bytes()
    if same and "confezione-hd" in old and (prev_dir / name).exists():
        shutil.copy(prev_dir / name, root / name)
        p["file"]["confezione-hd"] = old["confezione-hd"]
        reused += 1
        continue
    hd = upscale(Image.open(root / f["file"]))
    hd.save(root / name, "WEBP", quality=90, method=6)
    p["file"]["confezione-hd"] = {"file": name, "url": f["url"], "fonte": f["fonte"] + " + Real-ESRGAN",
                                  "w": hd.size[0], "h": hd.size[1], "kb": round((root / name).stat().st_size / 1024)}
    done += 1
    print(p["codice"], f["w"], "x", f["h"], "->", hd.size[0], "x", hd.size[1], flush=True)
json.dump(index, open(root / "index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# nella galleria README mostra la versione ingrandita
readme = root / "README.md"
if readme.exists():
    t = readme.read_text(encoding="utf-8")
    for p in index:
        if "confezione-hd" in p["file"]:
            t = t.replace('<img src="%s" width="70">' % p["file"]["confezione"]["file"], '<img src="%s" width="70">' % p["file"]["confezione-hd"]["file"])
    readme.write_text(t, encoding="utf-8")
print("bustine ingrandite:", done, "- riusate dall'esecuzione precedente:", reused)
