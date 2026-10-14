#!/usr/bin/env python3
"""Controlla la firma e la versione dell'APK pubblicato (eseguito via analysis.yml)."""
import glob, os, subprocess, urllib.request
for k, v in sorted(os.environ.items()):
    if "ANDROID" in k or k in ("HOME", "JAVA_HOME"): print("ENV", k, "=", v)
url = "https://github.com/knightofgemini/digital-gate-digimontcg/releases/download/latest/DigimonSetTracker.apk"
urllib.request.urlretrieve(url, "app.apk")
print("size", os.path.getsize("app.apk"))
bt = sorted(glob.glob(os.environ.get("ANDROID_HOME", "/usr/local/lib/android/sdk") + "/build-tools/*"))[-1]
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True); print("$", " ".join(cmd)); print(r.stdout[-3000:], r.stderr[-2000:])
run([bt + "/apksigner", "verify", "--verbose", "--print-certs", "app.apk"])
run([bt + "/aapt", "dump", "badging", "app.apk"])
run(["keytool", "-list", "-v", "-keystore", "android-keys/debug.keystore", "-storepass", "android"])
for p in ("~/.android", "~/.config/.android"):
    print(p, os.listdir(os.path.expanduser(p)) if os.path.isdir(os.path.expanduser(p)) else "assente")
