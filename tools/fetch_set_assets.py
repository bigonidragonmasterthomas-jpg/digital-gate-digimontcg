#!/usr/bin/env python3
"""Scarica dal sito ufficiale Bandai i loghi e gli artwork promozionali di tutte le espansioni del Digimon Card Game.

Fonte principale world.digimoncard.com (versione inglese globale); per ciò che manca prova le stesse cartelle su
en.digimoncard.com e digimoncard.com (Giappone). I prodotti presenti solo su questi due siti vengono aggiunti a parte.

Uso:  python3 tools/fetch_set_assets.py CARTELLA_OUT [tutto]

Scarica solo il materiale NUOVO: se CARTELLA_OUT contiene già la raccolta precedente (index.json e file), i prodotti già
presenti non vengono riscaricati. Si cercano soltanto i prodotti nuovi e, per quelli recenti o non ancora usciti (ultimi
12 mesi), i tipi di immagine che ancora mancano. I file già salvati non vengono mai sostituiti. Con "tutto" rifà tutto da capo.
Per i file già salvati controlla però, senza scaricarli, se sul sito sono stati sostituiti (dimensione diversa): in quel caso
scrive CARTELLA_OUT/_segnalazione.md, che il workflow trasforma in una segnalazione (issue) su GitHub.
I loghi separati non vengono più cercati su siti esterni: si aggiungono a mano in src/logos/CODICE.webp.

Per ogni espansione crea CARTELLA_OUT/CODICE/ con i file che il sito pubblica:
  keyvisual.*          key visual orizzontale (1920x756) con il logo del set – set dal 2024 in poi
  keyvisual-verticale.* key visual verticale (750x1082) per telefono
  banner.*             banner promozionale (800x600) – soprattutto i set fino al 2023
  promo.*              immagine promozionale dei prodotti Limited / Premium Bandai
  confezione.*         bustina o confezione del prodotto (riporta sempre il logo)
  logo.*               logo separato, solo quando il sito lo pubblica come file a sé
e in CARTELLA_OUT: index.json (elenco completo con le fonti), README.md (galleria) e anteprima.jpg (foglio provini).
"""
import concurrent.futures as cf
import datetime
import os
import html as htmllib
import io
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "set-assets").resolve()
OUT.mkdir(parents=True, exist_ok=True)
FULL = len(sys.argv) > 2 and sys.argv[2] == "tutto"
NEW = []   # file scaricati in questa esecuzione
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
HOSTS = {"world": "https://world.digimoncard.com", "en": "https://en.digimoncard.com", "jp": "https://digimoncard.com"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
KEEP = ("BT", "EX", "ST", "RB", "AD", "LM", "PB")          # famiglie di prodotto considerate "espansioni"
SLUG_CODES = {"goods/special-limited-set": "LM01-05", "goods/nexus-of-digimon": "PB24"}  # prodotti senza codice nel nome
APP = {"BT1-3_v1.0": ["BT1", "BT2"], "BT1-3_v1.5": ["BT2", "BT3"], "BT18-19": ["BT18", "BT19"], "BT19-20": ["BT19", "BT20"]}
KINDS = {  # tipo -> (regex sul percorso relativo alla cartella del prodotto, nomi da provare se la pagina non li mostra)
    "keyvisual": (r"^(?:point/)?pc/mv\.(?:webp|jpe?g|png)$", ["point/pc/mv.webp", "point/pc/mv.jpg", "point/pc/mv.png", "pc/mv.png", "pc/mv.jpg"]),
    "keyvisual-verticale": (r"^(?:point/)?sp/mv\.(?:webp|jpe?g|png)$", ["point/sp/mv.webp", "point/sp/mv.jpg", "sp/mv.jpg"]),
    "banner": (r"^bnr\.(?:jpe?g|png|webp)$", ["bnr.jpg", "bnr.png", "bnr.webp"]),
    "promo": (r"^img_?01\.(?:jpe?g|webp)$", []),
    # bustina: img_pkg è la miniatura dell'elenco; nei set recenti la pagina ha anche una versione grande in point/NN/pkg
    "confezione": (r"^(?:img_pkg|point/\d+/pkg(?:_?0?1)?)\.(?:png|webp|jpe?g)$", ["img_pkg.png", "img_pkg.webp"]),
    "logo": (r"^(?:(?:point/)?pc/)?(?:img_)?(?:logo|title)\.(?:png|webp|svg)$", ["logo.png", "logo.webp", "point/pc/logo.png", "point/logo.png", "pc/title.png"]),
}
TYPE_NAMES = {"BT": "Booster", "EX": "Extra / Theme Booster", "RB": "Reboot Booster", "AD": "Advanced Booster",
              "ST": "Starter / Advanced Deck", "LM": "Limited", "PB": "Premium Bandai"}


def get(url, binary=False, timeout=20):
    for _ in range(2):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
            return data if binary else data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410):
                return None
        except Exception:
            pass
    return None


def clean(s):
    return htmllib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or ""))).strip()


def canonical(raw):
    m = re.match(r"([A-Z]{2})[\s-]?(\d+)([A-Z]?)(?:\s*-\s*(\d+))?$", raw.strip())
    if not m:
        return None
    p, a, suf, b = m.groups()
    if b:
        return "%s%d-%d" % (p, int(a), int(b))
    if p == "LM":
        return "LM%02d" % int(a)
    return "%s%d%s" % (p, int(a), suf)


def app_codes(key):
    if key in APP:
        return APP[key]
    m = re.match(r"([A-Z]{2})(\d+)-(\d+)$", key)
    if m and m.group(1) != "LM":
        return ["%s%d" % (m.group(1), i) for i in range(int(m.group(2)), int(m.group(3)) + 1)]
    return [key]


def is_recent(release):
    """Vero se il prodotto è uscito da non più di 12 mesi, deve ancora uscire o non ha una data leggibile."""
    m = re.search(r"(\d{4})", release or "")
    if not m:
        return True
    month = 12
    mm = re.search("|".join(MONTHS), release, re.I)
    jp = re.search(r"\d{4}年\s*(\d{1,2})月", release)
    if mm:
        month = MONTHS.index(mm.group(0).lower()) + 1
    elif jp:
        month = int(jp.group(1))
    today = datetime.date.today()
    return (today.year - int(m.group(1))) * 12 + (today.month - month) <= 12


def load_old():
    """Raccolta già presente in CARTELLA_OUT: {codice: prodotto con i file che esistono davvero}."""
    f = OUT / "index.json"
    if FULL or not f.exists():
        return {}
    try:
        idx = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}
    old = {}
    for e in idx:
        files = {k: v for k, v in (e.get("file") or {}).items() if (OUT / v["file"]).exists()}
        old[e["codice"]] = {"key": e["codice"], "name": e.get("nome", ""), "release": e.get("uscita", ""), "page": e.get("pagina"),
                            "site": e.get("sito", "world"), "files": files}
    return old


def listing(site):
    """Prodotti elencati in /products/ di un sito: nome, codice, pagina, cartella immagini, date."""
    base = HOSTS[site] + "/products/"
    h = get(base) or ""
    items = []
    for m in re.finditer(r"<article([^>]*)>(.*?)</article>", h, re.S):
        attrs, inner = m.groups()
        nm = re.search(r'class="prodname"[^>]*>(.*?)</h4>', inner, re.S)
        name = clean(nm.group(1)) if nm else ""
        du = re.search(r'data-url="([^"]*)"', attrs)
        href = du.group(1) if du and du.group(1) else None
        if not href:
            for a in re.findall(r"<a([^>]*)>", inner):
                hm = re.search(r'href="([^"]+)"', a)
                if hm and "unreleased" not in a and "cardlist" not in hm.group(1) and not hm.group(1).startswith("http"):
                    href = hm.group(1)
                    break
        img = re.search(r'<img[^>]+src="([^"]+)"', inner)
        page = urllib.parse.urljoin(base, href).split("#")[0] if href else None
        pkg = urllib.parse.urljoin(base, img.group(1)).split("?")[0] if img else None
        if pkg and "/images/products/" in pkg:
            folder = pkg.rsplit("/", 1)[0] + "/"
        elif page and "/products/" in page:
            folder = HOSTS[site] + "/images/products/" + re.sub(r"\.php$", "", page.split("/products/", 1)[1]).strip("/") + "/"
        else:
            continue
        slug = folder.split("/images/products/", 1)[1].strip("/")
        codes = re.findall(r"[\[【]\s*([A-Z]{2}[\s-]?\d+[A-Z]?(?:\s*-\s*\d+)?)\s*[\]】]", name)
        key = canonical(codes[-1]) if codes else SLUG_CODES.get(slug)
        if not key or not key.startswith(KEEP):
            continue
        dates = {clean(dt): clean(dd) for dt, dd in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", inner, re.S)}
        release = next((v for k, v in dates.items() if re.search(r"release|発売", k, re.I) and not re.search(r"pre", k, re.I)), "")
        if not release:
            release = next((v for v in dates.values() if re.search(r"\d{4}", v) and not re.search(r"USD|円", v)), "")
        ver = re.search(r"Ver\.?\s*(\d+\.\d+)", name, re.I)
        items.append({"key": key, "name": re.sub(r"^(DIGIMON CARD GAME|デジモンカードゲーム)\s*", "", name), "site": site,
                      "page": page, "rel_folder": folder.split(HOSTS[site], 1)[1], "release": release, "ver": ver.group(1) if ver else ""})
    # stesso codice due volte (es. BT01-03 Ver.1.0 e Ver.1.5): distingui con la versione
    seen = {}
    for it in items:
        seen.setdefault(it["key"], []).append(it)
    for key, group in seen.items():
        if len(group) > 1:
            for it in group:
                if it["ver"]:
                    it["key"] = "%s_v%s" % (key, it["ver"])
    return items


def scan_page(host, rel_page, rel_folder):
    """Immagini della cartella del prodotto citate nella pagina (html + css del prodotto)."""
    found = []
    h = get(HOSTS[host] + rel_page) if rel_page else None
    if not h:
        return [], []
    page_url = HOSTS[host] + rel_page
    texts = [(page_url, h)]
    for c in dict.fromkeys(re.findall(r'href=["\']([^"\']+\.css[^"\']*)', h)):
        cu = urllib.parse.urljoin(page_url, c)
        if "/products/" in cu and cu.startswith(HOSTS[host]):
            ch = get(cu)
            if ch:
                texts.append((cu, ch))
    folder = HOSTS[host] + rel_folder
    # cartelle condivise da due prodotti usciti insieme (es. deck/st18-19/ per ST18 e ST19)
    num = re.search(r"(\d+)/$", rel_folder)
    parent = HOSTS[host] + rel_folder.rstrip("/").rsplit("/", 1)[0] + "/"
    shared = []
    for src, t in texts:
        refs = re.findall(r'(?:src|data-src|srcset|href|content)=["\']([^"\']+)', t) + re.findall(r'url\(\s*["\']?([^"\')]+)', t)
        for r in refs:
            for part in r.split(","):
                u = urllib.parse.urljoin(src, part.strip().split(" ")[0]).split("?")[0]
                if not re.search(r"\.(png|jpe?g|webp|svg)$", u, re.I):
                    continue
                if u.startswith(folder):
                    found.append(u[len(folder):])
                elif num and u.startswith(parent):
                    sub = u[len(parent):].split("/", 1)
                    if len(sub) == 2 and re.search(r"\d+-\d+$", sub[0]) and re.search(r"(?<!\d)0?%d(?!\d)" % int(num.group(1)), sub[0]):
                        shared.append(u)
    return list(dict.fromkeys(found)), list(dict.fromkeys(shared))


def fetch_image(url):
    b = get(url, binary=True, timeout=30)
    if not b:
        return None, None
    try:
        im = Image.open(io.BytesIO(b))
        im.load()
        if min(im.size) < 40:
            return None, None
        return b, im
    except Exception:
        return None, None


def process(prod):
    """Trova e scarica, per ogni tipo, la migliore immagine disponibile (prima world, poi en, poi jp)."""
    order = [prod["site"]] + [s for s in ("world", "en", "jp") if s != prod["site"]]
    pages = {prod["site"]: prod["page"].split(HOSTS[prod["site"]], 1)[1]} if prod["page"] else {}
    for s in order:
        pages.setdefault(s, pages.get(prod["site"]))
    out_dir = OUT / prod["key"]
    files = dict(prod.get("have") or {})   # già salvati: non si riscaricano
    for host in order:
        missing = [k for k in KINDS if k not in files]
        if not missing:
            break
        rels, shared = scan_page(host, pages.get(host), prod["rel_folder"])
        base = HOSTS[host] + prod["rel_folder"]
        for kind in missing:
            pattern, probes = KINDS[kind]
            if kind == "promo" and not prod["key"].startswith(("LM", "PB")):
                continue
            cands = [base + r for r in rels if re.match(pattern, r, re.I)] + [base + p for p in probes if p not in rels]
            if kind == "logo":  # un file che si chiama "logo" batte un "title"
                cands.sort(key=lambda u: "logo" not in u.rsplit("/", 1)[1])
            if kind.startswith("keyvisual"):
                cands += [u for u in shared if re.match(pattern, u.split("/images/products/", 1)[1].split("/", 2)[2], re.I)]
            if kind == "confezione":  # tra le versioni disponibili tieni la più grande
                got = [(u,) + fetch_image(u) for u in dict.fromkeys(cands)]
                got = [g for g in got if g[1] is not None]
                got.sort(key=lambda g: -g[2].size[0] * g[2].size[1])
                cands = [g[0] for g in got[:1]]
            for url in cands:
                data, im = fetch_image(url)
                if data is None:
                    continue
                ext = url.rsplit(".", 1)[1].lower().replace("jpeg", "jpg")
                out_dir.mkdir(parents=True, exist_ok=True)
                name = "%s.%s" % (kind, ext)
                (out_dir / name).write_bytes(data)
                NEW.append("%s/%s" % (prod["key"], name))
                files[kind] = {"file": "%s/%s" % (prod["key"], name), "url": url, "fonte": host,
                               "w": im.size[0], "h": im.size[1], "kb": round(len(data) / 1024)}
                break
    prod = dict(prod)
    prod["files"] = files
    return prod


def add_own_logos(done):
    """Loghi forniti a mano (src/logos/CODICE.webp): hanno la precedenza su tutte le altre fonti."""
    src = pathlib.Path(__file__).resolve().parent.parent / "src" / "logos"
    for p in done:
        f = src / (p["key"] + ".webp")
        if not f.exists():
            continue
        data = f.read_bytes()
        im = Image.open(io.BytesIO(data))
        im.load()
        (OUT / p["key"]).mkdir(parents=True, exist_ok=True)
        if (OUT / p["key"] / "logo.webp").exists() and (OUT / p["key"] / "logo.webp").read_bytes() == data:
            continue
        for old in (OUT / p["key"]).glob("logo.*"):
            old.unlink()
        (OUT / p["key"] / "logo.webp").write_bytes(data)
        NEW.append("%s/logo.webp" % p["key"])
        p["files"]["logo"] = {"file": "%s/logo.webp" % p["key"], "url": "src/logos/%s.webp" % p["key"], "fonte": "utente",
                              "w": im.size[0], "h": im.size[1], "kb": round(len(data) / 1024)}
    print("loghi forniti a mano: %d" % sum(1 for p in done if p["files"].get("logo", {}).get("fonte") == "utente"))


def head(url):
    """Dimensione e data di modifica dichiarate dal sito, senza scaricare il file."""
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA, method="HEAD"), timeout=20)
        n = r.headers.get("Content-Length") or ""
        return (int(n) if n.isdigit() else None, r.headers.get("Last-Modified") or "")
    except Exception:
        return (None, "")


def check_changes(done):
    """Materiale già salvato che sul sito ufficiale è stato sostituito: confronta la dimensione dichiarata dal sito con
    quella del file salvato (nessuno scaricamento). Il file salvato non viene toccato; ogni cambiamento è segnalato una volta sola."""
    items = [(p, k, v) for p in done for k, v in p["files"].items()
             if v.get("fonte") in HOSTS and str(v.get("url", "")).startswith("http") and v["file"] not in NEW and (OUT / v["file"]).exists()]
    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda it: head(it[2]["url"]), items))
    changed, seen = [], 0
    for (p, k, v), (n, mod) in zip(items, res):
        if n is None:
            continue
        seen += 1
        local = (OUT / v["file"]).stat().st_size
        if n == local:
            v.pop("segnalato", None)
        elif v.get("segnalato") != n:
            v["segnalato"] = n
            changed.append((p["key"], p["name"], k, v["url"], local, n, mod))
    print("controllo aggiornamenti: %d file verificati sul sito, %d cambiati" % (seen, len(changed)), flush=True)
    if os.environ.get("SEGNALA_PROVA") and items and not changed:   # prova della segnalazione, senza toccare l'indice
        p, k, v = items[0]
        changed.append((p["key"], p["name"] + " (PROVA: nessun cambiamento reale)", k, v["url"], (OUT / v["file"]).stat().st_size, 0, ""))
    if changed:
        md = ["Il controllo settimanale ha trovato materiale promozionale che sul sito ufficiale Bandai è stato **sostituito** "
              "rispetto alla copia salvata nel ramo `set-assets`. La copia salvata **non è stata modificata**.", "",
              "| Prodotto | Immagine | Salvata | Sul sito | Modificata sul sito |", "|---|---|---|---|---|"]
        for key, name, k, url, a, b, mod in changed:
            md.append("| **%s** %s | [%s](%s) | %d KB | %d KB | %s |" % (key, name, k, url, round(a / 1024), round(b / 1024), mod or "—"))
        md += ["", "Per prendere le versioni nuove: Actions → *Loghi e artwork set* → *Run workflow* con l'opzione **tutto** "
               "(riscarica l'intera raccolta). Se le versioni salvate vanno bene così, basta chiudere questa segnalazione: "
               "lo stesso cambiamento non verrà segnalato di nuovo."]
        (OUT / "_segnalazione.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def contact_sheet(products, path):
    """Foglio provini: per ogni espansione l'artwork principale e la confezione."""
    cw, ch, cols = 400, 210, 4
    rows = (len(products) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (11, 17, 32))
    dr = ImageDraw.Draw(sheet)
    for i, p in enumerate(products):
        x, y = (i % cols) * cw, (i // cols) * ch
        f = p["files"]
        main = next((f[k] for k in ("keyvisual", "banner", "promo", "keyvisual-verticale") if k in f), None)
        if main:
            im = Image.open(OUT / main["file"]).convert("RGB")
            im.thumbnail((300, 175))
            sheet.paste(im, (x + 6, y + 6))
        if "confezione" in f:
            im = Image.open(OUT / f["confezione"]["file"]).convert("RGBA")
            im.thumbnail((80, 175))
            sheet.paste(im, (x + 312, y + 6), im)
        tag = "%s  %s" % (p["key"], "".join(k[0].upper() for k in ("keyvisual", "banner", "logo") if k in f))
        dr.text((x + 6, y + 186), tag, fill=(255, 255, 255))
        dr.text((x + 6, y + 198), p["name"][:60], fill=(160, 170, 190))
    sheet.save(path, quality=72, optimize=True)


def order_key(p):
    m = re.match(r"([A-Z]{2})(\d+)", p["key"])
    fam = KEEP.index(m.group(1)) if m else 99
    return (fam, -int(m.group(2)) if m else 0, p["key"])


def main():
    products = {}
    covered = set()
    for site in ("world", "en", "jp"):
        items = listing(site)
        print("%s: %d prodotti" % (site, len(items)), flush=True)
        for it in items:
            codes = app_codes(it["key"])
            plain = {c.rstrip("E") for c in codes}
            if it["key"] in products or (site != "world" and plain & covered):
                continue
            products[it["key"]] = it
            covered |= plain
    old = load_old()
    todo, done = [], []
    for key, it in products.items():
        o = old.get(key)
        if o is None:                                        # prodotto nuovo: si scarica tutto
            todo.append(it)
        elif is_recent(it["release"] or o["release"]):       # recente o in arrivo: si cercano solo i tipi che mancano
            it["have"] = o["files"]
            todo.append(it)
        else:                                                # vecchio: resta com'è, nessuno scaricamento
            done.append(dict(it, files=o["files"]))
    done += [o for key, o in old.items() if key not in products]   # non più in elenco sul sito: resta com'è
    print("espansioni: %d sul sito, %d già in raccolta; da controllare: %d (%d nuove)"
          % (len(products), len(old), len(todo), sum(1 for it in todo if "have" not in it)), flush=True)
    with cf.ThreadPoolExecutor(8) as ex:
        done += list(ex.map(process, todo))
    done.sort(key=order_key)
    add_own_logos(done)
    if not FULL:
        check_changes(done)
    index = []
    for p in done:
        index.append({"codice": p["key"], "codici_app": app_codes(p["key"]), "nome": p["name"], "uscita": p["release"],
                      "tipo": TYPE_NAMES.get(p["key"][:2], ""), "pagina": p["page"], "sito": p["site"], "file": p["files"]})
    json.dump(index, open(OUT / "index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    contact_sheet(done, OUT / "anteprima.jpg")
    # galleria leggibile direttamente su GitHub
    md = ["# Loghi e artwork delle espansioni – Digimon Card Game", "",
          "Immagini scaricate automaticamente dal sito ufficiale Bandai (world.digimoncard.com; dove manca, en.digimoncard.com "
          "o digimoncard.com). Il copyright di artwork e loghi è di Bandai / Toei Animation: usale solo per scopi personali "
          "o con il loro permesso.", "",
          "Il sito Bandai non pubblica i **loghi trasparenti** (`logo.*`) come file separati: quelli con fonte `utente` in `index.json` "
          "sono stati forniti a mano (cartella `src/logos/` del progetto) e hanno la precedenza; quelli con fonte `unacollezione` sono "
          "copie salvate in passato da unacollezione.it, che non viene più consultato. "
          "Elenco completo con fonti e dimensioni in `index.json`, foglio riassuntivo in `anteprima.jpg`.", ""]
    fam = None
    for p in index:
        f = p["file"]
        if p["codice"][:2] != fam:
            fam = p["codice"][:2]
            md += ["", "## " + TYPE_NAMES.get(fam, fam), "", "| Set | Logo | Artwork | Confezione |", "|---|---|---|---|"]
        main = next((f[k] for k in ("keyvisual", "banner", "promo", "keyvisual-verticale") if k in f), None)
        art = '<img src="%s" width="320">' % main["file"] if main else "—"
        pkg = '<img src="%s" width="70">' % f["confezione"]["file"] if "confezione" in f else "—"
        extra = ", ".join("[%s](%s)" % (k, v["file"]) for k, v in f.items())
        logo = '<img src="%s" width="200">' % f["logo"]["file"] if "logo" in f else "—"
        md.append("| **%s**<br>%s<br>%s<br>%s | %s | %s | %s |" % (p["codice"], p["nome"], p["uscita"], extra, logo, art, pkg))
    (OUT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    # riepilogo
    from collections import Counter
    cnt = Counter(k for p in index for k in p["file"])
    print("file per tipo:", dict(cnt))
    print("::notice title=Materiale nuovo::%d file scaricati%s" % (len(NEW), ": " + " ".join(sorted(NEW)) if NEW else ""))
    no_art = [p["codice"] for p in index if not any(k in p["file"] for k in ("keyvisual", "banner", "promo", "keyvisual-verticale"))]
    print("::notice title=Loghi e artwork::%d espansioni, %d con artwork, %d con logo separato. Senza artwork: %s"
          % (len(index), len(index) - len(no_art), cnt.get("logo", 0), " ".join(no_art) or "nessuna"))
    for p in index:
        print(p["codice"].ljust(12), p["sito"].ljust(5), " ".join("%s:%s(%dx%d)" % (k, v["fonte"], v["w"], v["h"]) for k, v in p["file"].items()))


if __name__ == "__main__":
    main()
