"""Prezzi Cardmarket per Digital Gate.

Legge i file pubblici di Cardmarket (catalogo carte singole + guida prezzi giornaliera,
gioco Digimon = 17) e abbina ogni versione dell'app al prodotto Cardmarket giusto.
Scrive src/prices.json.

Uso:
  python3 tools/cardmarket_prices.py [--dir CARTELLA_FILE] [--sets EX13,BT26] [--scarica] [--ct-dir CARTELLA] [--ct-scarica]

CardTrader (facoltativo): con il codice nel segreto CARDTRADER_TOKEN scarica, per ogni prodotto, carte ("blueprint") e
offerte. Ogni carta CardTrader indica il proprio prodotto Cardmarket (card_market_ids) e il tipo di versione nel numero
(EX13-014 = Regular, ...a = Alternate Art ★, ...rp = Rare Pull ★★, ...sp = Special Rare SP): serve per confermare o
correggere l'abbinamento Cardmarket e per il prezzo CardTrader = offerta più bassa in inglese, Near Mint, non gradata.

Regole di abbinamento (prudenti: nel dubbio nessun prezzo, mai un prezzo sbagliato):
- per ogni prodotto dell'app si cerca l'espansione Cardmarket in cui compaiono più carte con il suo codice set;
- per ogni numero di carta i prodotti Cardmarket vengono ordinati per idProduct (ordine di inserimento: V1, V2, ...);
- se il numero di versioni coincide con quello dell'app si abbinano nell'ordine dell'app (Regular, ★, ★★, SP);
  se i prezzi non salgono in quell'ordine (es. la ★ costa più della ★★) le alternative art restano senza prezzo;
- se il numero non coincide si abbina solo la versione Regular, e solo se è chiaramente la più economica.
"""
import argparse, json, os, re, time, urllib.request
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


CT_API = "https://api.cardtrader.com/api/v2"
CT_SUFFIX = {"": 0, "a": 1, "rp": 2, "sp": "SP"}
CT_NUM = re.compile(r"^([A-Z0-9]+-\d+)([a-z]*)$")


def ct_get(path):
    tok = os.environ.get("CARDTRADER_TOKEN", "").strip()
    req = urllib.request.Request(CT_API + path, headers={"Authorization": "Bearer " + tok, "User-Agent": "DigitalGate/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def ct_scarica(cartella, codici):
    """Espansioni Digimon (gioco 8), blueprint e offerte dei prodotti richiesti (solo campi utili, niente venditori)."""
    os.makedirs(cartella, exist_ok=True)
    exps = [e for e in ct_get("/expansions") if e.get("game_id") == 8]
    Path(cartella, "expansions_digimon.json").write_text(json.dumps(exps))
    for e in exps:
        if e.get("code", "").upper().replace("-", "") not in codici:
            continue
        Path(cartella, f"blueprints_{e['id']}.json").write_text(json.dumps(ct_get(f"/blueprints/export?expansion_id={e['id']}")))
        time.sleep(1.1)
        mk = ct_get(f"/marketplace/products?expansion_id={e['id']}")
        slim = {b: [{"price_cents": o.get("price", {}).get("cents"), "currency": o.get("price", {}).get("currency"), "qty": o.get("quantity"),
                     "props": o.get("properties_hash"), "graded": o.get("graded")} for o in offs] for b, offs in mk.items()}
        Path(cartella, f"market_{e['id']}.json").write_text(json.dumps(slim))
        time.sleep(1.1)


def ct_carica(cartella, codice):
    """Per un codice set: {cmid: blueprint}, {(numero, segno): cmid}, offerte per blueprint. None se mancano i file."""
    try:
        exps = json.loads(Path(cartella, "expansions_digimon.json").read_text())
    except Exception:
        return None
    e = next((x for x in exps if x.get("code", "").upper().replace("-", "") == codice), None)
    if not e or not Path(cartella, f"blueprints_{e['id']}.json").exists():
        return None
    bps = json.loads(Path(cartella, f"blueprints_{e['id']}.json").read_text())
    market = json.loads(Path(cartella, f"market_{e['id']}.json").read_text())
    cm2bp, hint = {}, {}
    for b in bps:
        cn = ((b.get("fixed_properties") or {}).get("collector_number") or "").strip()
        m = CT_NUM.match(cn)
        ids = b.get("card_market_ids") or []
        for cid in ids:
            cm2bp[cid] = b
        if m and m.group(2) in CT_SUFFIX and len(ids) == 1:
            k = (m.group(1), CT_SUFFIX[m.group(2)])
            hint[k] = None if k in hint else ids[0]  # due carte con lo stesso segno = ambiguo
    return {"exp": e["id"], "cm2bp": cm2bp, "hint": {k: v for k, v in hint.items() if v}, "market": market}


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
    ap.add_argument("--sets", default="EX13")
    ap.add_argument("--scarica", action="store_true")
    ap.add_argument("--ct-dir", default="cardtrader")
    ap.add_argument("--ct-scarica", action="store_true")
    a = ap.parse_args()
    if a.scarica:
        scarica(a.dir)
    if a.ct_scarica:
        ct_scarica(a.ct_dir, {x.strip().upper() for x in a.sets.split(",") if x.strip()})
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
    out, report, covered, ctout, ctcov = {}, [], [], {}, []
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
        ct = ct_carica(a.ct_dir, s["code"].upper())
        if ct:
            ctcov.append(s["id"])
        ok = dubbi = corretti = confermate = 0
        for code, vers in app.items():
            prods = sorted(cm.get(code, []), key=lambda p: p["idProduct"])
            if not prods:
                report.append(f"{code}: non trovata su Cardmarket")
                dubbi += len(vers)
                continue
            # indicazioni CardTrader: per ogni versione dell'app il prodotto Cardmarket corrispondente
            ids = {p["idProduct"] for p in prods}
            hints = {}
            if ct:
                for key, v in vers:
                    if isinstance(v, int):
                        mk = 0
                    elif re.search(r"alternative art", versions[v[2]] if v[2] < len(versions) else "", re.I) and v[3] in (1, 2, "SP"):
                        mk = v[3]
                    else:
                        continue
                    cid = ct["hint"].get((code, mk))
                    if cid in ids:
                        hints[key] = cid
            if hints and len(set(hints.values())) == len(hints) and len(hints) == len(vers):
                confermate += 1
                if [hints[k] for k, _ in vers] != [p["idProduct"] for p in prods[:len(vers)]]:
                    report.append(f"{code}: ordine Cardmarket diverso dalle versioni, sistemato con CardTrader")
                for key, v in vers:
                    out[key] = voce(pg.get(hints[key]), hints[key]); ok += 1
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
            # dove CardTrader indica con certezza il prodotto, quell'indicazione vale più dell'ordine di Cardmarket
            if hints and len(set(hints.values())) == len(hints):
                for key, cid in hints.items():
                    prima = out.get(key, [None] * 6)[5]
                    if prima != cid:
                        corretti += 1
                        if prima is None:
                            ok += 1; dubbi -= 1
                    out[key] = voce(pg.get(cid), cid)
                for key, v in vers:
                    if key not in hints and key in out and out[key][5] in hints.values():
                        del out[key]; ok -= 1; dubbi += 1
        report.append(f"== {s['code']} (espansione Cardmarket {best}): {ok} versioni con prezzo, {dubbi} senza"
                      + (f"; CardTrader espansione {ct['exp']}: {confermate} carte abbinate con certezza, {corretti} versioni corrette" if ct else ""))
        if ct:
            nct = 0
            for key, v in [x for vs in app.values() for x in vs]:
                if key in out:
                    pr = ct_prezzo(ct, out[key][5])
                    if pr:
                        ctout[key] = pr; nct += pr[0] is not None
            report.append(f"   CardTrader: {nct} versioni con prezzo (inglese, Near Mint)")

    res = {"d": guide.get("createdAt", "")[:10], "src": "Cardmarket", "sets": covered, "p": out}
    if ctcov:
        res["ct"] = {"d": time.strftime("%Y-%m-%d"), "sets": ctcov, "p": ctout}
    (ROOT / "src/prices.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")))
    print("\n".join(report))


if __name__ == "__main__":
    main()
