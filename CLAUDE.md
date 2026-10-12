# Digital Gate - Digimon TCG

Catalogo non ufficiale del Digimon Card Game (carte **in inglese**) con collezione, prossime uscite, deckbuilding e lista ban.
Esiste come **sito** (GitHub Pages) e come **APK Android** (Capacitor). Ogni modifica vale sempre per **entrambi**.

- Sito: https://knightofgemini.github.io/digital-gate-digimontcg/
- APK (sempre l'ultima): https://github.com/knightofgemini/digital-gate-digimontcg/releases/download/latest/DigimonSetTracker.apk
- Repository: `knightofgemini/digital-gate-digimontcg` (pubblico)

## Come lavorare con l'utente

- **Rispondere sempre in italiano.** Tutta l'interfaccia è in italiano.
- **Mostrare un'anteprima prima di pubblicare**: lavorare su un ramo (es. `feature-x`), fare screenshot con Playwright e mandarli; fondere in `main` e pubblicare **solo dopo l'ok** ("vai", "pubblica", "okay").
- Dopo la pubblicazione, aspettare che il workflow finisca e confermare (sito ricaricando la pagina, APK dal link sopra).
- Spiegazioni semplici, senza gergo tecnico; l'utente non è uno sviluppatore.
- L'utente non può fare test qui: chiedere conferma quando qualcosa va provato su telefono (es. aggiornamento APK, gesti).

## Regole fisse sul contenuto

- **Non tradurre MAI il testo delle carte** (effetti, nomi, tratti, keyword, colori nei tag): resta in inglese esattamente come stampato.
- I nomi lunghi si **rimpiccioliscono per stare su una riga** (classe `fit`, funzione `fitOne`/`fitAll`).
- Prodotti ordinati **dal più recente al più vecchio** per data di uscita.
- Dentro un prodotto le carte sono in **ordine di numero**, raggruppate in: `Regular`, `Alternative Art`, `Ristampe`, `Ristampe · Alternative Art`.
- **PB (Premium Bandai)**: mostrano solo `Ristampe · Alternative Art`.
- **AD1 (Digimon Generation)**: ordine e sezioni speciali: `Regular`, `Alternative Art`, `Ristampe`, `Ristampe · Alternative Art` (arte nuova), `Ristampe · Gold Border`. Classificazione in `tools/ad1_class.json` (gold/new/same), verificata sulle immagini.
- Stelle/SP delle alternative art in `tools/alt_marks.json` (1 = ★, 2 = ★★, "SP").

## Struttura del progetto

- `src/template.html` – **tutta l'app** (HTML+CSS+JS in un file). `/*DATA*/` viene sostituito con `src/data.json`.
- `src/data.json` – dati generati (non modificare a mano): carte, prodotti, versioni, prossime uscite, banner, lista ban, errata.
- `tools/build.py` – crea `www/index.html` (+ manifest, service worker, `window.APPBUILD` = numero di build).
- `tools/make_data2.py` – genera `src/data.json` dalla raccolta TakaOtaku (`PreparedDigimonCardsENG.json`, repo `TakaOtaku/Digimon-Card-App`, clonata in `/home/claude/TakaOtaku_Digimon-Card-App`). Contiene nomi set, prodotti PB, prossime uscite.
- `tools/fetch_images.py` – scarica immagini carte (ufficiali HD, ripiego TakaOtaku) in `www/img/f` (grandi) e `www/img/t` (miniature), con cache.
- `tools/fetch_banners.py` + `tools/banners.json` – banner HD dei prodotti per la Home (`W/` sito ufficiale, `U/` img.unacollezione.it), con ritaglio per togliere date/testi promo e tenere il logo.
- `tools/apply_errata_images.py` – mette le immagini post-errata (`src/errata/KEY.webp`) come principali e salva l'originale in `www/img/pre/`.
- Formato carta in `data.json`: `[code,name,lv,colors,ct,form,attr,sp(trait),dp,play,evo,eff,inh,sec,extra,rar,setId,{x}]`; `x.d` = lato Option delle Digimon/Option, `x.o` = spiegazione Overflow.
- Formato set: `{id,code,name,type,n,date,v:[idx | [idx,suf,versionIdx,mark,cls]]}`.

### Correzioni ai dati (sopravvivono agli aggiornamenti TakaOtaku)

- `tools/card_fixes.json` – 96 correzioni verificate sulle immagini ufficiali (livello, costi, digievoluzioni, attribute, trait, rarità, DP…), testi delle **errata Bandai** (`text`: sostituzioni) e voci da rimuovere (`_remove`).
- `tools/official_extra.json` – dalla lista carte ufficiale EN: lato Option delle Digimon/Option (10 BT26/EX13 trascritti dalle immagini) e testo Overflow.
- `tools/banlist.json` – lista ban/restrizioni (in vigore dal 1 set 2026, fonte https://world.digimoncard.com/rule/restriction_card/). Va aggiornata a mano quando Bandai la cambia.
- Errore noto della fonte corretto in `make_data2.py`: tratto e costo invertiti (`w/[3] trait: Cost DS` → `w/[DS] trait: Cost 3`).

## Pubblicazione (GitHub Actions)

- `.github/workflows/build.yml` parte a ogni push su `main`: build → immagini → banner → errata → GitHub Pages → APK (Capacitor 6, Java 17, `assembleDebug`) → release `latest`.
- APK firmato sempre con `android-keys/debug.keystore` e `versionCode` = numero di run: così gli aggiornamenti si installano sopra senza disinstallare. **Non cambiare la chiave.**
- La release `latest` viene forzata a non-bozza; il nome contiene `build N` (usato dall'app per il controllo aggiornamenti).
- Commit con autore `Claude <noreply@anthropic.com>`.

### Limiti dell'ambiente cloud

- Dalla sandbox i siti esterni (digimoncard.com, github.io, fandom…) di solito **non sono raggiungibili**: usare `.github/workflows/analysis.yml` (workflow_dispatch con `ids` e `script`), che esegue uno script in Actions e salva `analysis/` sul ramo orfano `analysis-out`:
  `git fetch origin +analysis-out:refs/remotes/origin/analysis-out && git archive refs/remotes/origin/analysis-out | tar -x -C DIR`
- Dispatch/monitoraggio via REST (`gh api ...`), GraphQL non disponibile; release e segreti non modificabili da qui.

## Funzionalità dell'app (riassunto)

- Splash animato, menu a hamburger: Home, Prodotti, Prossime uscite, Ricerca carte, La mia collezione, Deckbuilding, Informazioni.
- Navigazione con cronologia (tasto/gesto indietro). Nell'APK il gesto indietro torna alla schermata precedente; nella scheda carta non fa nulla (lì: giù per chiudere con la maniglia, sinistra/destra per carta precedente/successiva). Barra superiore che si nasconde scorrendo.
- **Scheda carta**: intestazione con codice, set (arancione), rarità estesa colorata con ★/SP, versione ("Foil" arcobaleno); tag sotto l'immagine su righe separate (tipo+livello+colori / forma / attribute / trait), colori come le barrette; box Costo/DP/Rarità; Digievoluzione su una riga separata da •; Altra Digievoluzione e Digievoluzione speciale (DNA, App Fusion, Burst) con icone; Effetto, Ereditato, Sicurezza, Effetto Option (Use + colori), Regole, Regole Link/Assembly/DigiXros/Ace Overflow, Altre regole; Alternative Art (toccandone una si apre, uscendo si va alla sua espansione); sezione Pre errata.
- Icone per `[ ]` e `＜ ＞` con i colori delle carte: timing blu (anche Security), Trash/Hand/Breeding viola, Once/Twice Per Turn rosso, keyword arancioni esagonali, Digivolve/DNA/Burst/App Fusion blu-petrolio, DigiXros/Assembly/Link verdi, Rule grigio chiaro, Overflow grigio metallizzato, trait bianchi con testo nero.
- **Collezione** salvata nel dispositivo (localStorage), con quantità per versione.
- **Deckbuilding**: 50 carte principali esatte, 0–5 Digi-Egg, max 4 copie per numero (tutte le versioni insieme), carte "fino a 50"; bandite (lucchetto), limitate (MAX), coppie vietate (tag solo se entrambe nel mazzo; nella scheda nome cliccabile che apre la carta, chiudendo si torna indietro). Vista elenco/griglia, import/export testo, versioni alt nel mazzo, copie possedute bloccate con lucchetto nella scheda.
- **APK**: all'avvio controlla la release `latest` e propone l'aggiornamento aprendo il download nel browser esterno.

## Idee in sospeso / possibili prossimi passi

- Aggiornamento automatico settimanale dei dati (TakaOtaku) con anteprima e riepilogo prima di pubblicare (proposto, non fatto).
- Backup/ripristino di collezione e mazzi (proposto).
- Banner mancanti o provvisori per PB24, EX14, BT28.
- Spostare la chiave di firma APK nei segreti GitHub (opzionale).
