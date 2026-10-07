# Generates the Android launcher icons (android/app/src/main/res/mipmap-*) from the Karix wordmark.
# Run from the repo root:  python resources/android-icon/make_icons.py
# wordmark.png = transparent render of wordmark.svg (reference KX_LOGO, light variant).
# Adaptive foreground: wordmark 48% of the 108dp layer (inside the 66dp safe zone); background colour
# stays #FFFFFF (values/ic_launcher_background.xml). Legacy: white rounded square / circle.
import sys
from PIL import Image, ImageDraw
S = sys.argv[1] if len(sys.argv) > 1 else 'resources/android-icon'
RES = 'android/app/src/main/res'
wm = Image.open(S + '/wordmark.png').convert('RGBA')
assert wm.getpixel((0, 0))[3] == 0, 'master must be transparent'
wm = wm.crop(wm.getbbox())  # tight to the artwork

def place(canvas, frac):
    W = canvas.size[0]
    w = int(W * frac); h = round(wm.size[1] * w / wm.size[0])
    m = wm.resize((w, h), Image.LANCZOS)
    canvas.alpha_composite(m, ((W - w) // 2, (W - h) // 2))
    return canvas

def legacy(size, round_):
    big = size * 4  # supersample for smooth edges
    c = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    if round_:
        d.ellipse((0, 0, big - 1, big - 1), fill='white')
    else:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=int(big * 0.18), fill='white')
    place(c, 0.64 if round_ else 0.72)
    return c.resize((size, size), Image.LANCZOS)

for dens, n in {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}.items():
    legacy(n, False).save(f'{RES}/mipmap-{dens}/ic_launcher.png', optimize=True)
    legacy(n, True).save(f'{RES}/mipmap-{dens}/ic_launcher_round.png', optimize=True)
    fg = n * 108 // 48  # 108dp foreground layer
    big = Image.new('RGBA', (fg * 4, fg * 4), (0, 0, 0, 0))
    place(big, 0.48).resize((fg, fg), Image.LANCZOS).save(f'{RES}/mipmap-{dens}/ic_launcher_foreground.png', optimize=True)
    print(dens, n, fg)

# preview: adaptive (white bg + circle mask), legacy square, legacy round at xxxhdpi
prev = Image.new('RGBA', (3 * 220, 220), (40, 40, 40, 255))
fgi = Image.open(f'{RES}/mipmap-xxxhdpi/ic_launcher_foreground.png')
ad = Image.new('RGBA', fgi.size, 'white'); ad.alpha_composite(fgi)
mask = Image.new('L', fgi.size, 0); ImageDraw.Draw(mask).ellipse((fgi.size[0] * 0.17, fgi.size[1] * 0.17, fgi.size[0] * 0.83, fgi.size[1] * 0.83), fill=255)
ad.putalpha(mask); ad = ad.crop((int(fgi.size[0] * 0.17),) * 2 + (int(fgi.size[0] * 0.83),) * 2).resize((192, 192))
for i, im in enumerate([ad, Image.open(f'{RES}/mipmap-xxxhdpi/ic_launcher.png'), Image.open(f'{RES}/mipmap-xxxhdpi/ic_launcher_round.png')]):
    prev.alpha_composite(im.convert('RGBA'), (i * 220 + 14, 14))
prev.save(S + '/preview.png')
