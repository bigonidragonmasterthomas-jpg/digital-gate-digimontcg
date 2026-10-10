import sys, pathlib, urllib.request
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
U = {
 "io_dual.json": "https://digimoncard.io/api-public/search?type=Dual",
 "world_cards.html": "https://world.digimoncard.com/cards/?search=true&keyword=BT26-050",
 "world_cards_all.html": "https://world.digimoncard.com/cards/?search=true",
 "world_cards_bt26.html": "https://world.digimoncard.com/cards/?search=true&category=522026",
}
for n, u in U.items():
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        (out / n).write_bytes(b); print(n, len(b))
    except Exception as e: print(n, "err", e)
