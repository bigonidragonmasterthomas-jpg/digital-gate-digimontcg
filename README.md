# Digimon Set Tracker

Un'unica base di codice, due uscite: il **sito** (GitHub Pages) e l'**APK** (Capacitor).
Ogni push su `main` ricostruisce entrambi.

- `src/template.html` – l'app (HTML/CSS/JS) · `src/data.json` – catalogo carte incorporato
- `tools/build.py` – assembla `www/index.html` · `tools/make_data2.py` – rigenera `data.json` dai database delle carte
- `.github/workflows/build.yml` – pubblica il sito e crea l'APK (release "latest")
