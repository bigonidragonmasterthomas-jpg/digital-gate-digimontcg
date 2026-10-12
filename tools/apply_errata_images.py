#!/usr/bin/env python3
"""Sostituisce l'immagine principale delle carte con errata con la versione ufficiale post-errata (src/errata/KEY.webp)
e conserva l'immagine originale in www/img/pre/KEY.webp per la sezione "Pre errata" della scheda."""
import pathlib, shutil
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
img = root / "www" / "img"; (img / "pre").mkdir(parents=True, exist_ok=True)
n = 0
for src in sorted((root / "src" / "errata").glob("*.webp")):
    k = src.stem; f, t, pre = img / "f" / src.name, img / "t" / src.name, img / "pre" / src.name
    marker = img / "pre" / (k + ".done")
    if f.exists() and not pre.exists() and not marker.exists(): shutil.copy(f, pre)
    im = Image.open(src).convert("RGB")
    im.save(f, "WEBP", quality=82)
    b = im.copy(); b.thumbnail((120, 168)); b.save(t, "WEBP", quality=75)
    marker.write_text("1"); n += 1
print("errata applicate:", n, "pre:", len(list((img / "pre").glob("*.webp"))))
