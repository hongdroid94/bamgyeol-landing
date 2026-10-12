#!/usr/bin/env python3
"""Assemble site/ from src/ + assets. Run: python3 build.py https://<domain>"""
import os, re, shutil, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter

SITE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'https://bamgyeol.vercel.app'
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'site')
PH = os.environ.get('PHOSPHOR', '/private/tmp/claude-501/-Users-hongdroid/94422062-e883-4c2c-adf6-4d915ebb7ec3/scratchpad/ph/package/assets')
FONTS = os.path.expanduser('~/sleep_ambient/tools/fonts-src/GowunBatang-Regular.ttf'), os.path.expanduser('~/sleep_ambient/assets/fonts/IBMPlexMono-Regular.ttf')

# id, Korean name, English name, loop - same order as lib/sounds.dart
SOUNDS = [
    ('rain_shore', '잠든 해변의 비', 'Rain on the Sleeping Shore', '2:38'),
    ('wet_branches', '젖은 나뭇가지 아래', 'Under the Wet Branches', '2:41'),
    ('ancient_leaves', '오래된 잎사귀 아래', 'Under Ancient Leaves', '2:29'),
    ('still_waters', '고요한 물결 아래', 'Beneath Still Waters', '3:00'),
    ('windowpane', '창가의 자장가', 'Windowpane Lullaby', '2:29'),
    ('canopy', '우거진 잎 아래', 'Beneath the Canopy', '2:57'),
    ('drifting', '물결에 잠겨', 'Drifting Underneath', '2:42'),
    ('still_ripples', '잔물결의 밤', 'Still Ripples', '2:55'),
]
ICONS = {'apple': 'regular/apple-logo', 'gplay': 'regular/google-play-logo', 'play': 'fill/play-fill',
         'timer': 'regular/timer', 'lock': 'regular/lock-simple', 'prohibit': 'regular/prohibit', 'chart': 'regular/chart-bar'}

def sprite():
    out = []
    for k, p in ICONS.items():
        svg = open(f'{PH}/{p}.svg').read()
        inner = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.S).group(1)
        out.append(f'<symbol id="i-{k}" viewBox="0 0 256 256">{inner}</symbol>')
    return '<svg class="sprite" aria-hidden="true">' + ''.join(out) + '</svg>'

def windows():
    rows = []
    for i, (sid, ko, en, loop) in enumerate(SOUNDS):
        rows.append(f'''<button class="win" type="button" data-id="{sid}" data-name="{ko}" aria-pressed="false" style="--scene:url(/img/scene_{sid}.webp);--i:{i}">
        <span class="win__cap"><span class="win__pick">오늘의 추천</span><span class="win__name">{ko}</span><span class="win__en">{en} · {loop} 루프</span></span>
        <span class="win__state" aria-hidden="true"><svg><use href="#i-play"/></svg><span class="eq"><i></i><i></i><i></i></span></span>
      </button>''')
    return '\n      '.join(rows)

def og():
    W, H = 1200, 630
    bg = Image.open(f'{ROOT}/img/scene_canopy.webp').convert('RGB')
    bg = bg.resize((W, int(bg.height * W / bg.width))).crop((0, 120, W, 120 + H)).filter(ImageFilter.GaussianBlur(18))
    shade = Image.new('RGB', (W, H), (10, 16, 19)); bg = Image.blend(bg, shade, 0.55)
    shot = Image.open(f'{ROOT}/shots/home.webp').convert('RGB'); shot.thumbnail((280, 600))
    m = Image.new('L', shot.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *shot.size), 26, fill=255)
    bg.paste(shot, (W - shot.width - 110, (H - shot.height) // 2), m)
    from PIL import ImageFont
    d = ImageDraw.Draw(bg)
    f1 = ImageFont.truetype(FONTS[0], 64); f2 = ImageFont.truetype(FONTS[0], 30)
    d.text((96, 190), '잠들기까지,', font=f1, fill=(230, 238, 240))
    d.text((96, 275), '소리 하나면 충분해요', font=f1, fill=(230, 238, 240))
    d.text((96, 395), '밤결 · 수면 백색소음 빗소리', font=f2, fill=(169, 214, 226))
    bg.save(f'{OUT}/og.jpg', quality=88)

shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
for d in ('img', 'shots', 'audio'):
    shutil.copytree(f'{ROOT}/{d}', f'{OUT}/{d}')
for f in ('favicon.png', 'apple-touch-icon.png'):
    shutil.copy(f'{ROOT}/{f}', OUT)
for f in ('styles.css', 'main.js'):
    shutil.copy(f'{ROOT}/src/{f}', OUT)
html = open(f'{ROOT}/src/index.html').read().replace('<!--SPRITE-->', sprite()).replace('<!--WINDOWS-->', windows()).replace('__SITE__', SITE)
open(f'{OUT}/index.html', 'w').write(html)

# Subset fonts to exactly the glyphs on the page.
os.makedirs(f'{OUT}/fonts')
text = re.sub(r'<[^>]+>', ' ', html) + ''.join(s[1] for s in SOUNDS) + '들어보기멈추기'
open('/tmp/bg-glyphs.txt', 'w').write(''.join(sorted(set(text))))
subprocess.run([sys.executable, '-m', 'fontTools.subset', FONTS[0], '--text-file=/tmp/bg-glyphs.txt', '--flavor=woff2', f'--output-file={OUT}/fonts/gowun.woff2'], check=True)
subprocess.run([sys.executable, '-m', 'fontTools.subset', FONTS[1], '--unicodes=U+0020-007E,U+00B7', '--flavor=woff2', f'--output-file={OUT}/fonts/plexmono.woff2'], check=True)
og()
open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
open(f'{OUT}/sitemap.xml', 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE}/</loc></url></urlset>\n')
assert '—' not in html and '–' not in html, 'em/en dash on page'
print('built', SITE)
