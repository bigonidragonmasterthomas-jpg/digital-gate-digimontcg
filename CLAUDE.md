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
- `tools/fetch_banners.py` + `tools/banners.json` – banner HD dei prodotti per la Home (`W/` sito ufficiale, `L/` copia salvata in `src/banners/`), con ritaglio per togliere date/testi promo e tenere il logo.
- `tools/fetch_products.py` + `tools/product_fixes.json` – caratteristiche dei prodotti dal sito ufficiale (uscita anche per regione, pre-release, prezzo, numero di carte, contenuto, rarità, immagine della confezione) in `src/products.json`, una voce per codice set; parte dall'indice del ramo `set-assets`. Va rilanciato quando escono prodotti nuovi (anche via `analysis.yml`). `tools/build.py` le aggiunge ai dati come `products`.
- `tools/fetch_product_images.py` – confezioni (`pk` in `products.json`) in `www/prod/CODICE.webp`.
- `tools/apply_errata_images.py` – mette le immagini post-errata (`src/errata/KEY.webp`) come principali e salva l'originale in `www/img/pre/`.
- Formato carta in `data.json`: `[code,name,lv,colors,ct,form,attr,sp(trait),dp,play,evo,eff,inh,sec,extra,rar,setId,{x}]`; `x.d` = lato Option delle Digimon/Option, `x.o` = spiegazione Overflow.
- Formato set: `{id,code,name,type,n,date,v:[idx | [idx,suf,versionIdx,mark,cls]]}`.

### Correzioni ai dati (sopravvivono agli aggiornamenti TakaOtaku)

- `tools/card_fixes.json` – 96 correzioni verificate sulle immagini ufficiali (livello, costi, digievoluzioni, attribute, trait, rarità, DP…), testi delle **errata Bandai** (`text`: sostituzioni) e voci da rimuovere (`_remove`).
- `tools/official_extra.json` – dalla lista carte ufficiale EN: lato Option delle Digimon/Option (10 BT26/EX13 trascritti dalle immagini) e testo Overflow.
- `tools/banlist.json` – lista ban/restrizioni (in vigore dal 1 set 2026, fonte https://world.digimoncard.com/rule/restriction_card/). Va aggiornata a mano quando Bandai la cambia.
- Errore noto della fonte corretto in `make_data2.py`: tratto e costo invertiti (`w/[3] trait: Cost DS` → `w/[DS] trait: Cost 3`).

## Pubblicazione (GitHub Actions)

- `.github/workflows/build.yml` parte a ogni push su `main`: build → immagini → banner → confezioni → errata → GitHub Pages → APK (Capacitor 6, Java 17, `assembleDebug`) → release `latest`.
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
- **Scheda prodotto**: in cima alla pagina di ogni prodotto (nascosta mentre si cerca), con confezione, tipo, uscita, pre-release, prezzo, carte, contenuto, rarità e link alla pagina ufficiale. Etichette in italiano; contenuto e rarità restano in inglese come sul sito (tranne "N carte per busta" / "N buste per box"). I prodotti in arrivo con dati ufficiali hanno una pagina con la sola scheda (da Home, Prodotti e Prossime uscite).
- **Elenco Prodotti**: prima del codice c'è il logo del prodotto (`lg` in `products.json`, dal ramo `set-assets`, in `www/prod/logo/`; i loghi "solo nome" forniti dall'utente stanno in `src/logos/CODICE.webp` e hanno la precedenza: `tools/fetch_set_assets.py` li copia nel ramo `set-assets` come `CODICE/logo.webp` con fonte `utente`; per ora AD1, BT10, BT12, BT24, BT25, BT26, BT27, EX4, EX11, EX12, EX13), nei gruppi in cui la maggior parte dei prodotti ne ha uno (non i Premium Bandai). Ogni sezione ha in cima il titolo con il nome del menu (`pageTitle`).
- **Anteprima al passaggio del mouse (solo PC)**: sopra l'immagine di una carta negli elenchi (anche nei mazzi) compare, dopo 0,35 secondi, la carta grande accanto al puntatore (`.zoompop`); sparisce uscendo dall'immagine, al clic e scorrendo.
- **Raccoglitore del materiale promozionale** (`set-assets.yml` + `tools/fetch_set_assets.py`, ogni lunedì o a mano): scarica **solo il nuovo**. Parte dalla raccolta già nel ramo `set-assets`: prodotti nuovi per intero; per quelli usciti da meno di 12 mesi o in arrivo solo i tipi di immagine che mancano; i più vecchi non vengono toccati e nessun file già salvato viene sostituito. Per rifare tutto: avvio manuale con l'opzione `tutto`. Per i file già salvati controlla, senza scaricarli, se sul sito Bandai sono stati sostituiti (dimensione diversa) e in quel caso apre una **issue** su GitHub (una sola volta per cambiamento; opzione `prova` per una segnalazione di prova). **Nessuna dipendenza da unacollezione.it** (scelta dell'utente, ottobre 2026): i loghi nuovi si aggiungono a mano in `src/logos/`; nel ramo `set-assets` restano le copie dei loghi presi lì in passato.
- **Versione desktop (PC con mouse, finestra da 1000 px; `body.desk`, variabile `DESK`)**: crasi delle proposte Claude + ChatGPT (ottobre 2026). Barra laterale fissa con logo "D" (stesso disegno del primo mockup), colori che seguono il tema (chiara nel chiaro, scura nello scuro), pulsante accanto al logo per ridurla a sole icone (salvato in `dg-sidec`, attributo `data-sidec="1"`), gruppi Esplora / Il tuo spazio / Progetto, contatori, collezione e in fondo due pulsanti: tema chiaro/scuro (salvato in `dg-theme`; finché non si sceglie segue il sistema) e barra a sinistra/destra (salvato in `dg-side`, attributo `data-side="r"` su `html`). Home con hero della prossima uscita e conto alla rovescia, "All'orizzonte", set recenti con avanzamento, pannelli mazzo e lista ban; Prodotti a griglia con artwork (banner > logo > confezione > codice); pagina prodotto con intestazione, avanzamento e barra delle rarità; Ricerca e Collezione con filtri nella colonna sinistra (colori, tipo, livello, dove cercare) e griglia di default; Collezione con riepilogo e avanzamento per prodotto; scheda carta in finestra a due colonne con frecce (anche ← →) ed Esc, distanziata dal bordo superiore; anteprima al passaggio del mouse ridotta del 15%; Deckbuilding con copertine dei mazzi, editor affiancato (ricerca a sinistra, pannello con regole, curva, colori e lista a destra); Prossime uscite come cronologia per mese dalla più vicina (solo desktop; sul telefono resta l'ordine di prima). Ingrandimento solo su schermi molto larghi (1,12× da 1500 px, 1,3× da 1800 px, 1,7× da 2300 px). Telefoni e APK identici a prima (verificato con confronto pixel).
- **Digimon ACE** (carte con `Effetto ACE:` nelle regole): accanto al nome compare il simbolo `ACE` (anche negli elenchi e nella ricerca), e nella scheda un asterisco con la nota che il simbolo non fa parte del nome (regolamento ufficiale, pagina Digimon ACE).
- **Ricerca**: passando da Prodotti/Prossime uscite a Ricerca carte o Collezione, testo e filtri vengono azzerati.
- **Collezione** salvata nel dispositivo (localStorage), con quantità per versione.
- **Deckbuilding**: 50 carte principali esatte, 0–5 Digi-Egg, max 4 copie per numero (tutte le versioni insieme), carte "fino a 50"; bandite (lucchetto), limitate (MAX), coppie vietate (tag solo se entrambe nel mazzo; nella scheda nome cliccabile che apre la carta, chiudendo si torna indietro). Vista elenco/griglia, import/export testo, versioni alt nel mazzo, copie possedute bloccate con lucchetto nella scheda.
- **APK**: all'avvio controlla la release `latest` e propone l'aggiornamento aprendo il download nel browser esterno.

## Idee in sospeso / possibili prossimi passi

- Aggiornamento automatico settimanale dei dati (TakaOtaku) con anteprima e riepilogo prima di pubblicare (proposto, non fatto).
- Backup/ripristino di collezione e mazzi (proposto).
- Banner mancanti o provvisori per PB24, EX14, BT28.
- Spostare la chiave di firma APK nei segreti GitHub (opzionale).
