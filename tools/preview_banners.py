import subprocess, pathlib, json
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
d = root / "analysis" / "banners"; subprocess.run(["python3", str(root / "tools" / "fetch_banners.py"), str(d)])
ims = sorted(d.glob("*.webp")); W = 520
rows = []
for p in ims:
    im = Image.open(p); im = im.resize((W, round(im.size[1] * W / im.size[0]))); rows.append((p.stem, im))
cols = 3; H = [0] * cols; S = Image.new("RGB", (cols * (W + 10), 6000), "white"); dr = ImageDraw.Draw(S)
for i, (n, im) in enumerate(rows):
    c = H.index(min(H)); x = c * (W + 10); y = H[c]
    dr.text((x, y), n + " %dx%d" % im.size, fill="black"); S.paste(im, (x, y + 14)); H[c] += im.size[1] + 24
S.crop((0, 0, S.size[0], max(H))).save(root / "analysis" / "banners_sheet.jpg", quality=80)
