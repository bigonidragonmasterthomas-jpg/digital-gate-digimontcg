"""Trova il gioco Digimon nei file pubblici di Cardmarket (catalogo + guida prezzi)
e li salva in analysis/cardmarket/. Uso: python3 tools/probe_cardmarket.py [id_max]"""
import json, os, sys, urllib.request

BASE = "https://downloads.s3.cardmarket.com/productCatalog"
OUT = "analysis/cardmarket"
os.makedirs(OUT, exist_ok=True)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "DigitalGate/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    top = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 40
    found = None
    summary = {}
    for gid in range(1, top + 1):
        try:
            raw = get(f"{BASE}/productList/products_singles_{gid}.json")
        except Exception as e:  # file assente per questo gioco
            summary[gid] = f"errore: {e}"
            continue
        data = json.loads(raw)
        prods = data.get("products", [])
        names = [p.get("name") for p in prods[:5]]
        summary[gid] = {"n": len(prods), "esempi": names}
        print(gid, len(prods), names)
        if found is None and any(p.get("name", "").startswith(("Agumon", "Gabumon", "Koromon")) for p in prods):
            found = gid
    json.dump(summary, open(f"{OUT}/giochi.json", "w"), ensure_ascii=False, indent=1)
    print("DIGIMON =", found)
    if found:
        for name, url in [
            ("singles.json", f"{BASE}/productList/products_singles_{found}.json"),
            ("nonsingles.json", f"{BASE}/productList/products_nonsingles_{found}.json"),
            ("price_guide.json", f"{BASE}/priceGuide/price_guide_{found}.json"),
        ]:
            try:
                open(f"{OUT}/{name}", "wb").write(get(url))
                print("salvato", name)
            except Exception as e:
                print("errore", name, e)


if __name__ == "__main__":
    main()
