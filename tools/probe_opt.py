import sys, pathlib, urllib.request
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
U = {
 "ban_world.html": "https://world.digimoncard.com/rule/restriction_card/",
 "ban_en.html": "https://en.digimoncard.com/rule/restriction_card/",
 "rule_world.html": "https://world.digimoncard.com/rule/",
}
for n, u in U.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        (out / n).write_bytes(b); print(n, len(b))
    except Exception as e: print(n, "err", e)
