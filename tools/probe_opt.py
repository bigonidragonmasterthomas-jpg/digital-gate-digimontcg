import sys, pathlib, urllib.request
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
U = {
 "rule_world.html": "https://world.digimoncard.com/rule/",
 "errata_world.html": "https://world.digimoncard.com/rule/errata_card/",
 "errata_world2.html": "https://world.digimoncard.com/rule/errata/",
 "errata_en.html": "https://en.digimoncard.com/rule/errata_card/",
 "rule_en.html": "https://en.digimoncard.com/rule/",
 "lang.html": "https://world.digimoncard.com/rule/lang-standardization-rules/",
}
for n, u in U.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        (out / n).write_bytes(b); print(n, len(b))
    except Exception as e: print(n, "err", e)
