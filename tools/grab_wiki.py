import sys, pathlib, urllib.request
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
B = "https://digimoncardgame.fandom.com"
U = {"timings.html": "/wiki/Timings", "timings.wiki": "/wiki/Timings?action=raw",
     "common.css": "/wiki/MediaWiki:Common.css?action=raw", "fandom.css": "/wiki/MediaWiki:Fandomdesktop.css?action=raw"}
for n, p in U.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(B + p, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        (out / n).write_bytes(b); print(n, len(b))
    except Exception as e: print(n, "err", e)
