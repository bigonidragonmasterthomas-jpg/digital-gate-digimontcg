import sys, pathlib, urllib.request
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
U = {
 "io1.json": "https://digimoncard.io/api-public/search.php?card=BT26-050",
 "io2.json": "https://digimoncard.io/api-public/search?card=BT26-050",
 "world_list.html": "https://world.digimoncard.com/cardlist/?search=true&keyword=BT26-050",
 "world_cat.html": "https://world.digimoncard.com/cardlist/?search=true&category=522026",
 "en_list.html": "https://en.digimoncard.com/cardlist/?search=true&keyword=BT26-050",
 "world_root.html": "https://world.digimoncard.com/cardlist/",
 "wikimon.html": "https://wikimon.net/BT26-050",
}
for n, u in U.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        (out / n).write_bytes(b); print(n, len(b))
    except Exception as e: print(n, "err", e)
