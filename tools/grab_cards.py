import sys, pathlib, urllib.request
SRC = ["https://world.digimoncard.com/images/cardlist/card/{}.png", "https://en.digimoncard.com/images/cardlist/card/{}.png", "https://web-garage.takaotaku.de/{}.webp"]
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
for code in sys.argv[1:]:
    for u in SRC:
        try:
            b = urllib.request.urlopen(urllib.request.Request(u.format(code), headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
            if len(b) > 5000: (out / (code + "." + u.rsplit(".", 1)[1])).write_bytes(b); print(code, "ok", u, len(b)); break
        except Exception as e: print(code, "err", u, e)
