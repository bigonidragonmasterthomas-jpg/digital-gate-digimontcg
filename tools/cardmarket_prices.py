"""Prezzi Cardmarket e CardTrader per Digital Gate -> src/prices.json.

Cardmarket: file pubblici giornalieri (catalogo carte singole + guida prezzi, gioco Digimon = 17), nessun permesso necessario.
CardTrader: API ufficiale con il codice del segreto CARDTRADER_TOKEN (mai stampato). Ogni carta CardTrader ("blueprint")
indica il proprio prodotto Cardmarket (card_market_ids) e il tipo di versione nel numero (EX13-014 = Regular,
...a = Alternate Art ★, ...rp = Rare Pull ★★, ...sp = Special Rare SP).

Uso:
  python3 tools/cardmarket_prices.py [--sets ALL | EX13,BT26] [--dir cardmarket] [--scarica] [--ct-dir cardtrader] [--ct-scarica]
         [--out src/prices.json] [--report report.txt]

Abbinamento (prudente: nel dubbio nessun prezzo, mai un prezzo sbagliato), per ogni prodotto dell'app:
- espansione Cardmarket = quella con più carte che hanno il codice del prodotto (BT26-..., EX13-...); i prodotti senza
  carte proprie (Premium Bandai, Limited, promo) per ora restano senza prezzi;
- per ogni numero di carta (anche le ristampe presenti nel prodotto) si prendono i prodotti Cardmarket di quell'espansione;
- se CardTrader indica con certezza il prodotto Cardmarket di ogni versione, vale quello;
- altrimenti ordine di inserimento su Cardmarket (V1, V2...) = ordine dell'app (Regular, ★, ★★, SP), accettato solo se i
  prezzi salgono in quell'ordine; se il numero di versioni non coincide si abbina solo la Regular, se è la più economica;
- le indicazioni certe di CardTrader correggono comunque l'ordine (es. Gankoomon EX13-061: ★ e ★★ invertite).
Prezzo CardTrader = offerta più bassa in inglese, Near Mint, non gradata (tra le 25 più economiche che dà l'API).
"""
import argparse, json, os, re, time, urllib.request
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://downloads.s3.cardmarket.com/productCatalog"
GAME = 17  # Digimon su Cardmarket
CODE = re.compile(r"\(([A-Z0-9]+-\d+)\)\s*$")
CT_API = "https://api.cardtrader.com/api/v2"
CT_GAME = 8  # Digimon su CardTrader
CT_SUFFIX = {"": 0, "a": 1, "rp": 2, "sp": "SP"}
CT_NUM = re.compile(r"^([A-Z0-9]+-\d+)([a-z]*)$")


def scarica(cartella):
    os.makedirs(cartella, exist_ok=True)
    for nome, url in [("singles.json", f"{BASE}/productList/products_singles_{GAME}.json"),
                      ("price_guide.json", f"{BASE}/priceGuide/price_guide_{GAME}.json")]:
        req = urllib.request.Request(url, headers={"User-Agent": "DigitalGate/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            Path(cartella, nome).write_bytes(r.read())


def ct_get(path, tentativi=3):
    tok = os.environ.get("CARDTRADER_TOKEN", "").strip()
    for n in range(tentativi):
        try:
            req = urllib.request.Request(CT_API + path, headers={"Authorization": "Bearer " + tok, "User-Agent": "DigitalGate/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if n == tentativi - 1:
                raise
            print("CardTrader: nuovo tentativo dopo", type(e).__name__, getattr(e, "code", ""))
            time.sleep(5 * (n + 1))


def ct_scarica(cartella):
    """Tutte le espansioni Digimon: carte e offerte (solo i campi utili, niente venditori). Circa 2 chiamate al secondo."""
    os.makedirs(cartella, exist_ok=True)
    exps = [e for e in ct_get("/expansions") if e.get("game_id") == CT_GAME]
    Path(cartella, "expansions_digimon.json").write_text(json.dumps(exps))
    for e in exps:
        try:
            Path(cartella, f"blueprints_{e['id']}.json").write_text(json.dumps(ct_get(f"/blueprints/export?expansion_id={e['id']}")))
            time.sleep(1.1)
            mk = ct_get(f"/marketplace/products?expansion_id={e['id']}")
            slim = {b: [{"price_cents": o.get("price", {}).get("cents"), "currency": o.get("price", {}).get("currency"),
                         "qty": o.get("quantity"), "props": o.get("properties_hash"), "graded": o.get("graded")} for o in offs]
                    for b, offs in mk.items()}
            Path(cartella, f"market_{e['id']}.json").write_text(json.dumps(slim))
            time.sleep(1.1)
        except Exception as ex:
            print("CardTrader: espansione", e.get("code"), "saltata:", type(ex).__name__)


def ct_carica(cartella):
    """Tutte le carte CardTrader scaricate: {cmid: blueprint}, {cmid: (numero, segno)}, offerte per blueprint."""
    cm2bp, cm2mk, market = {}, {}, {}
    p = Path(cartella)
    if not p.exists():
        return None
    for f in sorted(p.glob("blueprints_*.json")):
        eid = f.stem.split("_")[1]
        mf = p / f"market_{eid}.json"
        if mf.exists():
            market.update(json.loads(mf.read_text()))
        for b in json.loads(f.read_text()):
            ids = b.get("card_market_ids") or []
            cn = ((b.get("fixed_properties") or {}).get("collector_number") or "").strip()
            m = CT_NUM.match(cn)
            for cid in ids:
                cm2bp[cid] = b
                if len(ids) == 1 and m and m.group(2) in CT_SUFFIX:
                    cm2mk[cid] = (m.group(1), CT_SUFFIX[m.group(2)])
    return {"cm2bp": cm2bp, "cm2mk": cm2mk, "market": market} if cm2bp else None


def ct_prezzo(ct, cmid):
    b = ct["cm2bp"].get(cmid)
    if not b:
        return None
    offs = [o for o in ct["market"].get(str(b["id"]), []) if not o.get("graded") and o.get("currency") == "EUR"
            and (o.get("props") or {}).get("digimon_language") == "en" and (o.get("props") or {}).get("condition") == "Near Mint"
            and not (o.get("props") or {}).get("altered") and not (o.get("props") or {}).get("signed") and o.get("price_cents")]
    if not offs:
        return [None, 0, b["id"]]
    return [round(min(o["price_cents"] for o in offs) / 100, 2), len(offs), b["id"]]


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
    ap.add_argument("--sets", default="ALL")
    ap.add_argument("--scarica", action="store_true")
    ap.add_argument("--ct-dir", default="cardtrader")
    ap.add_argument("--ct-scarica", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "src/prices.json"))
    ap.add_argument("--report", default="")
    a = ap.parse_args()
    if a.scarica:
        scarica(a.dir)
    if a.ct_scarica and os.environ.get("CARDTRADER_TOKEN", "").strip():
        ct_scarica(a.ct_dir)
    singles = json.loads(Path(a.dir, "singles.json").read_text())
    guide = json.loads(Path(a.dir, "price_guide.json").read_text())
    pg = {g["idProduct"]: g for g in guide["priceGuides"]}
    data = json.loads((ROOT / "src/data.json").read_text())
    cards, versions = data["cards"], data["versions"]
    ct = ct_carica(a.ct_dir)

    # prodotti Cardmarket per espansione e per numero di carta
    by_exp = defaultdict(lambda: defaultdict(list))
    for p in singles["products"]:
        m = CODE.search(p["name"])
        if m:
            by_exp[p["idExpansion"]][m.group(1)].append(p)

    wanted = None if a.sets.strip().upper() == "ALL" else {s.strip().upper() for s in a.sets.split(",") if s.strip()}
    out, report, covered, ctout = {}, [], [], {}
    tot = Counter()
    for s in sorted(data["sets"], key=lambda x: x["date"], reverse=True):
        if wanted and s["code"].upper() not in wanted:
            continue
        # versioni dell'app per numero di carta, nell'ordine dell'app
        app = defaultdict(list)
        for v in s["v"]:
            i = v if isinstance(v, int) else v[0]
            c = cards[i]
            key_base = f"{c[16]}|{c[0]}"
            key = key_base if isinstance(v, int) else key_base + "~" + v[1]
            app[c[0]].append((key, v))
        if not app:
            continue
        # espansione Cardmarket con più carte che hanno il codice di questo prodotto
        pref = s["code"].upper() + "-"
        own = [k for k in app if k.startswith(pref)]
        best = max(by_exp, key=lambda e: sum(1 for k in own if k in by_exp[e]), default=None) if own else None
        found = sum(1 for k in own if best is not None and k in by_exp[best])
        if not own or found < max(1, len(own) // 2):
            report.append(f"-- {s['code']} {s['name']}: nessuna espansione Cardmarket sicura (carte proprie {len(own)}), senza prezzi")
            continue
        covered.append(s["id"])
        cm = by_exp[best]
        ok = dubbi = conf = corr = 0
        dettagli = []
        for code, vers in app.items():
            prods = sorted(cm.get(code, []), key=lambda p: p["idProduct"])
            if not prods:
                dubbi += len(vers)
                continue
            ids = {p["idProduct"] for p in prods}
            # indicazioni CardTrader: per ogni versione il prodotto Cardmarket con lo stesso segno (Regular, ★, ★★, SP)
            hints = {}
            if ct:
                bymk = defaultdict(list)
                for cid in ids:
                    mk = ct["cm2mk"].get(cid)
                    if mk and mk[0] == code:
                        bymk[mk[1]].append(cid)
                for key, v in vers:
                    if isinstance(v, int):
                        mk = 0
                    elif len(v) > 3 and re.search(r"alternative art", versions[v[2]] if v[2] < len(versions) else "", re.I) and v[3] in (1, 2, "SP"):
                        mk = v[3]
                    else:
                        continue
                    if len(bymk.get(mk, [])) == 1:
                        hints[key] = bymk[mk][0]
                if len(set(hints.values())) != len(hints):
                    hints = {}
            vals = [val(pg.get(p["idProduct"])) for p in prods]
            assegnati = {}
            # la Regular dev'essere la prima e la più economica
            base_ok = isinstance(vers[0][1], int) and vals[0] is not None and all(x is None or vals[0] <= x for x in vals[1:])
            if len(prods) == len(vers):
                seq = [x for x in vals if x is not None]
                crescente = all(x <= y for x, y in zip(seq, seq[1:]))
                for n, ((key, v), p) in enumerate(zip(vers, prods)):
                    if base_ok if (n == 0 and isinstance(v, int)) else crescente:
                        assegnati[key] = p["idProduct"]
            elif base_ok:
                assegnati[vers[0][0]] = prods[0]["idProduct"]
            # le indicazioni certe di CardTrader valgono più dell'ordine di Cardmarket
            if hints:
                conf += 1
                for key, cid in hints.items():
                    if key in assegnati and assegnati[key] != cid:
                        corr += 1
                        dettagli.append(f"   {code}: versione {key.split('~')[-1] if '~' in key else 'Regular'} corretta con CardTrader ({assegnati[key]} -> {cid})")
                    assegnati[key] = cid
                usati = set(hints.values())
                for key in list(assegnati):
                    if key not in hints and assegnati[key] in usati:
                        del assegnati[key]
            if len(set(assegnati.values())) != len(assegnati):
                assegnati = {}  # mai lo stesso prodotto per due versioni
            for key, cid in assegnati.items():
                out[key] = voce(pg.get(cid), cid)
                if ct:
                    pr = ct_prezzo(ct, cid)
                    if pr:
                        ctout[key] = pr
            ok += len(assegnati)
            dubbi += len(vers) - len(assegnati)
        chiavi = [k for vs in app.values() for k, _ in vs]
        nct = sum(1 for k in chiavi if ctout.get(k) and ctout[k][0] is not None)
        tot["ok"] += ok; tot["no"] += dubbi; tot["ct"] += nct
        report.append(f"{s['code']:8} {s['name'][:34]:34} Cardmarket {ok:3}/{ok + dubbi:3}  CardTrader {nct:3}"
                      + (f"  (confermate da CardTrader {conf}, corrette {corr})" if ct else ""))
        report.extend(dettagli)
    report.append(f"TOTALE versioni con prezzo Cardmarket {tot['ok']}/{tot['ok'] + tot['no']}, con prezzo CardTrader {tot['ct']}")

    res = {"d": guide.get("createdAt", "")[:10], "src": "Cardmarket", "sets": covered, "p": out}
    if ct:
        res["ct"] = {"d": time.strftime("%Y-%m-%d"), "sets": covered, "p": ctout}
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")))
    txt = "\n".join(report)
    print(txt)
    if a.report:
        Path(a.report).write_text(txt)


if __name__ == "__main__":
    main()
