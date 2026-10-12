#!/usr/bin/env python3
"""Scarica dal sito ufficiale Bandai i loghi e gli artwork promozionali di tutte le espansioni del Digimon Card Game.

Fonte principale world.digimoncard.com (versione inglese globale); per ciò che manca prova le stesse cartelle su
en.digimoncard.com e digimoncard.com (Giappone). I prodotti presenti solo su questi due siti vengono aggiunti a parte.

Uso:  python3 tools/fetch_set_assets.py CARTELLA_OUT

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
    "confezione": (r"^img_pkg\.(?:png|webp|jpe?g)$", ["img_pkg.png", "img_pkg.webp"]),
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
        return found
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
    files = {}
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
            if kind.startswith("keyvisual"):
                cands += [u for u in shared if re.match(pattern, u.split("/images/products/", 1)[1].split("/", 2)[2], re.I)]
            for url in cands:
                data, im = fetch_image(url)
                if data is None:
                    continue
                ext = url.rsplit(".", 1)[1].lower().replace("jpeg", "jpg")
                out_dir.mkdir(parents=True, exist_ok=True)
                name = "%s.%s" % (kind, ext)
                (out_dir / name).write_bytes(data)
                files[kind] = {"file": "%s/%s" % (prod["key"], name), "url": url, "fonte": host,
                               "w": im.size[0], "h": im.size[1], "kb": round(len(data) / 1024)}
                break
    prod = dict(prod)
    prod["files"] = files
    return prod


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
    print("espansioni:", len(products), flush=True)
    with cf.ThreadPoolExecutor(8) as ex:
        done = list(ex.map(process, products.values()))
    done.sort(key=order_key)
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
          "Il sito non pubblica quasi mai i loghi come file separati: il logo si trova nel **key visual** (set recenti) e sempre "
          "sulla **confezione**. Elenco completo con fonti e dimensioni in `index.json`, foglio riassuntivo in `anteprima.jpg`.", ""]
    fam = None
    for p in index:
        f = p["file"]
        if p["codice"][:2] != fam:
            fam = p["codice"][:2]
            md += ["", "## " + TYPE_NAMES.get(fam, fam), "", "| Set | Artwork | Confezione |", "|---|---|---|"]
        main = next((f[k] for k in ("keyvisual", "banner", "promo", "keyvisual-verticale") if k in f), None)
        art = '<img src="%s" width="320">' % main["file"] if main else "—"
        pkg = '<img src="%s" width="70">' % f["confezione"]["file"] if "confezione" in f else "—"
        extra = ", ".join("[%s](%s)" % (k, v["file"]) for k, v in f.items())
        md.append("| **%s**<br>%s<br>%s<br>%s | %s | %s |" % (p["codice"], p["nome"], p["uscita"], extra, art, pkg))
    (OUT / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    # riepilogo
    from collections import Counter
    cnt = Counter(k for p in index for k in p["file"])
    print("file per tipo:", dict(cnt))
    no_art = [p["codice"] for p in index if not any(k in p["file"] for k in ("keyvisual", "banner", "promo", "keyvisual-verticale"))]
    print("::notice title=Loghi e artwork::%d espansioni, %d con artwork, %d con logo separato. Senza artwork: %s"
          % (len(index), len(index) - len(no_art), cnt.get("logo", 0), " ".join(no_art) or "nessuna"))
    for p in index:
        print(p["codice"].ljust(12), p["sito"].ljust(5), " ".join("%s:%s(%dx%d)" % (k, v["fonte"], v["w"], v["h"]) for k, v in p["file"].items()))


if __name__ == "__main__":
    main()
