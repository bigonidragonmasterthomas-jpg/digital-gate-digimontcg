#!/usr/bin/env python3
"""Costruisce www/index.html (sito e APK usano gli stessi file) da src/template.html + src/data.json."""
import shutil, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src, www = root / "src", root / "www"
www.mkdir(exist_ok=True)
tpl = (src / "template.html").read_text(encoding="utf-8")
data = (src / "data.json").read_text(encoding="utf-8")
assert "/*DATA*/" in tpl
head = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="theme-color" content="#0b1120">\n<meta name="color-scheme" content="light dark">\n'
        '<link rel="manifest" href="manifest.webmanifest">\n<link rel="icon" href="icon-192.png">\n'
        '<link rel="apple-touch-icon" href="icon-192.png">\n<style>[hidden]{display:none!important}</style>\n')
tail = ('\n<script>if ("serviceWorker" in navigator && /^https?:/.test(location.protocol)) '
        'navigator.serviceWorker.register("sw.js").catch(function(){});</script>\n</body>\n</html>\n')
html = head + tpl.replace("/*DATA*/", data) + tail
(www / "index.html").write_text(html, encoding="utf-8")
for f in ("icon-192.png", "icon-512.png", "manifest.webmanifest", "sw.js"):
    shutil.copy(src / f, www / f)
print("www/index.html", len(html) // 1024, "KB")
