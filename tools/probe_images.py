import urllib.request, pathlib, sys
from PIL import Image
import io
out = pathlib.Path("analysis"); out.mkdir(exist_ok=True)
ids = sys.argv[1:]
for i in ids:
    for name, url in (("off", "https://world.digimoncard.com/images/cardlist/card/%s.png" % i), ("taka", "https://web-garage.takaotaku.de/%s.webp" % i)):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
            im = Image.open(io.BytesIO(b)).convert("RGB")
            print(i, name, im.size)
            im.save(out / ("%s_%s.png" % (i, name)))
        except Exception as e:
            print(i, name, "ERR", e)
