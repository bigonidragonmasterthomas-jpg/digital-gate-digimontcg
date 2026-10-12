#!/usr/bin/env python3
"""Caratteristiche dei prodotti dal sito ufficiale Bandai (data di uscita, prezzo, tipi di carte, rarità, contenuto).
Parte dall'indice del ramo "set-assets" (index.json: codice prodotto, codici dell'app, pagina ufficiale) e salva
src/products.json, con una voce per ogni codice set dell'app. Correzioni a mano in tools/product_fixes.json.
Uso: python3 tools/fetch_products.py [cartella con le pagine già scaricate CODICE.html]"""
import html, json, os, pathlib, re, sys, urllib.parse, urllib.request
root = pathlib.Path(__file__).resolve().parent.parent
INDEX = "https://raw.githubusercontent.com/knightofgemini/digital-gate-digimontcg/set-assets/index.json"
cache = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and pathlib.Path(sys.argv[1]).is_dir() else None
# set dell'app presenti in due prodotti: quale pagina usare
PREFER = {"BT19": "BT18-19", "BT2": "BT1-3_v1.0"}
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
DATE = re.compile(r"\b(" + "|".join(MONTHS) + r")\b\.?,?\s*(?:(\d{1,2})(?:st|nd|rd|th)?\b)?,?\s*(\d{4})", re.I)
SOFT = "\x01"

def get(u):
    try:
        return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        print("ERR", u, e); return ""

def to_lines(h):
    h = re.sub(r"<!--.*?-->", "", h, flags=re.S)
    h = re.sub(r"<(script|style)\b.*?</\1>", "", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>", SOFT, h, flags=re.I)
    h = re.sub(r"<li\b[^>]*class=\"[^\"]*asterisk[^\"]*\"[^>]*>", "\n*", h, flags=re.I)
    h = re.sub(r"</?(dt|dd|dl|li|ul|ol|p|div|tr|td|th|table|h\d|section|header|footer|nav)\b[^>]*>", "\n", h, flags=re.I)
    h = html.unescape(re.sub(r"<[^>]+>", "", h)).replace("　", " ").replace("\xa0", " ")
    out = []
    for l in h.split("\n"):
        l = re.sub(r"\s+", " ", l).strip()
        l = re.sub(r"^(?:" + SOFT + r"\s*)+|(?:\s*" + SOFT + r")+$", "", l).strip()
        if l: out.append(l)
    return out

LABELS = [("pre", re.compile(r"^pre-?release date\b", re.I)),
          ("rel", re.compile(r"^release date(\s*\(for [^)]*\))?\s*:?$", re.I)),
          ("ship", re.compile(r"^scheduled shipping date(\s*\(for [^)]*\))?\s*:?$", re.I)),
          ("unit", re.compile(r"^1 ?(pack|deck|set|box)( of \d+ cards)?$", re.I)),
          ("price", re.compile(r"^(msrp\b|manufacturer.s suggested retail price)", re.I)),
          ("types", re.compile(r"^card types?\s*:?$", re.I)),
          ("rar", re.compile(r"^rarity\s*:?$", re.I)),
          ("cont", re.compile(r"^contents?\s*:?$", re.I)),
          ("skip", re.compile(r"^(product name|tournament legal date)\b", re.I))]
STOP = re.compile(r"^([*※]|apology$|premium bandai|photos and actual|product specifications|prices? (is|are) |this product (is|contains|features) |card list$|questionnaire$|return to products|please check|pre-order|booster packs?$|official social|view more$|contents open$|point ?\d)", re.I)

def fields(lines):
    """Ogni etichetta raccoglie le righe che la seguono; vale l'ultimo blocco della pagina (la scheda in fondo)."""
    f, cur = {}, None
    for l in lines:
        plain = l.replace(SOFT, " ")
        plain = re.sub(r"\s+", " ", plain).strip()
        key = next((k for k, rx in LABELS if rx.search(plain)), None)
        if key:
            cur = key; f[cur] = [l]; continue
        if cur is None: continue
        if STOP.search(plain) or len(plain) > 170 or len(f[cur]) > 12:
            cur = None; continue
        f[cur].append(l)
    return f

def flat(ls): return re.sub(r"\s+", " ", " ".join(ls).replace(SOFT, " ")).strip()

def dates(ls, label_rx):
    """[[regione, 'AAAA-MM-GG' oppure 'AAAA-MM'], ...]"""
    head = flat(ls[:1]); t = flat(ls)
    m = re.search(r"\(for ([^)]+)\)", head, re.I); base = m.group(1).strip() if m else ""
    t = label_rx.sub("", t, count=1)
    t = re.sub(r"^\s*\([^)]*\)", "", t)
    out, pos = [], 0
    for m in DATE.finditer(t):
        reg = re.sub(r"[()*:|]", " ", t[pos:m.start()])
        reg = re.sub(r"\s+", " ", reg).strip(" ,/;.-")
        reg = re.sub(r"\s*/\s*", "/", reg)
        if re.search(r"varies|check", reg, re.I): reg = ""
        d = "%s-%02d" % (m.group(3), MONTHS.index(m.group(1).lower()) + 1) + ("-%02d" % int(m.group(2)) if m.group(2) else "")
        out.append([reg or base, d]); pos = m.end()
    return out

def price(ls):
    t = flat(ls)
    m = re.search(r"\$?\s*(\d[\d,]*(?:\.\d+)?)\s*USD", t, re.I)
    if m: return ["USD", m.group(1).replace(",", "")]
    m = re.search(r"(\d[\d,]*)\s*(?:yen|円)", t, re.I)
    if m: return ["JPY", m.group(1).replace(",", "")]
    return None

def contents(ls):
    out = []
    for l in ls[1:]:
        l = re.sub(r"\s+", " ", l.replace(SOFT, " ")).strip()
        for part in re.split(r"・|(?<=\.)\s+(?=\d)", l):
            part = part.strip(" ・")
            if not part: continue
            if part.startswith("(") and out: out[-1] += " " + part
            else: out.append(part)
    return out

def parse(page):
    f = fields(to_lines(page)); p = {}
    whole = flat(to_lines(page))
    rel = []
    for k in ("ship", "rel"):
        if k in f: rel += dates(f[k], re.compile(r"^(release|scheduled shipping) date", re.I))
    if rel: p["rel"] = rel
    if not p.get("rel"):
        m = re.search(r"Release Date\s*:\s*([A-Za-z]+\.?,?\s*(?:\d{1,2},?\s*)?\d{4})", whole, re.I)
        if m: p["rel"] = dates(["x", m.group(1)], re.compile("^x"))
    if "pre" in f:
        d = dates(f["pre"], LABELS[0][1])
        if d: p["pre"] = d[0][1]
    pr = None
    for k in ("price", "unit"):
        if k in f and not pr: pr = price(f[k])
    if not pr:
        m = re.search(r"MSRP\s*:?\s*\$?\s*(\d[\d,]*(?:\.\d+)?)\s*USD", whole, re.I)
        if m: pr = ["USD", m.group(1).replace(",", "")]
    if pr:
        if "unit" in f:
            m = re.match(r"1 ?(pack|deck|set|box)", flat(f["unit"][:1]), re.I)
            if m: pr.append(m.group(1).lower())
        p["price"] = pr
    if "types" in f and len(f["types"]) > 1: p["types"] = flat(f["types"][1:])
    if "rar" in f:
        r = [[re.sub(r"\s+", " ", a).strip(" ・,"), int(b)] for a, b in re.findall(r"([A-Za-z0-9][A-Za-z0-9 .\-]*?)\s*:\s*(\d+)\s*types?", flat(f["rar"][1:]))]
        for x in r:
            if x[0] == "Ultimate Rate": x[0] = "Ultimate Rare"
        if r: p["rar"] = r
    if "cont" in f:
        c = contents(f["cont"])
        if c: p["cont"] = c
    return p

def pack_image(page, url, e):
    """Immagine della confezione: img_pkg della pagina (quella del prodotto, se la pagina ne mostra due); ripiego: indice set-assets."""
    c = list(dict.fromkeys(re.findall(r"[\"'(]([^\"'() ?]*img_pkg\.(?:png|jpg|webp))", page, re.I)))
    slug = [s for s in url.split("/") if s][-1].replace(".php", "")
    c.sort(key=lambda x: slug not in x)
    if c: return urllib.parse.urljoin(url, c[0])
    return e.get("file", {}).get("confezione", {}).get("url")

def main():
    idx = json.loads((cache / "index.json").read_text(encoding="utf-8")) if cache and (cache / "index.json").exists() else json.loads(get(INDEX))
    fixes = json.load(open(root / "tools" / "product_fixes.json", encoding="utf-8"))
    out, raw = {}, []
    for e in idx:
        code = e["codice"]
        page = (cache / (code + ".html")).read_text(encoding="utf-8", errors="replace") if cache and (cache / (code + ".html")).exists() else get(e["pagina"])
        p = parse(page) if page else {}
        p["k"] = code; p["url"] = e["pagina"]
        pk = pack_image(page, e["pagina"], e)
        if pk: p["pk"] = pk
        raw.append(code + " " + json.dumps(p, ensure_ascii=False))
        for app in e.get("codici_app") or [code]:
            if app in out and PREFER.get(app, code) != code: continue
            out[app] = dict(p)
    for app, fx in fixes.items():
        if app.startswith("_"): continue
        out.setdefault(app, {}).update(fx)
        for k in [k for k, v in out[app].items() if v is None]: del out[app][k]
    txt = "{\n" + ",\n".join(json.dumps(k, ensure_ascii=False) + ":" + json.dumps(v, ensure_ascii=False, separators=(",", ":")) for k, v in out.items()) + "\n}\n"
    (root / "src" / "products.json").write_text(txt, encoding="utf-8")
    if os.environ.get("GITHUB_ACTIONS"):
        an = root / "analysis"; an.mkdir(exist_ok=True)
        (an / "products.json").write_text(txt, encoding="utf-8")
    print("\n".join(raw))
    miss = [k for k, v in out.items() if not v.get("rel")]
    print(len(out), "prodotti; senza data:", " ".join(miss) or "-")

main()
