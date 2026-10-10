import json,re,collections
SP=__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"..","src")+"/"
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
order=["BT","EX","ST","LM","PB","AL"]
sets=[{"id":p.lower(),"code":p,"name":NAMES.get(p,p),"type":gtype(p),"n":cnt[p]} for p in cnt]
AL_ORDER=["AD1","RB1","P"]
# Prodotti Premium Bandai (PB): nessuna carta "propria", solo carte uscite al loro interno (promo e ristampe)
PB=[("PB1","Tamer's Evolution Box","2021-02-01"),("PB2","Tamer's Set","2021-05-01"),("PB3","Official WarGreymon Playmat","2021-09-01"),
 ("PB4","Tamer's Set Vol.2","2021-12-01"),("PB5","Tamer's Set Vol.3","2022-04-01"),("PB6","Tamer's Evolution Box 2","2022-05-01"),
 ("PB7","Tamer's Set EX","2022-06-01"),("PB8","Playmat and Card Set 1 Digimon Tamers","2022-06-01"),("PB9","Playmat and Card Set 2 Floral Fun","2022-09-01"),
 ("PB10","Tamer's Set Vol.4","2022-09-01"),("PB11","Tamer's Set Vol.5","2022-12-01"),("PB12E","2nd Anniversary Set","2023-03-01"),
 ("PB13","Royal Knights Binder Set","2023-06-01"),("PB14","Tamer Goods Set Angewomon & LadyDevimon","2023-06-01"),("PB16","Tamer Goods Set Diaboromon","2023-07-01"),
 ("PB17","Digimon Adventure 02: The Beginning Set","2024-06-01"),("PB18","Premium Heroines Set","2024-10-01"),("PB19","Omnimon Binder Set","2025-02-01"),
 ("PB20","Digimon Animation Series 25th Anniversary Set","2025-05-01"),("PB21","Tamer's Evolution Box -Rise of Digimon-","2025-12-01"),
 ("PB22","Digimon Liberator Debuggers Set","2026-02-01"),("PB23","Premium Heroines Set Ver.2","2026-03-01")]
for code,name,date in PB:
    sets.append({"id":"pb"+re.sub(r"\D","",code),"code":code,"name":name,"type":"PB","n":0,"date":date})
# Date di uscita internazionali (inglese). "~" = stimata. P (promo) non ha una data: va in fondo.
DATES={"BT1":"2021-02-12","BT2":"2021-02-12","BT3":"2021-03-12","BT4":"2021-06-11","BT5":"2021-08-06","BT6":"2021-10-15",
 "BT7":"2022-03-04","BT8":"2022-05-13","BT9":"2022-07-29","BT10":"2022-10-14","BT11":"2023-02-17","BT12":"2023-04-28",
 "BT13":"2023-07-21","BT14":"2023-11-17","BT15":"2024-02-16","BT16":"2024-05-24","BT17":"2024-08-09","BT18":"2024-11-01",
 "BT19":"2024-11-01","BT20":"2025-02-01","BT21":"2025-04-25","BT22":"2025-07-25","BT23":"2025-10-24","BT24":"2026-01-23",
 "BT25":"2026-05-22","BT26":"2026-09-04",
 "EX1":"2021-12-10","EX2":"2022-06-24","EX3":"2022-11-11","EX4":"2023-06-23","EX5":"2024-01-19","EX6":"2024-06-28",
 "EX7":"2024-09-13","EX8":"2025-01-01","EX9":"2025-06-26","EX10":"2025-09-19","EX11":"2026-02-14","EX12":"2026-07-04","EX13":"2026-10-02",
 "ST1":"2021-01-29","ST2":"2021-01-29","ST3":"2021-01-29","ST4":"2021-06-11","ST5":"2021-06-11","ST6":"2021-06-11",
 "ST7":"2021-10-15","ST8":"2021-10-15","ST9":"2022-05-13","ST10":"2022-05-13","ST12":"2022-10-14","ST13":"2022-10-14",
 "ST14":"2023-03-24","ST15":"2023-10-13","ST16":"2023-10-13","ST17":"2024-03-08","ST18":"2024-09-13","ST19":"2024-09-13",
 "ST20":"2025-04-18","ST21":"2025-04-18","ST22":"2025-12-05","ST23":"2026-05-15","ST24":"2026-05-15",
 "RB1":"2023-09-29","AD1":"2026-03-27","LM01-05":"2024-12-13","LM06":"2025-10-01","LM07":"2026-03-01","LM08":"2026-08-04","P":"0000-00-00"}
for x in sets: x["date"]=x.get("date") or DATES.get(x["code"],"0000-00-00")
missing_dates=[x["code"] for x in sets if x["date"]=="0000-00-00" and x["code"]!="P"]
print("senza data:",missing_dates)
# dentro ogni gruppo: dalla piu recente alla piu vecchia (a parita di data, numero piu alto prima)
sets.sort(key=lambda s:(s["date"],nat(s["code"])),reverse=True)
chron={s["id"]:i for i,s in enumerate(sets)}
sets.sort(key=lambda s:order.index(s["type"]))
rows.sort(key=lambda r:(chron[r[16]],nat(r[0])))

# simboli stampati accanto alla rarità sulle versioni alternative (1 = ★, 2 = ★★, "SP"), verificati sulle immagini
MARKS=json.load(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"alt_marks.json")))
# AD1: per le ristampe, "gold" = stessa arte con cornice dorata, "new" = arte nuova (verificato sulle immagini)
AD1C=json.load(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"ad1_class.json")))
# ---- ristampe: carte uscite in un prodotto ma appartenenti a un altro set ----
home={r[0]:r[16] for r in rows}
idx={r[0]:i for i,r in enumerate(rows)}
setids={x["id"] for x in sets}
def prod_ids(note):
    n=re.sub(r'\b(BT|LM|ST)\d\d-\d\d\b',' ',note)
    ids=set()
    if re.search(r'SPE[I]?CIAL LIMITED SET',n,re.I): ids.add("lm01-05")
    for num in re.findall(r'\bPB-?0*(\d+)E?\b',n,re.I): ids.add("pb%d"%int(num))
    for pre,num in re.findall(r'\b(BT|EX|ST|LM|AD|RB)-?0*(\d+)\b',n,re.I):
        pre=pre.upper(); num=int(num)
        if pre=="LM": pid="lm01-05" if num<=5 else "lm%02d"%num
        elif pre=="AD": pid="ad1"
        elif pre=="RB": pid="rb1"
        else: pid=pre.lower()+str(num)
        ids.add(pid)
    return ids
# Ogni prodotto contiene "versioni" (carta + arte): base = id uguale al numero, alternative = suffisso _P1, _P2...
VERS=["Normal"]; verix={"Normal":0}
def vlabel(k):
    v=re.sub(r"\s+"," ",(k.get("version") or "").replace("\xa0"," ")).strip(" -") or "Normal"
    if v not in verix: verix[v]=len(VERS); VERS.append(v)
    return verix[v]
ent=collections.defaultdict(dict)   # set id -> {(idx,suffix): versione}
mem=collections.defaultdict(set)    # set id -> numeri carta presenti (qualsiasi versione)
for k in src:
    n=k["cardNumber"].strip(); vid=k["id"].strip()
    if n not in home or "Errata" in vid: continue
    suf=vid[len(n):]
    for part in re.split(r'\n|\u25b9',k.get("notes") or ""):
        for pid in prod_ids(part):
            if pid not in setids: continue
            if suf=="" and pid!=home[n]: continue   # la versione base appartiene al suo set d'origine
            ent[pid][(idx[n],suf)]=vlabel(k); mem[pid].add(n)
for r in rows:   # ogni carta base sta sempre nel suo set
    ent[r[16]].setdefault((idx[r[0]],""),0); mem[r[16]].add(r[0])
OFFICIAL={ # liste ufficiali (cardlist en.digimoncard.com) delle ristampe nei Limited
 "lm01-05":"BT6-032 BT8-013 BT8-086 BT9-023 BT9-086 BT10-050 BT10-091 RB1-009 RB1-028 RB1-029 "
  "BT2-059 BT3-070 BT4-098 BT5-071 BT7-005 BT7-056 BT7-069 BT8-001 BT8-038 BT8-110 BT9-015 BT9-065 BT9-112 BT10-024 BT10-046 BT11-002 BT11-007 BT12-021 BT12-047 BT12-057 BT12-072 BT13-034 BT13-065 BT13-084 BT13-093 EX2-044 EX3-046 EX4-068 ST7-05 ST8-06 ST12-12 ST12-13 ST12-15 "
  "BT6-015 BT10-053 BT10-058 BT11-063 BT13-008 BT14-064 BT15-063 BT16-028 BT16-046 BT16-061 BT16-076 BT17-036 EX1-066 EX4-074 EX5-070 ST14-12 P-076 P-091 P-143 P-144 P-145 P-146 P-148 P-149 P-150 P-151 EX7-013 EX7-048 EX7-059 "
  "BT3-093 BT11-061 BT12-011 BT13-111 BT14-001 BT14-033 BT15-038 BT16-058 EX2-008 EX2-046 EX6-014 EX6-054 ST17-13 P-095 P-110 P-131 P-152 P-153 P-154 P-155 P-156 P-157 P-158 P-159",
 "pb21":"BT5-086 BT9-112 BT10-042 BT10-057 BT10-112 BT11-019 BT16-102 BT18-071 EX5-063 EX6-035 EX7-023 EX8-074",
 "pb22":"BT19-027 BT19-053 BT19-082 BT19-084 BT20-055 BT20-079 BT20-086 BT20-088 BT21-029 BT21-081 EX7-030 EX7-062 EX7-065 EX7-074 EX8-016 EX8-028 EX8-055 EX8-065 EX8-066 EX8-067 EX9-033 EX9-067 ST18-12 ST18-14 ST19-14 P-151",
 "pb23":"BT5-092 BT8-082 BT11-089 BT11-112 BT13-057 EX3-065 EX5-025 EX6-074 LM-042 ST10-06 ST14-09 ST19-12 P-195",
 "pb9":"BT1-010 BT1-029 BT2-036 ST1-02 ST3-04 ST4-03 ST4-04 P-004",
 "pb14":"ST10-05 ST10-12",
 "lm07":"BT10-093 BT13-112 BT16-077 BT20-014 BT20-026 BT21-005 BT21-017 BT21-095 BT21-097 EX4-073 EX6-029 EX6-043 P-092 P-133 P-136 P-176 P-177 P-178 P-179 P-180 P-181 P-188 P-189 P-190 P-191 P-192 P-193",
 "lm08":"BT9-102 BT11-023 BT11-112 BT15-096 BT20-018 BT20-037 BT20-060 BT20-061 BT20-077 BT21-071 BT22-008 BT22-017 BT22-088 EX8-029 EX8-074 P-201 P-202 P-203 P-204 P-205 P-206 P-214 P-215 P-216 P-217 P-218 P-219"}
miss=[]
for pid,txt in OFFICIAL.items():
    for n in txt.split():
        if n not in home: miss.append(n)
        elif home[n]!=pid and n not in mem[pid]:
            ent[pid][(idx[n],"")]=0; mem[pid].add(n)   # versione non nota: si usa l'arte base
print("ufficiali non trovate nel database:",miss)
for x in sets:
    e=ent.get(x["id"],{})
    def sk(t):
        (i,suf),_=t
        return (1 if suf else 0, 0 if rows[i][16]==x["id"] else 1, i, nat(suf))   # arti alternative in fondo
    x["v"]=[]
    for (i,suf),vv in sorted(e.items(),key=sk):
        if not (suf or vv): x["v"].append(i); continue
        m=MARKS.get(rows[i][0]+suf,0) if suf else 0
        k={"gold":"g","new":"n"}.get(AD1C.get(rows[i][0]+suf),"") if x["id"]=="ad1" and suf and rows[i][16]!="ad1" else ""
        x["v"].append([i,suf,vv,m,k] if k else ([i,suf,vv,m] if m else [i,suf,vv]))
print({x["code"]:len(x["v"]) for x in sets})
upcoming=[
 {"code":"LM09","name":"Distancia Cero","kind":"Limited Card Pack","from":"2026-11-02","to":"2026-11-30","prec":"month","note":"Premium Bandai: spedizioni USA dal 2 novembre 2026, uscita nelle altre regioni il 27 novembre 2026. 33 tipi di carte (6 nuove, 27 ristampe alternate art). Le carte nuove saranno legali nei tornei ufficiali dall'11 dicembre 2026."},
 {"code":"ST25","name":"Digimon Alysion · Rubeusdramon","kind":"Starter Deck","from":"2026-12-04","to":"2026-12-04","prec":"day","note":"In negozio dal 4 dicembre 2026 (sito ufficiale)."},
 {"code":"ST26","name":"Digimon Alysion · Yukinamon","kind":"Starter Deck","from":"2026-12-04","to":"2026-12-04","prec":"day","note":"In negozio dal 4 dicembre 2026 (sito ufficiale)."},
 {"code":"BT27","name":"Ignition of X","kind":"Booster","from":"2026-12-11","to":"2026-12-11","prec":"day","note":"Pre-release dal 4 dicembre, in negozio dall'11 dicembre 2026 (sito ufficiale)."},
 {"code":"EX14","name":"Malevolent VII","kind":"Extra Booster","from":"2027-01-01","to":"2027-01-31","prec":"month","note":"Gennaio 2027, annunciato sul sito ufficiale."},
 {"code":"PB25","name":"Digimon Story Time Stranger Set","kind":"Premium Bandai","from":"2027-02-01","to":"2027-02-28","prec":"month","note":"Febbraio 2027 (Premium Bandai, sito ufficiale)."},
 {"code":"PB26","name":"Tamer's Selection Box Ver.X Antibody","kind":"Premium Bandai","from":"2027-03-01","to":"2027-03-31","prec":"month","note":"Marzo 2027 (Premium Bandai, sito ufficiale)."},
 {"code":"BT28","name":"Abyss of X","kind":"Booster","from":"2027-03-01","to":"2027-03-31","prec":"month","note":"Marzo 2027 secondo un resoconto della community; non ancora confermato in modo ufficiale."},
 {"code":"PB27","name":"Premium Battle Set Ver. Royal Knights","kind":"Premium Bandai","from":"2027-06-01","to":"2027-06-30","prec":"month","note":"Giugno 2027 (Premium Bandai, sito ufficiale)."},
 {"code":"PB28","name":"Premium Battle Set Ver. Seven Great Demon Lords","kind":"Premium Bandai","from":"2027-06-01","to":"2027-06-30","prec":"month","note":"Giugno 2027 (Premium Bandai, sito ufficiale)."},
 {"code":"PB24","name":"Tamer's Evolution Card Set: Nexus of Digimon","kind":"Premium Bandai","prec":"none","note":"Annunciato, data non ancora comunicata."}]
BAN=json.load(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"banners.json")))
out={"sets":sets,"cards":rows,"upcoming":upcoming,"versions":VERS,"banners":sorted(BAN)}
s=json.dumps(out,ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
open(SP+"data.json","w",encoding="utf-8").write(s)
print(len(rows),"cards",len(sets),"sets",len(s)//1024,"KB")
