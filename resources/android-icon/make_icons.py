# Generates the Android app icons from the Karix artwork. Run from the repo root:
#   python resources/android-icon/make_icons.py
# - Launcher icon (mipmap-*) = "K" mark. k-glyph.png = transparent render of k-glyph.svg (white K + pink dot,
#   reference KX_MARK). Adaptive: NAVY background colour + white K foreground inside the 66dp safe zone;
#   legacy: navy rounded square / navy circle.
# - Launch screen = "karix" wordmark on white. wordmark.png = transparent render of wordmark.svg (KX_LOGO light):
#   drawable-*/splash_icon.png (Android 12+ splash icon, 288dp canvas, inside the 192dp circle) and the
#   older full-screen drawable*/splash.png. styles.xml's launch theme points at splash_icon.
import sys

from PIL import Image, ImageDraw

S = sys.argv[1] if len(sys.argv) > 1 else 'resources/android-icon'
RES = 'android/app/src/main/res'
NAVY = '#160E7A'
GLYPH_IN_FOREGROUND = 0.58  # glyph canvas size relative to the 108dp foreground layer

glyph = Image.open(S + '/k-glyph.png').convert('RGBA')
assert glyph.getpixel((0, 0))[3] == 0, 'master must be transparent'


def put_glyph(canvas, frac):
    W = canvas.size[0]
    g = glyph.resize((int(W * frac),) * 2, Image.LANCZOS)
    canvas.alpha_composite(g, ((W - g.size[0]) // 2,) * 2)
    return canvas


def legacy(size, round_):
    big = size * 4  # supersample for smooth edges
    c = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    if round_:
        d.ellipse((0, 0, big - 1, big - 1), fill=NAVY)
    else:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=int(big * 14 / 64), fill=NAVY)  # = KX_MARK rx 14/64
    put_glyph(c, 0.95 if round_ else 1.0)
    return c.resize((size, size), Image.LANCZOS)


for dens, n in {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}.items():
    legacy(n, False).save(f'{RES}/mipmap-{dens}/ic_launcher.png', optimize=True)
    legacy(n, True).save(f'{RES}/mipmap-{dens}/ic_launcher_round.png', optimize=True)
    fg = n * 108 // 48  # 108dp foreground layer
    big = Image.new('RGBA', (fg * 4, fg * 4), (0, 0, 0, 0))
    put_glyph(big, GLYPH_IN_FOREGROUND).resize((fg, fg), Image.LANCZOS).save(
        f'{RES}/mipmap-{dens}/ic_launcher_foreground.png', optimize=True
    )
    print(dens, n, fg)

open(f'{RES}/values/ic_launcher_background.xml', 'w', encoding='utf-8').write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
    f'    <color name="ic_launcher_background">{NAVY}</color>\n</resources>\n'
)

# preview: adaptive (navy bg + circle mask), legacy square, legacy round at xxxhdpi
prev = Image.new('RGBA', (3 * 220, 220), (235, 235, 240, 255))
fgi = Image.open(f'{RES}/mipmap-xxxhdpi/ic_launcher_foreground.png')
ad = Image.new('RGBA', fgi.size, NAVY)
ad.alpha_composite(fgi)
W = fgi.size[0]
mask = Image.new('L', fgi.size, 0)
ImageDraw.Draw(mask).ellipse((W * 0.17, W * 0.17, W * 0.83, W * 0.83), fill=255)
ad.putalpha(mask)
ad = ad.crop((int(W * 0.17),) * 2 + (int(W * 0.83),) * 2).resize((192, 192))
for i, im in enumerate(
    [ad, Image.open(f'{RES}/mipmap-xxxhdpi/ic_launcher.png'), Image.open(f'{RES}/mipmap-xxxhdpi/ic_launcher_round.png')]
):
    prev.alpha_composite(im.convert('RGBA'), (i * 220 + 14, 14))
prev.save(S + '/preview.png')  # visual check

# ---------- launch screen: "karix" wordmark ----------
import glob, os

wm = Image.open(S + '/wordmark.png').convert('RGBA')
assert wm.getpixel((0, 0))[3] == 0, 'wordmark master must be transparent'
wm = wm.crop(wm.getbbox())


def put_wordmark(canvas, width_px):
    W, H = canvas.size
    h = round(wm.size[1] * width_px / wm.size[0])
    canvas.alpha_composite(wm.resize((width_px, h), Image.LANCZOS), ((W - width_px) // 2, (H - h) // 2))
    return canvas


# Android 12+ splash icon: 288dp square, content must fit the 192dp circle → wordmark 60% wide
for dens, scale in {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}.items():
    n = int(288 * scale)
    os.makedirs(f'{RES}/drawable-{dens}', exist_ok=True)
    put_wordmark(Image.new('RGBA', (n, n), (0, 0, 0, 0)), int(n * 0.6)).save(
        f'{RES}/drawable-{dens}/splash_icon.png', optimize=True
    )

# older devices / window background: full-screen white with the wordmark (keeps each file's size)
for f in glob.glob(f'{RES}/drawable*/splash.png'):
    W, H = Image.open(f).size
    put_wordmark(Image.new('RGBA', (W, H), 'white'), int(min(W, H) * 0.42)).convert('RGB').save(f, optimize=True)

styles = f'{RES}/values/styles.xml'
xml = open(styles, encoding='utf-8').read()
launch = '''    <style name="AppTheme.NoActionBarLaunch" parent="Theme.SplashScreen">
        <item name="android:background">@drawable/splash</item>
        <item name="windowSplashScreenBackground">#FFFFFF</item>
        <item name="windowSplashScreenAnimatedIcon">@drawable/splash_icon</item>
        <item name="postSplashScreenTheme">@style/AppTheme.NoActionBar</item>
    </style>'''
start = xml.index('    <style name="AppTheme.NoActionBarLaunch"')
end = xml.index('</style>', start) + len('</style>')
open(styles, 'w', encoding='utf-8').write(xml[:start] + launch + xml[end:])
print('launch screen: splash_icon x5, splash.png x', len(glob.glob(f'{RES}/drawable*/splash.png')), ', styles.xml updated')
