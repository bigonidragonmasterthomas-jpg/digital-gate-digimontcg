"""Prova CardTrader: verifica il codice (segreto CARDTRADER_TOKEN, mai stampato), trova Digimon e un'espansione,
e salva in analysis/cardtrader/ giochi, espansioni Digimon, blueprint e offerte (solo i campi utili, niente venditori).
Uso: python3 tools/probe_cardtrader.py EX13"""
import json, os, sys, time, urllib.request, urllib.error

TOKEN = os.environ.get("CARDTRADER_TOKEN", "").strip()
API = "https://api.cardtrader.com/api/v2"
OUT = "analysis/cardtrader"
os.makedirs(OUT, exist_ok=True)


def get(path):
    req = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + TOKEN, "User-Agent": "DigitalGate/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def save(name, obj):
    json.dump(obj, open(f"{OUT}/{name}", "w"), ensure_ascii=False, indent=1)


def main():
    code = (sys.argv[1] if len(sys.argv) > 1 else "EX13").upper()
    if not TOKEN:
        print("ERRORE: il segreto CARDTRADER_TOKEN non è arrivato al workflow"); return
    try:
        info = get("/info")
        print("codice valido:", {k: info.get(k) for k in ("name", "id") if k in info})
    except urllib.error.HTTPError as e:
        print("ERRORE codice:", e.code, e.reason); return
    games = get("/games")
    games = games.get("array", games) if isinstance(games, dict) else games
    save("games.json", games)
    dg = [g for g in games if "digimon" in json.dumps(g).lower()]
    print("giochi Digimon:", dg)
    if not dg:
        return
    gid = dg[0]["id"]
    exps = [e for e in get("/expansions") if e.get("game_id") == gid]
    save("expansions_digimon.json", exps)
    print("espansioni Digimon:", len(exps))
    cand = [e for e in exps if code.lower() in (e.get("code", "") + " " + e.get("name", "")).lower().replace("-", "")]
    print("candidate", code, ":", cand[:10])
    for e in cand[:3]:
        bps = get(f"/blueprints/export?expansion_id={e['id']}")
        save(f"blueprints_{e['id']}.json", bps)
        print("blueprint", e["id"], len(bps))
        time.sleep(1.2)
        mk = get(f"/marketplace/products?expansion_id={e['id']}")
        slim = {}
        for bid, offers in mk.items():
            slim[bid] = [{
                "price_cents": o.get("price", {}).get("cents"), "currency": o.get("price", {}).get("currency"),
                "qty": o.get("quantity"), "props": o.get("properties_hash"), "graded": o.get("graded"),
            } for o in offers]
        save(f"market_{e['id']}.json", slim)
        print("offerte", e["id"], "carte con offerte:", len(slim), "totale offerte:", sum(len(v) for v in slim.values()))
        time.sleep(1.2)


if __name__ == "__main__":
    main()
