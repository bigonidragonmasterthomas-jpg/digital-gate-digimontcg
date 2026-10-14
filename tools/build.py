#!/usr/bin/env python3
"""Costruisce www/index.html (sito e APK usano gli stessi file) da src/template.html + src/data.json."""
import json, shutil, pathlib, os
root = pathlib.Path(__file__).resolve().parent.parent
src, www = root / "src", root / "www"
www.mkdir(exist_ok=True)
tpl = (src / "template.html").read_text(encoding="utf-8")
data = (src / "data.json").read_text(encoding="utf-8")
# caratteristiche dei prodotti (tools/fetch_products.py): aggiunte ai dati come "products"
prod = json.loads((src / "products.json").read_text(encoding="utf-8"))
data = data.rstrip()[:-1] + ',"products":' + json.dumps(prod, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "}"
assert "/*DATA*/" in tpl
head = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="theme-color" content="#0b1120">\n<meta name="color-scheme" content="light dark">\n'
        '<link rel="manifest" href="manifest.webmanifest">\n<link rel="icon" href="favicon.ico" sizes="16x16 32x32 48x48">\n'
        '<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">\n'
        '<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">\n'
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n<style>[hidden]{display:none!important}</style>\n')
tail = ('\n<script>if ("serviceWorker" in navigator && /^https?:/.test(location.protocol)) '
        'navigator.serviceWorker.register("sw.js").catch(function(){});</script>\n</body>\n</html>\n')
# numero di build (run di GitHub Actions): l'APK lo confronta con quello dell'ultima release per proporre l'aggiornamento
build = os.environ.get("GITHUB_RUN_NUMBER", "0")
head += '<script>window.APPBUILD=' + str(int(build)) + ';</script>\n'
html = head + tpl.replace("/*DATA*/", data) + tail
(www / "index.html").write_text(html, encoding="utf-8")
# icone generate da src/icons/digital-gate-mark.svg con tools/make_icons.py
for f in ("icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "favicon.ico", "favicon-32.png",
          "manifest.webmanifest", "sw.js"):
    shutil.copy(src / f, www / f)
print("www/index.html", len(html) // 1024, "KB")
