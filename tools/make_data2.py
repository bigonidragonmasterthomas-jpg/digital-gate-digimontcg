import json,re,collections
SP="/tmp/claude-0/-home-claude/29c59d16-e198-5a70-803e-bf6b7cc866d0/scratchpad/build/"
src=json.load(open("/home/claude/TakaOtaku_Digimon-Card-App/src/assets/cardlists/PreparedDigimonCardsENG.json",encoding="utf-8"))
def nat(s): return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)',s.lower())]
def cl(v):
    v=(v or "").strip() if isinstance(v,str) else ""
    return "" if v in ("-","–") else v
# base cards: one per cardNumber, prefer id==cardNumber
best={}
for k in src:
    n=k["cardNumber"].strip()
    if n not in best or (k["id"]==n and best[n]["id"]!=n): best[n]=k
NAMES={ # prefix -> set name
 "BT1":"Release Special Booster Ver.1.0","BT2":"Release Special Booster Ver.1.0 / 1.5","BT3":"Release Special Booster Ver.1.5",
 "BT4":"Great Legend","BT5":"Battle of Omni","BT6":"Double Diamond","BT7":"Next Adventure","BT8":"New Awakening","BT9":"X Record",
 "BT10":"Xros Encounter","BT11":"Dimensional Phase","BT12":"Across Time","BT13":"Versus Royal Knights","BT14":"Blast Ace",
 "BT15":"Exceed Apocalypse","BT16":"Beginning Observer","BT17":"Secret Crisis","BT18":"Special Booster Ver.2.0",
 "BT19":"Special Booster Ver.2.0 / 2.5","BT20":"Special Booster Ver.2.5","BT21":"World Convergence","BT22":"Cyber Eden",
 "BT23":"Hackers' Slumber","BT24":"Time Stranger","BT25":"Dual Revolution","BT26":"Timeless Bonds",
 "EX1":"Classic Collection","EX2":"Digital Hazard","EX3":"Draconic Roar","EX4":"Alternative Being","EX5":"Animal Colosseum",
 "EX6":"Infernal Ascension","EX7":"Digimon Liberator","EX8":"Chain of Liberation","EX9":"Versus Monsters","EX10":"Sinister Order",
 "EX11":"Dawn of Liberator","EX12":"Digital World Shambala","EX13":"Chivalrous XIII",
 "ST1":"Gaia Red","ST2":"Cocytus Blue","ST3":"Heaven's Yellow","ST4":"Giga Green","ST5":"Machine Black","ST6":"Venomous Violet",
 "ST7":"Gallantmon","ST8":"Ulforce Veedramon","ST9":"Ultimate Ancient Dragon","ST10":"Parallel World Tactician","ST12":"Jesmon",
 "ST13":"Ragnaloardmon","ST14":"Beelzemon Advanced Deck Set","ST15":"Dragon of Courage","ST16":"Wolf of Friendship",
 "ST17":"Double Typhoon Advanced Deck Set","ST18":"Guardian Vortex","ST19":"Fable Waltz","ST20":"Protector of Light","ST21":"Hero of Hope",
 "ST22":"Amethyst Mandala Advanced Deck Set","ST23":"Beatbreak","ST24":"Data Squad",
 "LM01-05":"Special Limited Set","LM03":"Limited Card Set 2024","LM04":"Torridvice","LM06":"Billion Bullet","LM07":"Another Knight","LM08":"Final Crest","AD1":"Digimon Generation","RB1":"Resurgence Booster","P":"Promotional Cards"}
def gtype(p):
    if p.startswith("BT"): return "BT"
    if p.startswith("EX"): return "EX"
    if p.startswith("ST"): return "ST"
    if p.startswith("LM"): return "LM"
    return "AL"
rows=[]; cnt=collections.Counter(); missing=set()
for n,k in best.items():
    p=n.split("-")[0]
    if p=="LM":
        num=int(n.split("-")[1])
        if num>62: continue  # LM-09 Distancia Cero: non ancora uscito
        p="LM01-05" if num<=44 else "LM06" if num<=50 else "LM07" if num<=56 else "LM08"
    if p not in NAMES: missing.add(p)
    evo=[]
    for c in k.get("digivolveCondition") or []:
        evo.append(("Lv."+str(c.get("level",""))+" "+str(c.get("color","")) + ": " + str(c.get("cost",""))).strip())
    extra=[]
    for lab,key in (("Digievoluzione speciale","specialDigivolve"),("DNA Digivolve","dnaDigivolve"),("Digi-Xros","digiXros"),("Burst Digivolve","burstDigivolve"),("Assembly","assembly"),("Effetto ACE","aceEffect"),("Regola","rule"),("Link","linkEffect")):
        v=cl(k.get(key))
        if v: extra.append(lab+": "+v)
    ct=cl(k["cardType"]) or "Altro"
    lv=cl(k.get("cardLv")); lv = lv if re.match(r"Lv\.\d",lv) else ""
    rows.append([n,k["name"]["english"].strip(),lv,cl(k["color"]),ct,cl(k["form"]),cl(k["attribute"]),cl(k["type"]),cl(k["dp"]),cl(k["playCost"]),
        "; ".join(evo),cl(k["effect"]),cl(k.get("digivolveEffect")),cl(k["securityEffect"]),"\n".join(extra),cl(k["rarity"]),p.lower()])
    cnt[p]+=1
print("missing names",missing)
order=["BT","EX","ST","LM","AL"]
sets=[{"id":p.lower(),"code":p,"name":NAMES.get(p,p),"type":gtype(p),"n":cnt[p]} for p in cnt]
AL_ORDER=["AD1","RB1","P"]
sets.sort(key=lambda s:nat("LM00" if s["code"]=="LM01-05" else s["code"]),reverse=True)
sets.sort(key=lambda s:(order.index(s["type"]),AL_ORDER.index(s["code"]) if s["type"]=="AL" else 0))
rank={s["id"]:i for i,s in enumerate(sets)}
rows.sort(key=lambda r:(rank[r[16]],nat(r[0])))

# ---- ristampe: carte uscite in un prodotto ma appartenenti a un altro set ----
home={r[0]:r[16] for r in rows}
idx={r[0]:i for i,r in enumerate(rows)}
setids={x["id"] for x in sets}
def prod_ids(note):
    n=re.sub(r'\b(BT|LM|ST)\d\d-\d\d\b',' ',note)
    ids=set()
    if re.search(r'SPE[I]?CIAL LIMITED SET',n,re.I): ids.add("lm01-05")
    for pre,num in re.findall(r'\b(BT|EX|ST|LM|AD|RB)-?0*(\d+)\b',n,re.I):
        pre=pre.upper(); num=int(num)
        if pre=="LM": pid="lm01-05" if num<=5 else "lm%02d"%num
        elif pre=="AD": pid="ad1"
        elif pre=="RB": pid="rb1"
        else: pid=pre.lower()+str(num)
        ids.add(pid)
    return ids
mem=collections.defaultdict(set)
for k in src:
    n=k["cardNumber"].strip()
    if n not in home: continue
    for part in re.split(r'\n|\u25b9',k.get("notes") or ""):
        for pid in prod_ids(part):
            if pid in setids and pid!=home[n]: mem[pid].add(n)
OFFICIAL={ # liste ufficiali (cardlist en.digimoncard.com) delle ristampe nei Limited
 "lm01-05":"BT6-032 BT8-013 BT8-086 BT9-023 BT9-086 BT10-050 BT10-091 RB1-009 RB1-028 RB1-029 "
  "BT2-059 BT3-070 BT4-098 BT5-071 BT7-005 BT7-056 BT7-069 BT8-001 BT8-038 BT8-110 BT9-015 BT9-065 BT9-112 BT10-024 BT10-046 BT11-002 BT11-007 BT12-021 BT12-047 BT12-057 BT12-072 BT13-034 BT13-065 BT13-084 BT13-093 EX2-044 EX3-046 EX4-068 ST7-05 ST8-06 ST12-12 ST12-13 ST12-15 "
  "BT6-015 BT10-053 BT10-058 BT11-063 BT13-008 BT14-064 BT15-063 BT16-028 BT16-046 BT16-061 BT16-076 BT17-036 EX1-066 EX4-074 EX5-070 ST14-12 P-076 P-091 P-143 P-144 P-145 P-146 P-148 P-149 P-150 P-151 EX7-013 EX7-048 EX7-059 "
  "BT3-093 BT11-061 BT12-011 BT13-111 BT14-001 BT14-033 BT15-038 BT16-058 EX2-008 EX2-046 EX6-014 EX6-054 ST17-13 P-095 P-110 P-131 P-152 P-153 P-154 P-155 P-156 P-157 P-158 P-159",
 "lm07":"BT10-093 BT13-112 BT16-077 BT20-014 BT20-026 BT21-005 BT21-017 BT21-095 BT21-097 EX4-073 EX6-029 EX6-043 P-092 P-133 P-136 P-176 P-177 P-178 P-179 P-180 P-181 P-188 P-189 P-190 P-191 P-192 P-193",
 "lm08":"BT9-102 BT11-023 BT11-112 BT15-096 BT20-018 BT20-037 BT20-060 BT20-061 BT20-077 BT21-071 BT22-008 BT22-017 BT22-088 EX8-029 EX8-074 P-201 P-202 P-203 P-204 P-205 P-206 P-214 P-215 P-216 P-217 P-218 P-219"}
miss=[]
for pid,txt in OFFICIAL.items():
    for n in txt.split():
        if n not in home: miss.append(n)
        elif home[n]!=pid: mem[pid].add(n)
print("ufficiali non trovate nel database:",miss)
for x in sets:
    x["rp"]=sorted(idx[n] for n in mem.get(x["id"],()))
print({x["code"]:len(x["rp"]) for x in sets if x["rp"]})
upcoming=[
 {"code":"BT27","name":"Ignition of X","kind":"Booster","from":"2026-12-01","to":"2026-12-31","prec":"month","note":"Dicembre 2026 secondo le schede dei negozianti; un negozio indica spedizioni a gennaio."},
 {"code":"ST25","name":"Digimon Alysion · Rubeusdramon","kind":"Starter Deck","from":"2026-12-01","to":"2026-12-31","prec":"month","note":"Dicembre 2026, dal comunicato ufficiale di maggio 2026."},
 {"code":"ST26","name":"Digimon Alysion · Yukinamon","kind":"Starter Deck","from":"2026-12-01","to":"2026-12-31","prec":"month","note":"Dicembre 2026, dal comunicato ufficiale di maggio 2026."},
 {"code":"LM09","name":"Distancia Cero","kind":"Limited Card Pack","from":"2026-11-01","to":"2026-11-30","prec":"month","note":"Premium Bandai: spedizioni USA dal 2 novembre 2026, uscita nelle altre regioni il 27 novembre 2026. 33 tipi di carte (6 nuove, 27 ristampe alternate art). Le carte nuove saranno legali nei tornei ufficiali dall'11 dicembre 2026."},
 {"code":"EX14","name":"Malevolent VII","kind":"Extra Booster","from":"2027-01-01","to":"2027-01-31","prec":"month","note":"Gennaio 2027, annunciato sul sito ufficiale."},
 {"code":"BT28","name":"Abyss of X","kind":"Booster","from":"2027-03-01","to":"2027-03-31","prec":"month","note":"Marzo 2027 secondo un resoconto della community; non ancora confermato in modo ufficiale."},
 {"code":"PB24","name":"Tamer's Evolution Card Set: Nexus of Digimon","kind":"Prodotto speciale","prec":"none","note":"Annunciato, data non ancora comunicata."},
 {"code":"PB26","name":"Tamer's Selection Box Ver.X Antibody","kind":"Prodotto speciale","prec":"none","note":"Annunciato, data non ancora comunicata."}]
out={"sets":sets,"cards":rows,"upcoming":upcoming}
s=json.dumps(out,ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
open(SP+"data2.json","w",encoding="utf-8").write(s)
print(len(rows),"cards",len(sets),"sets",len(s)//1024,"KB")
