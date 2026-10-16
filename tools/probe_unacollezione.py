"""Studio (solo lettura) di come unacollezione.it mostra i prezzi Cardmarket: cerca 'cardmarket' nelle pagine
e negli script del sito e salva gli estratti e le immagini collegate in analysis/una/."""
import os, re, sys, urllib.parse, urllib.request

OUT = "analysis/una"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read()


pages = ["https://unacollezione.it/", "https://unacollezione.it/digimon", "https://unacollezione.it/tutti-i-set"] + sys.argv[1:]
seen, scripts, imgs = set(), [], set()
log = open(f"{OUT}/estratti.txt", "w")
for u in pages:
    try:
        h = get(u).decode("utf-8", "replace")
    except Exception as e:
        print("errore", u, e); continue
    open(f"{OUT}/" + re.sub(r"\W+", "_", u)[-60:] + ".html", "w").write(h)
    for m in re.finditer(r'(?:src|href)="([^"]+\.(?:js|css))"', h):
        s = urllib.parse.urljoin(u, m.group(1))
        if s not in seen:
            seen.add(s); scripts.append(s)
    for m in re.finditer(r".{0,300}cardmarket.{0,300}", h, re.I | re.S):
        log.write(f"\n=== {u}\n{m.group(0)}\n")
for s in scripts[:80]:
    try:
        t = get(s).decode("utf-8", "replace")
    except Exception as e:
        print("errore", s, e); continue
    hits = list(re.finditer(r".{0,400}cardmarket.{0,400}", t, re.I | re.S))
    if hits:
        open(f"{OUT}/" + os.path.basename(urllib.parse.urlparse(s).path), "w").write(t)
        print("trovato in", s, len(hits))
        for m in hits[:30]:
            log.write(f"\n=== {s}\n{m.group(0)}\n")
    for m in re.finditer(r'["\'(]([^"\'()\s]*cardmarket[^"\'()\s]*\.(?:svg|png|webp|jpg))', t, re.I):
        imgs.add(urllib.parse.urljoin(s, m.group(1)))
log.close()
for i in imgs:
    try:
        open(f"{OUT}/" + os.path.basename(urllib.parse.urlparse(i).path), "wb").write(get(i)); print("immagine", i)
    except Exception as e:
        print("errore immagine", i, e)
print("script", len(scripts), "immagini", len(imgs))
