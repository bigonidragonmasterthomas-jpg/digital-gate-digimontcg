"""Estrae dalla lista carte ufficiale EN (cardlist html) il lato Option delle carte Digimon/Option e il testo Overflow."""
import re, html, json, sys
s = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
out = {}
def clean(t):
    t = re.sub(r"<br\s*/?>", "\n", t); t = re.sub(r"<[^>]+>", "", t); t = html.unescape(t)
    return [re.sub(r"[ \t]+", " ", l).strip() for l in t.split("\n") if l.strip()]
for it in s.split('<li class="image_lists_item')[1:]:
    no = re.search(r'class="cardno">([^<]+)', it); ty = re.search(r'class="cardtype">([^<]+)', it)
    if not no: continue
    code = no.group(1).strip(); e = {}
    texts = re.findall(r"<dt>(Upper Text|Lower Text)</dt>\s*<dd>(.*?)</dd>", it, re.S)
    allt = [l for _, t in texts for l in clean(t)]
    if ty and ty.group(1).strip() == "Digimon/Option":
        low = [clean(t) for k, t in texts if k == "Lower Text"]
        lines = low[0] if low else []
        d = {"lines": []}
        for l in lines:
            m = re.match(r"\[DUAL Color\]\s*(.+)", l); n = re.match(r"\[DUAL Cost\]\s*(.+)", l)
            if m: d["color"] = m.group(1).strip()
            elif n: d["cost"] = n.group(1).strip()
            else: d["lines"].append(l)
        e["dual"] = d
    for l in allt:
        m = re.search(r"＜Overflow \((-\d+)\)＞\s*(\([^)]*\))", l)
        if m: e["ovf"] = [m.group(1), m.group(2)]
    if e: out.setdefault(code, {}).update(e)
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
print(len(out), sum(1 for v in out.values() if "dual" in v), sum(1 for v in out.values() if "ovf" in v))
