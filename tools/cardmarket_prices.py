"""Prezzi Cardmarket per Digital Gate.

Legge i file pubblici di Cardmarket (catalogo carte singole + guida prezzi giornaliera,
gioco Digimon = 17) e abbina ogni versione dell'app al prodotto Cardmarket giusto.
Scrive src/prices.json.

Uso:
  python3 tools/cardmarket_prices.py [--dir CARTELLA_FILE] [--sets EX13,BT26] [--scarica]

Regole di abbinamento (prudenti: nel dubbio nessun prezzo, mai un prezzo sbagliato):
- per ogni prodotto dell'app si cerca l'espansione Cardmarket in cui compaiono più carte con il suo codice set;
- per ogni numero di carta i prodotti Cardmarket vengono ordinati per idProduct (ordine di inserimento: V1, V2, ...);
- se il numero di versioni coincide con quello dell'app si abbinano nell'ordine dell'app (Regular, ★, ★★, SP);
  se i prezzi non salgono in quell'ordine (es. la ★ costa più della ★★) le alternative art restano senza prezzo;
- se il numero non coincide si abbina solo la versione Regular, e solo se è chiaramente la più economica.
"""
import argparse, json, os, re, urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://downloads.s3.cardmarket.com/productCatalog"
GAME = 17  # Digimon su Cardmarket
CODE = re.compile(r"\(([A-Z0-9]+-\d+)\)\s*$")


def scarica(cartella):
    os.makedirs(cartella, exist_ok=True)
    for nome, url in [("singles.json", f"{BASE}/productList/products_singles_{GAME}.json"),
                      ("price_guide.json", f"{BASE}/priceGuide/price_guide_{GAME}.json")]:
        req = urllib.request.Request(url, headers={"User-Agent": "DigitalGate/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            Path(cartella, nome).write_bytes(r.read())


def val(g):
    """Prezzo di riferimento per i controlli: trend, altrimenti il più basso."""
    if not g:
        return None
    return g.get("trend") or g.get("low") or None


def voce(g, idp):
    r = lambda x: None if x in (None, 0) else round(float(x), 2)
    return [r(g.get("trend")), r(g.get("low")), r(g.get("avg1")), r(g.get("avg7")), r(g.get("avg30")), idp] if g else [None] * 5 + [idp]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="cardmarket")
    ap.add_argument("--sets", default="EX13")
    ap.add_argument("--scarica", action="store_true")
    a = ap.parse_args()
    if a.scarica:
        scarica(a.dir)
    singles = json.loads(Path(a.dir, "singles.json").read_text())
    guide = json.loads(Path(a.dir, "price_guide.json").read_text())
    pg = {g["idProduct"]: g for g in guide["priceGuides"]}
    data = json.loads((ROOT / "src/data.json").read_text())
    cards, versions = data["cards"], data["versions"]

    # prodotti Cardmarket per espansione e per numero di carta
    by_exp = defaultdict(lambda: defaultdict(list))
    for p in singles["products"]:
        m = CODE.search(p["name"])
        if m:
            by_exp[p["idExpansion"]][m.group(1)].append(p)

    wanted = {s.strip().upper() for s in a.sets.split(",") if s.strip()}
    out, report, covered = {}, [], []
    for s in data["sets"]:
        if s["code"].upper() not in wanted:
            continue
        # versioni dell'app per numero di carta, nell'ordine dell'app
        app = defaultdict(list)
        for v in s["v"]:
            i = v if isinstance(v, int) else v[0]
            c = cards[i]
            key_base = f"{c[16]}|{c[0]}"
            key = key_base if isinstance(v, int) else key_base + "~" + v[1]
            app[c[0]].append((key, v))
        # espansione Cardmarket con più carte di questo set
        pref = s["code"].upper() + "-"
        best = max(by_exp, key=lambda e: sum(1 for k in by_exp[e] if k.startswith(pref)), default=None)
        if best is None or not any(k.startswith(pref) for k in by_exp[best]):
            report.append(f"{s['code']}: nessuna espansione Cardmarket trovata")
            continue
        covered.append(s["id"])
        cm = by_exp[best]
        ok = dubbi = 0
        for code, vers in app.items():
            prods = sorted(cm.get(code, []), key=lambda p: p["idProduct"])
            if not prods:
                report.append(f"{code}: non trovata su Cardmarket")
                dubbi += len(vers)
                continue
            vals = [val(pg.get(p["idProduct"])) for p in prods]
            # la Regular dev'essere la prima e la più economica
            base_ok = isinstance(vers[0][1], int) and vals[0] is not None and all(x is None or vals[0] <= x for x in vals[1:])
            if len(prods) == len(vers):
                seq = [x for x in vals if x is not None]
                crescente = all(x <= y for x, y in zip(seq, seq[1:]))
                for n, ((key, v), p) in enumerate(zip(vers, prods)):
                    if (base_ok if (n == 0 and isinstance(v, int)) else crescente):
                        out[key] = voce(pg.get(p["idProduct"]), p["idProduct"]); ok += 1
                    else:
                        dubbi += 1
                if not crescente and len(vers) > 1:
                    report.append(f"{code}: prezzi delle versioni fuori ordine {vals} -> alternative art senza prezzo")
            else:
                key, v = vers[0]
                if base_ok:
                    out[key] = voce(pg.get(prods[0]["idProduct"]), prods[0]["idProduct"]); ok += 1
                dubbi += len(vers) - (1 if base_ok else 0)
                report.append(f"{code}: app {len(vers)} versioni, Cardmarket {len(prods)} -> " + ("solo Regular" if base_ok else "nessun prezzo"))
        report.append(f"== {s['code']} (espansione Cardmarket {best}): {ok} versioni con prezzo, {dubbi} senza")

    res = {"d": guide.get("createdAt", "")[:10], "src": "Cardmarket", "sets": covered, "p": out}
    (ROOT / "src/prices.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")))
    print("\n".join(report))


if __name__ == "__main__":
    main()
