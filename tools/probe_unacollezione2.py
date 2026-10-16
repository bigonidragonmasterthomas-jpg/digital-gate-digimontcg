"""Studio (solo lettura): scarica i moduli JS di unacollezione.it che disegnano i prezzi (logo del negozio + valore)."""
import os, re, urllib.parse, urllib.request

OUT = "analysis/una2"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36"}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode("utf-8", "replace")
home = get("https://unacollezione.it/")
idx = urllib.parse.urljoin("https://unacollezione.it/", re.search(r'src="(/assets/index-[^"]+\.js)"', home).group(1))
t = get(idx)
chunks = sorted(set(re.findall(r'assets/[A-Za-z0-9_.-]+\.js', t)))
print("moduli", len(chunks))
for c in chunks:
    try:
        s = get("https://unacollezione.it/" + c)
    except Exception as e:
        print("errore", c, e); continue
    if re.search(r"referenceMetrics|cardmarket|Cardmarket|providerLogo|-logo\.webp", s):
        open(f"{OUT}/" + os.path.basename(c), "w").write(s); print("salvato", c, len(s))
    if re.search(r"\.css$", c):
        pass
for css in re.findall(r'href="(/assets/[^"]+\.css)"', home):
    open(f"{OUT}/" + os.path.basename(css), "w").write(get(urllib.parse.urljoin("https://unacollezione.it/", css))); print("css", css)
