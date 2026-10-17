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
# One source for the visible FAQ, FAQPage JSON-LD and llms.txt, so they never drift apart.
FAQ = [
    ('밤결은 무료인가요?', '네. App Store와 Google Play에서 무료로 받을 수 있고, 광고도 로그인도 없습니다.'),
    ('인터넷 없이도 들을 수 있나요?', '네. 모든 소리가 앱 안에 들어 있어 스트리밍하지 않습니다. 비행기 모드에서도 재생되고 데이터를 쓰지 않아요.'),
    ('어떤 소리가 있나요?', '비, 숲, 물 세 갈래의 여덟 가지 소리입니다. ' + ', '.join(s[1] for s in SOUNDS) + '. 각각 2~3분 길이의 음원이 이음매 없이 반복됩니다.'),
    ('화면을 끄거나 다른 앱을 써도 계속 재생되나요?', '네. 백그라운드에서 계속 재생되고, 잠금화면에서 바로 멈추거나 다시 재생할 수 있습니다.'),
    ('수면 타이머는 어떻게 동작하나요?', '15분, 30분, 45분, 1시간, 2시간 중에 고르면 그 시간에 소리가 멈춥니다. 끝나기 전 2분 동안 소리가 서서히 줄어들고, 이 페이드아웃은 타이머 화면에서 끌 수 있어요.'),
    ('개인정보를 수집하나요?', '아니요. 밤결은 어떤 개인정보도 수집하거나 전송하지 않으며, 앱에 인터넷 접근 권한 자체가 없습니다. 음량과 타이머 같은 설정만 기기 안에 저장됩니다.'),
    ('어떤 기기에서 쓸 수 있나요?', 'iPhone, iPad, Android 스마트폰과 태블릿에서 쓸 수 있습니다.'),
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

def faq_html():
    return '\n      '.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)

def jsonld():
    import json
    app = {'@type': 'MobileApplication', '@id': f'{SITE}/#app', 'name': '밤결', 'alternateName': 'Bamgyeol',
           'url': f'{SITE}/', 'inLanguage': 'ko', 'operatingSystem': 'iOS, Android', 'applicationCategory': 'HealthApplication',
           'applicationSubCategory': '수면 사운드', 'description': '빗소리, 숲, 물결. 여덟 가지 밤의 소리를 고르는 순간 바로 재생되는 수면 사운드 앱. 수면 타이머, 백그라운드 재생, 광고와 로그인 없음.',
           'image': f'{SITE}/img/icon.png', 'screenshot': [f'{SITE}/shots/{n}.webp' for n in ('home', 'player', 'timer', 'filtered')],
           'featureList': ['여덟 가지 수면 사운드 (비, 숲, 물)', '끊김 없는 무한 반복 재생', '15분부터 2시간까지 수면 타이머와 페이드아웃',
                           '백그라운드 및 잠금화면 재생', '오프라인 재생', '광고, 로그인, 개인정보 수집 없음', '지난 7일 수면 기록'],
           'isAccessibleForFree': True, 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'KRW'},
           'author': {'@id': f'{SITE}/#author'}, 'publisher': {'@id': f'{SITE}/#author'},
           'sameAs': ['https://apps.apple.com/kr/app/id6816719142', 'https://play.google.com/store/apps/details?id=com.bamgyeol.bamgyeol'],
           'downloadUrl': ['https://apps.apple.com/kr/app/id6816719142', 'https://play.google.com/store/apps/details?id=com.bamgyeol.bamgyeol']}
    graph = [
        {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': f'{SITE}/', 'name': '밤결', 'inLanguage': 'ko', 'publisher': {'@id': f'{SITE}/#author'}},
        {'@type': 'Person', '@id': f'{SITE}/#author', 'name': '홍드로이드'},
        app,
        {'@type': 'FAQPage', '@id': f'{SITE}/#faq', 'inLanguage': 'ko', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ]},
    ]
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)

def llms():
    sounds = '\n'.join(f'- {ko} ({en}), {loop} 루프' for _, ko, en, loop in SOUNDS)
    faq = '\n\n'.join(f'### {q}\n{a}' for q, a in FAQ)
    return f'''# 밤결 (Bamgyeol)

> 빗소리, 숲, 물결. 여덟 가지 밤의 소리를 고르는 순간 바로 재생되는 iOS·Android 수면 사운드 앱. 무료, 광고 없음, 로그인 없음, 오프라인 재생, 개인정보 수집 없음.

- 웹사이트: {SITE}/
- App Store: https://apps.apple.com/kr/app/id6816719142
- Google Play: https://play.google.com/store/apps/details?id=com.bamgyeol.bamgyeol
- 개인정보처리방침: https://bamgyeol-sleep-app.web.app/privacy.html
- 고객지원: https://bamgyeol-sleep-app.web.app/support.html
- 개발: 홍드로이드

## 소리

{sounds}

## 기능

- 소리를 누르면 바로 재생. 섞거나 조절하는 과정 없음
- 2~3분 음원이 이음매 없이 밤새 반복
- 수면 타이머 15분, 30분, 45분, 1시간, 2시간. 끝나기 전 2분 페이드아웃(타이머 화면에서 끄기 가능)
- 화면을 꺼도, 다른 앱을 써도 백그라운드 재생. 잠금화면에서 조작
- 매일 바뀌는 오늘의 추천 소리
- 지난 7일 수면 기록

## 자주 묻는 질문

{faq}
'''

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
html = open(f'{ROOT}/src/index.html').read().replace('<!--SPRITE-->', sprite()).replace('<!--WINDOWS-->', windows()).replace('<!--FAQ-->', faq_html()).replace('<!--JSONLD-->', jsonld()).replace('__SITE__', SITE)
open(f'{OUT}/index.html', 'w').write(html)

# Subset fonts to exactly the glyphs on the page.
os.makedirs(f'{OUT}/fonts')
text = re.sub(r'<[^>]+>', ' ', html) + ''.join(s[1] for s in SOUNDS) + '들어보기멈추기'
open('/tmp/bg-glyphs.txt', 'w').write(''.join(sorted(set(text))))
subprocess.run([sys.executable, '-m', 'fontTools.subset', FONTS[0], '--text-file=/tmp/bg-glyphs.txt', '--flavor=woff2', f'--output-file={OUT}/fonts/gowun.woff2'], check=True)
subprocess.run([sys.executable, '-m', 'fontTools.subset', FONTS[1], '--unicodes=U+0020-007E,U+00B7', '--flavor=woff2', f'--output-file={OUT}/fonts/plexmono.woff2'], check=True)
og()
# AI crawlers are named explicitly: being quoted by answer engines is the point (GEO).
bots = ['*', 'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'PerplexityBot', 'Google-Extended', 'Applebot-Extended', 'Yeti', 'Daumoa']
open(f'{OUT}/robots.txt', 'w').write(''.join(f'User-agent: {b}\n' for b in bots) + f'Allow: /\n\nSitemap: {SITE}/sitemap.xml\n')
import datetime
open(f'{OUT}/sitemap.xml', 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE}/</loc><lastmod>{datetime.date.today()}</lastmod></url></urlset>\n')
open(f'{OUT}/llms.txt', 'w').write(llms())
assert '—' not in html and '–' not in html, 'em/en dash on page'
print('built', SITE)
