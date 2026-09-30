# -*- coding: utf-8 -*-
"""블랙야크 100대 명산 블로그 - 정적 사이트 생성기 (표준 라이브러리만 사용)

  python build.py          → docs/ 에 사이트 생성

출력 폴더가 docs/ 인 것은 GitHub Pages 때문이다. Pages 는 저장소 루트
아니면 /docs 만 게시할 수 있어서, 소스와 사이트를 한 저장소에 두려면
docs/ 여야 한다.
"""
import urllib.parse
import json, os, shutil, html, hashlib, datetime, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'docs')
# 스타일·스크립트 파일 이름. main() 에서 내용 해시를 붙인 이름으로 바꾼다.
# 이름이 내용에 따라 달라져야 브라우저가 예전 파일을 계속 쓰지 않는다.
ASSET = {'css': 'assets/style.css', 'js': 'assets/app.js'}

# 사진 파일 이름 -> 내용 해시가 붙은 이름. main() 의 copy_images() 가 채운다.
IMG = {}


def img(rel):
    """이미지 주소. 내용이 바뀌면 이름도 바뀌어 브라우저가 새로 받는다.

    사진은 이름이 고정이면 교체해도 방문자가 예전 것을 계속 본다.
    지도가 없으면(설정 전 등) 원래 이름을 그대로 돌려준다."""
    return IMG.get(rel, rel)

# 방문자 수 스크립트. main() 에서 채운다. Firebase 설정이 없으면 빈 문자열이라
# 아무것도 실리지 않는다.
VISITS = {'js': '', 'html': ''}

# 배포 주소. og:image·canonical·sitemap 은 절대 주소여야 해서 필요하다.
# 도메인을 옮기면 이 값만 고치면 된다.
SITE_URL = "https://jthird-ops.github.io/"

# 검색엔진 사이트 소유확인. 등록할 때 받은 값을 넣는다. 빈 값은 나가지 않는다.
# 다음 웹마스터도구 소유 확인 — robots.txt 맨 끝에 한 줄로 들어간다
DAUM_PIN = 'j!76085593'

VERIFY = {
    "naver-site-verification": "b875b07332feb15b1f88e64db570658ec357757e",
    "google-site-verification": "5BFFeaf_HVuRt1YrPSbNKNMxJ4LbtXOB9mh8F-GnnmQ",
}

SITE = "블랙야크 100대 명산 기록"
TAGLINE = "100개 산, 100개의 기록 — 코스·난이도·인증장소를 한 곳에"

REGION_ORDER = ["서울", "인천", "경기", "강원", "충북", "충남",
                "경북", "경남", "전북", "전남", "지리산", "제주도"]

ZOOM_W = 260               # 개별 산 페이지 미니맵이 보여줄 범위(지도 좌표 기준)


def e(s):
    return html.escape(str(s), quote=True)


_BBOX = {}


def path_bbox(d):
    """SVG path 문자열의 경계 상자. 미니맵에서 화면 밖 폴리곤을 걸러내는 데 쓴다."""
    if d not in _BBOX:
        xs, ys = [], []
        for pair in d[1:-1].split(' '):
            x, _, y = pair.partition(',')
            xs.append(float(x))
            ys.append(float(y))
        _BBOX[d] = (min(xs), min(ys), max(xs), max(ys))
    return _BBOX[d]


def visible(d, win):
    x0, y0, x1, y1 = path_bbox(d)
    return not (x1 < win[0] or x0 > win[2] or y1 < win[1] or y0 > win[3])


def provinces_svg(kmap, counts=None, win=None):
    """시도 경계 레이어. 지역마다 다른 색으로 칠하고 이름을 얹는다."""
    out = []
    for p in kmap.get('provinces', []):
        r = p['region']
        ds = [d for d in p['paths'] if win is None or visible(d, win)]
        if not ds:
            continue
        paths = ''.join(f'<path d="{d}"/>' for d in ds)
        out.append(f'<g class="prov" data-region="{e(r)}">{paths}</g>')
    labels = []
    for p in kmap.get('provinces', []):
        lb = p.get('label')
        if not lb:
            continue
        r = p['region']
        n = f' {counts[r]}' if counts and r in counts else ''
        labels.append(f'<text class="plabel" data-region="{e(r)}" '
                      f'x="{lb["x"]}" y="{lb["y"]}">{e(r)}{n}</text>')
    return ''.join(out), ''.join(labels)


def load_photos():
    p = os.path.join(ROOT, 'data/photos.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


# 지역별 하늘 색 — 사진이 없는 산의 대체 그래픽에 쓴다
SKY = {
 "서울": ("#cfe0f5", "#8fb3dc"), "인천": ("#d3e6f2", "#93bcd4"),
 "경기": ("#cfe1f7", "#8db4de"), "강원": ("#d2ead8", "#8fbfa2"),
 "충북": ("#f3ecd2", "#d3c58c"), "충남": ("#f7ded0", "#dfaf94"),
 "경북": ("#e2dcf1", "#a99fd0"), "경남": ("#cfe7ee", "#8fbfcd"),
 "전북": ("#f2e6d6", "#d3bb99"), "전남": ("#d5eee1", "#93c6ab"),
 "지리산": ("#e6e0f0", "#a99ec7"), "제주도": ("#efdfee", "#c79cc0"),
}


def ridge_svg(m, vb="0 0 400 300"):
    """사진이 없는 산을 위한 능선 일러스트. 슬러그로 모양을 정해 산마다 다르되
    빌드할 때마다 같은 그림이 나오도록 했다. 사진인 척하지 않는 그래픽이다."""
    h = int(hashlib.md5(m['slug'].encode('utf-8')).hexdigest(), 16)

    def r(i, lo, hi):
        return lo + ((h >> (i * 5)) & 0x3ff) / 1023 * (hi - lo)

    top, bot = SKY.get(m['region'], ("#dfe6ec", "#a6b4c0"))
    # 높이가 높을수록 봉우리를 높게 그린다 (327~1950m → 화면 위쪽으로)
    lift = (m['heightM'] - 327) / (1950 - 327)
    layers = []
    for i, (base, col, op) in enumerate([(250, "#7d93a4", .38),
                                         (268, "#5d7688", .58),
                                         (286, "#3d5464", .92)]):
        peak = base - (52 + lift * 58) * (1 - i * 0.16)
        px = r(i * 3 + 1, 120, 280)
        a = r(i * 3 + 2, 30, 90)
        b = r(i * 3 + 3, 300, 370)
        mid1 = base - (peak_off := (base - peak) * r(i * 3 + 4, .35, .7))
        mid2 = base - (base - peak) * r(i * 3 + 5, .3, .65)
        d = (f"M-10,300 L-10,{base:.0f} L{a:.0f},{mid1:.0f} "
             f"L{px - 60:.0f},{base - (base - peak) * .55:.0f} "
             f"L{px:.0f},{peak:.0f} L{px + 70:.0f},{mid2:.0f} "
             f"L{b:.0f},{base - 6:.0f} L410,{base + 8:.0f} L410,300 Z")
        layers.append(f'<path d="{d}" fill="{col}" opacity="{op}"/>')

    sun_x, sun_y = r(9, 60, 340), r(10, 48, 96)
    return (
        f'<svg class="ridge" viewBox="{vb}" preserveAspectRatio="xMidYMid slice" '
        f'role="img" aria-label="{e(m["name"])} 일러스트">'
        f'<defs><linearGradient id="s{h % 99999}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/>'
        f'</linearGradient></defs>'
        f'<rect width="400" height="300" fill="url(#s{h % 99999})"/>'
        f'<circle cx="{sun_x:.0f}" cy="{sun_y:.0f}" r="17" fill="#fff" opacity=".55"/>'
        + ''.join(layers) + '</svg>')


def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    ax, ay = pts[0]
    bx, by = pts[-1]
    dx, dy = bx - ax, by - ay
    den = (dx * dx + dy * dy) ** .5 or 1e-9
    imax, dmax = 0, -1.0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * px - dx * py + bx * ay - by * ax) / den
        if d > dmax:
            imax, dmax = i, d
    if dmax <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[:imax + 1], eps)[:-1] + _rdp(pts[imax:], eps)


_MINI = {}


def mini_map_paths(kmap, eps=4.0, keep=3):
    """메뉴 썸네일용으로 지도를 아주 거칠게 줄인다. 큰 덩어리 몇 개만 남긴다."""
    if not _MINI:
        rows = []
        for d in kmap['paths']:
            pts = []
            for pair in d[1:-1].split(' '):
                x, _, y = pair.partition(',')
                pts.append((float(x), float(y)))
            x0, y0, x1, y1 = path_bbox(d)
            rows.append(((x1 - x0) * (y1 - y0), pts))
        rows.sort(key=lambda r: -r[0])
        out = []
        for _, pts in rows[:keep]:
            q = _rdp(pts, eps)
            if len(q) > 3:
                out.append('M' + ' '.join(f'{x:.0f},{y:.0f}' for x, y in q) + 'Z')
        _MINI['d'] = out
    return _MINI['d']


def menu_photo(slug, photos):
    ph = photos.get(slug)
    if not ph:
        return ''
    return (f'<img src="{img("assets/photos/" + thumb_file(ph))}" alt="" '
            f'loading="lazy" decoding="async">')


def thumb_file(ph):
    """목록 카드용 작은 이미지. 없으면 원본으로 되돌린다."""
    t = ph['file'].rsplit('.', 1)[0] + '-t.jpg'
    return t if os.path.exists(os.path.join(ROOT, 'assets/photos', t)) else ph['file']


def credit_line(ph, short=False):
    """사진 저작자 표기. CC 라이선스는 저작자와 라이선스를 반드시 밝혀야 한다."""
    a = e(ph['author'])
    prov = ph.get('provider')
    if ph.get('own'):                       # 직접 찍은 사진
        d = f" · {e(ph['date'])}" if ph.get('date') else ''
        return ('직접 촬영' if short else f'직접 촬영{d}')
    if short:
        return f"© {a} · {e(prov) + ' · ' if prov else ''}{e(ph['license'])}"
    lic = (f'<a href="{e(ph["license_url"])}" target="_blank" rel="noopener">{e(ph["license"])}</a>'
           if ph.get('license_url') else e(ph['license']))
    # 위키미디어 사진은 원본 문서로 링크하고, 한국관광공사 사진은 제공처를 밝힌다
    if prov:
        title = f'<span class="c-title">{e(ph["title"])} · </span>'
        who = f'{a} · <a href="{e(ph["source"])}" target="_blank" rel="noopener">{e(prov)}</a>'
    else:
        title = (f'<span class="c-title"><a href="{e(ph["source"])}" target="_blank" '
                 f'rel="noopener">{e(ph["title"])}</a> · </span>')
        who = a
    return f'{title}{who} · {lic}'


def load_map():
    return json.load(open(os.path.join(ROOT, 'data/korea_map.json'), encoding='utf-8'))


def load():
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    for m in mts:
        p = os.path.join(ROOT, 'content', m['slug'] + '.json')
        m['content'] = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
    mts.sort(key=lambda m: m['rank'])
    return mts


# ---------------------------------------------------------------- 공통 셸
def page(title, body, depth=0, desc="", extra_head="", image="", path="", og_type="article"):
    up = '../' * depth
    # 파일 이름이 한글이라 og:image·canonical 은 퍼센트 인코딩해 둔다.
    # 카카오톡·페이스북 크롤러가 원문 UTF-8 주소를 못 읽는 경우가 있다.
    verify = '\n'.join(f'<meta name="{k}" content="{v}">'
                       for k, v in VERIFY.items() if v)
    path = urllib.parse.quote(path)
    image = urllib.parse.quote(img(image or 'assets/photos/hero.jpg'))
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{verify}
<title>{e(title)}</title>
<meta name="description" content="{e(desc or TAGLINE)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc or TAGLINE)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{e(SITE)}">
<meta property="og:locale" content="ko_KR">
<meta property="og:url" content="{SITE_URL}{path}">
<meta property="og:image" content="{SITE_URL}{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE_URL}{path}">
<link rel="icon" href="{up}{img('assets/favicon.png')}" type="image/png">
<link rel="apple-touch-icon" href="{up}{img('assets/apple-touch-icon.png')}">
<link rel="stylesheet" href="{up}{ASSET['css']}">
{extra_head}
</head>
<body>
<header class="site">
  <a class="brand" href="{up}index.html">
    <span class="mark">
      <svg viewBox="0 0 40 40" aria-hidden="true">
        <defs>
          <mask id="mark100">
            <rect width="40" height="40" fill="#fff"/>
            <text x="20" y="25.5" text-anchor="middle">100</text>
          </mask>
        </defs>
        <image href="{up}{img('assets/mark.jpg')}" width="40" height="40"
               preserveAspectRatio="xMidYMid slice" mask="url(#mark100)"/>
      </svg>
      <b class="sr">100대 명산</b>
    </span>
    <span class="brand-text"><b>블랙야크 100대 명산</b><em>등반 기록 블로그</em></span>
  </a>
  <nav>
    <a href="{up}index.html#tab-list">100대 명산</a>
    <a href="{up}index.html#tab-photos">대표 명산</a>
    <a href="{up}index.html#tab-map">지도</a>
    <a href="{up}index.html#tab-regions">지역별</a>
    <a href="{up}index.html#tab-auth">인증방법</a>
    <a href="{up}index.html#tab-app">어플</a>
    <a href="{up}guestbook.html">방명록</a>
  </nav>
</header>
{body}
<footer class="site">
  <p><b>{e(SITE)}</b> · 산 데이터 100건 · 지도 데이터 Natural Earth (public domain)</p>
  <p><a class="foot-link" href="{up}credits.html">사진 출처</a>
     <a class="foot-link" href="{up}guestbook.html">방명록</a></p>
  <p class="muted">본문의 코스·시간·교통 정보는 작성 시점 기준입니다. 산행 전 국립공원공단·지자체 공지와 기상 상황을 반드시 확인하세요.</p>
  {VISITS['html']}
</footer>
<script src="{up}{ASSET['js']}"></script>
{VISITS['js']}
</body>
</html>
"""


# ---------------------------------------------------------------- 홈
INDEX_LD = '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"WebSite","name":"블랙야크 100대명산 기록","alternateName":["블랙야크 100대 명산","BAC 100대명산"],"url":"https://jthird-ops.github.io/","inLanguage":"ko-KR"}
</script>
'''


def done_badge(c):
    """등반기록이 있는 산의 카드 사진 위 '완등' 배지. 가장 최근 산행 날짜를 쓴다."""
    logs = (c or {}).get('log') or []
    ds = sorted(x.get('date', '') for x in logs if x.get('date'))
    if not logs:
        return ''
    d = ds[-1][2:].replace('-', '.') if ds else ''
    return f'<span class="done-badge">✓ 완등{" " + d if d else ""}</span>'


def build_index(mts):
    import _guestbook, _appcount           # 방명록·다운로드 수 (Firebase)
    import _appshot                        # 어플 소개와 화면
    courses = sum(len(m['content']['courses']) for m in mts if m['content'])
    by_region = {}
    for m in mts:
        by_region.setdefault(m['region'], []).append(m)

    kmap = load_map()
    photos = load_photos()
    shapes = ''.join(f'<path d="{d}"/>' for d in kmap['paths'])
    counts = {r: len(v) for r, v in by_region.items()}
    provs, plabels = provinces_svg(kmap, counts)
    markers = []
    for m in mts:
        cls = 'pin'
        markers.append(
            f'<a class="{cls}" data-region="{e(m["region"])}" '
            f'href="mountain/{e(m["slug"])}.html">'
            f'<circle cx="{m["x"]}" cy="{m["y"]}" r="14"/>'
            f'<title>{e(m["name"])} · {e(m["height"])} · {e(m["region"])}</title></a>')

    # 메뉴 카드 배경 — 지도·지역·어플은 그림으로, 나머지는 사진으로 표현한다
    mini = ''.join(f'<path d="{d}"/>' for d in mini_map_paths(kmap))
    dots = ''.join(
        f'<circle cx="{m["x"]:.0f}" cy="{m["y"]:.0f}" r="17"/>'
        for m in mts[::3])
    mc_map = (f'<svg class="mc-svg" viewBox="0 0 {kmap["width"]} {kmap["height"]}" '
              f'preserveAspectRatio="xMidYMid meet" aria-hidden="true">'
              f'<g class="mm-land">{mini}</g><g class="mm-dot">{dots}</g></svg>')
    swatch = ''.join(
        f'<rect x="{6 + (i % 3) * 44}" y="{6 + (i // 3) * 44}" width="38" height="38" rx="10" '
        f'class="sw-{e(r)}"/>' for i, r in enumerate(REGION_ORDER))
    mc_region = (f'<svg class="mc-svg" viewBox="0 0 138 182" preserveAspectRatio="xMidYMid meet" '
                 f'aria-hidden="true">{swatch}</svg>')
    mc_app = ('<svg class="mc-svg" viewBox="40 6 120 128" preserveAspectRatio="xMidYMid meet" '
              'aria-hidden="true"><rect x="72" y="18" width="56" height="104" rx="12" '
              'class="ph-body"/><rect x="79" y="30" width="42" height="76" rx="4" class="ph-scr"/>'
              '<circle cx="100" cy="114" r="4" class="ph-btn"/>'
              '<path d="M100 46 L100 84 M86 70 L100 84 L114 70" class="ph-dl"/></svg>')

    chips = ['<button class="chip active" data-region="전체">전체 <i>100</i></button>']
    for r in REGION_ORDER:
        if r in by_region:
            chips.append(f'<button class="chip" data-region="{e(r)}">{e(r)} <i>{len(by_region[r])}</i></button>')

    cards = []
    for m in mts:
        c = m['content']
        summary = c['summary'] if c else '글 준비 중입니다.'
        ph = photos.get(m['slug'])
        thumb = (f'<img src="{img("assets/photos/" + thumb_file(ph))}" alt="{e(m["name"])} 사진" '
                 f'loading="lazy" decoding="async">') if ph else ridge_svg(m)
        cards.append(f"""
      <a class="card{'' if c else ' todo'}" href="mountain/{e(m['slug'])}.html"
         data-region="{e(m['region'])}" data-name="{e(m['name'])}">
        <span class="card-thumb">{thumb}{done_badge(c)}</span>
        <span class="card-body">
          <span class="card-top"><i class="rank">{m['rank']}</i><i class="tag">{e(m['region'])}</i></span>
          <strong>{e(m['name'])}</strong>
          <span class="h">{e(m['height'])}</span>
          <span class="s">{e(summary)}</span>
        </span>
      </a>""")

    region_blocks = []
    for r in REGION_ORDER:
        if r not in by_region:
            continue
        ms = sorted(by_region[r], key=lambda x: -x['heightM'])
        items = ' '.join(
            f'<a href="mountain/{e(m["slug"])}.html">{e(m["name"])} <em>{e(m["height"])}</em></a>'
            for m in ms)
        region_blocks.append(
            f'<div class="region-block" data-region="{e(r)}">'
            f'<h3><button class="region-pick" data-region="{e(r)}">{e(r)} '
            f'<span>{len(ms)}</span></button></h3>'
            f'<div class="pills">{items}</div></div>')

    # 사진이 있는 산 중 높은 순으로 12곳만 대표로 세운다
    featured = sorted((m for m in mts if m['slug'] in photos),
                      key=lambda m: -m['heightM'])[:12]
    featured.sort(key=lambda m: m['rank'])
    pcards = []
    for m in featured:
        ph = photos[m['slug']]
        c = m['content']
        pcards.append(f"""
      <a class="pcard" href="mountain/{e(m['slug'])}.html">
        <span class="pcard-img"><img src="{img("assets/photos/" + thumb_file(ph))}"
             alt="{e(m['name'])} 사진" loading="lazy" decoding="async">{done_badge(c)}</span>
        <span class="pcard-body">
          <span class="pc-top"><i>{e(m['region'])}</i><b>{e(m['height'])}</b></span>
          <strong>{e(m['name'])}</strong>
          <span class="pc-sum">{e(c['summary'] if c else '')}</span>
          <span class="pc-go">기록 보기 →</span>
        </span>
        <span class="pcard-credit">{credit_line(ph, short=True)}</span>
      </a>""")

    hero = photos.get('hero')
    hero_bg = (f'<img class="vhero-bg" src="{img("assets/photos/" + hero["file"])}" alt="" '
               f'fetchpriority="high" decoding="async">') if hero else ''
    hero_credit = (f'<p class="vhero-credit">사진 {credit_line(hero)}</p>') if hero else ''

    body = f"""
<section class="vhero">
  {hero_bg}
  <div class="vhero-shade"></div>
  <div class="vhero-inner">
    <p class="eyebrow">BAC · BLACKYAK ALPINE CLUB</p>
    <h1>블랙야크 100대명산을<br>하나씩 기록합니다</h1>
    <p class="lead">{e(TAGLINE)}</p>
  </div>
  {hero_credit}
</section>

<section class="statbar">
  <div class="stats">
    <div><b>100</b><span>대상 산</span></div>
    <div><b>{courses}</b><span>등산 코스</span></div>
    <div><b>{len(by_region)}</b><span>지역</span></div>
    <div><b>1950m</b><span>최고 · 한라산</span></div>
  </div>
</section>

<nav class="menu" id="menu">
  <button class="menu-card" data-tab="tab-list">
    <span class="mc-bg">{menu_photo('지리산천왕봉', photos)}</span>
    <span class="mc-txt"><i>01</i><b>100대 명산</b><em>전체 목록과 검색</em></span>
  </button>
  <button class="menu-card" data-tab="tab-photos">
    <span class="mc-bg">{menu_photo('설악산', photos)}</span>
    <span class="mc-txt"><i>02</i><b>대표 명산 12곳</b><em>사진으로 둘러보기</em></span>
  </button>
  <button class="menu-card art" data-tab="tab-map">
    <span class="mc-bg">{mc_map}</span>
    <span class="mc-txt"><i>03</i><b>지도로 한눈에 보기</b><em>지도에서 고르기</em></span>
  </button>
  <button class="menu-card art" data-tab="tab-regions">
    <span class="mc-bg">{mc_region}</span>
    <span class="mc-txt"><i>04</i><b>지역별로 한눈에</b><em>12개 지역별 목록</em></span>
  </button>
  <button class="menu-card" data-tab="tab-auth">
    <span class="mc-bg">{menu_photo('천마산', photos)}</span>
    <span class="mc-txt"><i>05</i><b>인증방법</b><em>정상석 인증 절차</em></span>
  </button>
  <button class="menu-card art" data-tab="tab-app">
    <span class="mc-bg">{mc_app}</span>
    <span class="mc-txt"><i>06</i><b>정복 어플</b><em>완등 기록 남기기</em></span>
  </button>
</nav>

<div id="tab-list" class="tabpanel">
  <section id="list" class="list-section">
    <h2>전체 100대 명산</h2>
    <div class="controls">
      <input type="search" id="q" placeholder="산 이름으로 검색 (예: 설악, 지리)" aria-label="산 이름 검색">
      <div class="chips">{''.join(chips)}</div>
    </div>
    <p class="count" id="count"></p>
    <div class="grid" id="grid">{''.join(cards)}</div>
    <p class="empty" id="empty" hidden>검색 결과가 없습니다.</p>
  </section>
</div>

<div id="tab-photos" class="tabpanel" hidden>
  <section id="photos" class="photos">
    <h2>대표 명산 {len(pcards)}곳</h2>
    <p class="sub">사진을 누르면 그 산의 기록으로 이동합니다.</p>
    <div class="pgrid">{''.join(pcards)}</div>
    <p class="more-link"><a href="#tab-list">100개 산 전체 목록 보기 →</a></p>
  </section>
</div>

<div id="tab-map" class="tabpanel" hidden>
  <section id="map" class="map-section">
    <h2>지도로 한눈에 보기</h2>
    <p class="sub">시도별로 색을 나눴습니다. 점을 누르면 해당 글로, 아래 지역 버튼을 누르면 그 지역만 지도에 남습니다.</p>
    <div class="chips chips-map">{''.join(chips)}</div>
    <div class="map-box">
      <svg class="kmap" id="kmap" viewBox="{kmap['viewBox']}" width="{kmap['width']}" height="{kmap['height']}" role="img"
           aria-label="대한민국 시도별 100대 명산 위치 지도">
        <g class="land">{shapes}</g>
        <g class="provs">{provs}</g>
        <g class="plabels">{plabels}</g>
        <g class="pins">{''.join(markers)}</g>
      </svg>
      <p class="attrib">지도 경계 데이터: Natural Earth 1:10m · 시도 경계 admin-1 (public domain)</p>
    </div>
  </section>
</div>

<div id="tab-regions" class="tabpanel" hidden>
  <section id="regions" class="regions">
    <h2>지역별로 한눈에</h2>
    <p class="sub">지역 이름을 누르면 그 지역의 산만 모아 <b>100대 명산</b> 목록으로 이동합니다.</p>
    {''.join(region_blocks)}
  </section>
</div>

<div id="tab-auth" class="tabpanel" hidden>
  <section class="auth">
    <h2>블랙야크 100대 명산 인증방법</h2>
    <p class="sub">블랙야크 알파인클럽(BAC)의 '명산100' 도전 프로그램 기준입니다.</p>

    <ol class="steps">
      <li>
        <b>BAC 앱 설치하고 가입하기</b>
        <p>앱스토어·플레이스토어에서 <em>BAC</em> 를 검색해 '블랙야크 알파인 클럽 BAC' 앱을 설치하고
           회원가입합니다. 앱 사용과 인증은 무료입니다.</p>
      </li>
      <li>
        <b>도전 프로그램 신청하기</b>
        <p>앱에서 '명산100' 도전을 신청합니다. 신청한 시점부터의 산행이 인증 대상이 됩니다.</p>
      </li>
      <li>
        <b>인증 용품 챙기기</b>
        <p>인증 타월(수건)이나 공식 굿즈를 함께 들고 찍는 것이 일반적입니다.
           산행 전에 미리 챙겨두세요.</p>
      </li>
      <li>
        <b>정상에서 GPS 인증하기</b>
        <p>정상석 주변 반경 약 100m 안에서 앱을 열고 해당 산을 선택해
           <em>GPS 인증(발도장)</em> 을 먼저 찍습니다. 통신이 약한 곳이 많으니
           정상에 서면 바로 시도하는 편이 안전합니다.</p>
      </li>
      <li>
        <b>정상석 사진 등록하기</b>
        <p>지정된 정상석 앞에서 찍은 사진을 앱에 올립니다.
           GPS 인증 후 <em>48시간 안에</em> 사진을 등록해야 하며, 넘기면 GPS 기록이 지워져
           다시 올라가야 할 수 있습니다.</p>
      </li>
      <li>
        <b>승인 확인하기</b>
        <p>등록한 인증은 검토를 거쳐 승인됩니다. 100곳을 모두 채우면 완주자로 등록되고
           완주 기념 굿즈를 받을 수 있습니다.</p>
      </li>
    </ol>

    <div class="auth-note">
      <h3>주의할 점</h3>
      <ul>
        <li><b>지정된 정상석에서만</b> 인증됩니다. 능선을 길게 종주해도 인증 지점이 늘지 않습니다.</li>
        <li><b>안전수칙을 어긴 사진은 반려</b>될 수 있습니다. 겨울철 아이젠 미착용,
            난간 밖이나 위험 지형 위에서 촬영한 사진 등이 해당합니다.</li>
        <li>같은 산에 여러 봉우리가 있어도 <b>인증 지점은 한 곳</b>입니다.
            설악산은 대청봉, 지리산은 천왕봉·반야봉·바래봉이 각각 별개 항목입니다.</li>
        <li>한라산처럼 <b>사전 예약이 필요한 산</b>은 예약을 못 하면 정상에 오를 수 없습니다.</li>
      </ul>
      <p class="muted">인증 규정은 바뀔 수 있습니다. 산행 전 BAC 앱 공지나
         <a href="https://bac.blackyak.com/BAC/ChallengeProgram/114" target="_blank" rel="noopener">공식 안내</a>를
         확인하세요. 문의는 BAC 고객센터 1800-6166.</p>
    </div>

    <p class="more-link"><a href="https://bac.blackyak.com/BAC/BacApp/auth/" target="_blank" rel="noopener">BAC 공식 인증방법 안내 보기 →</a></p>
  </section>
</div>

<div id="tab-app" class="tabpanel" hidden>
  <section class="appsec">
    <h2>100대 명산 정복 어플</h2>
    <p class="sub">완등한 산을 지도 위에 표시하고 날짜와 함께 기록하는 어플입니다.</p>
    <div class="app-box">
      <div class="app-cta">
        <a class="btn-hero primary" href="app/bac100-tracker.html"
           download="bac100-tracker.html">어플 내려받기</a>
        <a class="btn-hero outline" href="app/index.html">여기서 바로 열기</a>
      </div>
      <p class="app-note">파일 하나(약 110KB)를 내려받아 두 번 눌러 열면 됩니다.
         설치할 것도, 인터넷도 필요 없습니다.</p>
      {_appcount.html()}
      <ul class="app-feat">
        <li><b>지도에서 한눈에</b> 완등한 산은 초록, 남은 산은 빨강으로 표시됩니다.
            이 블로그와 같은 지도를 씁니다.</li>
        <li><b>날짜까지 기록</b> 산마다 다녀온 날을 적어 둘 수 있습니다.</li>
        <li><b>지역·완등 여부로 걸러보기</b> 남은 산만 모아 볼 수 있습니다.</li>
        <li><b>인터넷 없이</b> 내려받은 파일은 신호가 없는 산속에서도 열립니다.</li>
      </ul>
      <div class="app-install">
        <h3>내려받은 뒤에</h3>
        <p><b>컴퓨터</b> — 내려받은 <code>bac100-tracker.html</code> 을 두 번 누르면
           브라우저에서 열립니다. 즐겨찾기에 넣어 두면 편합니다.</p>
        <p><b>휴대폰</b> — 여기서 바로 열기로 연 뒤 브라우저 메뉴에서
           <b>홈 화면에 추가</b>를 고르면 아이콘이 생깁니다. 아이폰은 사파리의 공유 단추,
           안드로이드는 크롬 우측 상단 메뉴에 있습니다.</p>
      </div>
      <p class="more-link"><a href="app-guide.html">어플 사용방법 자세히 보기 →</a></p>
      {_appshot.block(kmap, mts)}
      <p class="app-warn">기록은 어플을 연 브라우저 안에만 저장됩니다. 서버로 보내지
         않으므로 다른 기기에서 열면 기록이 보이지 않고, 브라우저 데이터를 지우면
         사라집니다. 내려받은 파일과 여기서 연 어플은 서로 다른 곳에 저장하므로
         <b>한쪽만 정해서 쓰시는 편</b>이 좋습니다.</p>
    </div>
  </section>
</div>
"""
    return page("블랙야크 100대명산 | 100대 명산 코스·난이도·인증장소 총정리", body, 0,
                desc="블랙야크 100대명산(BAC) 100개 산의 등산 코스, 난이도, 정상 인증장소를 지역별 목록과 지도로 한눈에 정리했습니다.",
                og_type="website",
                extra_head=INDEX_LD + _appcount.js(_guestbook.config()))


# ---------------------------------------------------------------- 어플 사용방법
GUIDE_TITLE = "블랙야크 100대명산 등반기록 어플 사용방법 | 완등 기록·지도·백업"
GUIDE_DESC = ("블랙야크 100대명산 완등 기록 어플 사용법. 설치 없이 열고, 다녀온 산을 "
              "날짜와 함께 기록해 지도에서 초록·빨강으로 확인하는 방법과 백업·복구까지 정리했어요.")
GUIDE_CSS = """<style>
.guide{max-width:860px;margin:0 auto;padding:26px 20px 56px}
.guide .lead{font-size:17px;color:var(--sub);margin:10px 0 0}
.guide h2{font-size:22px;margin:44px 0 14px;padding-top:6px}
.guide h3{font-size:17px;margin:0 0 4px}
.g-cta{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0 6px}
.g-cta a{display:inline-block;padding:11px 20px;border-radius:999px;font-weight:700;font-size:15px;
  border:1.5px solid var(--green);background:var(--green);color:#fff}
.g-cta a:hover{background:#188044;border-color:#188044}
.g-cta a.outline{background:transparent;color:var(--green)}
.g-cta a.outline:hover{background:var(--green-soft)}
.g-why{background:var(--green-soft);border-radius:14px;padding:16px 20px;margin:22px 0 0}
.g-why h2{font-size:18px;margin:0 0 6px;padding:0}
.g-why p{margin:0 0 8px}
.g-why p:last-child{margin:0}
.g-toc{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:14px 18px;margin:26px 0 0;font-size:15px}
.g-toc ol{margin:6px 0 0;padding-left:20px;columns:2;column-gap:28px}
.g-toc a{color:var(--green)}
.g-shot{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px}
.g-shot svg{display:block;width:100%;height:auto}
.g-shot figcaption{font-size:13px;color:var(--sub);margin-top:8px}
.g-parts{margin:14px 0 0;padding-left:20px}
.g-mobile{margin:30px 0 0}
.g-mobile p{margin:6px 0 14px}
.g-phones{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:620px}
.g-phones figure{margin:0}
.g-phones img{display:block;width:100%;height:auto;border:8px solid #1b1f24;border-radius:26px;
  background:#fff;box-shadow:0 6px 18px rgba(0,0,0,.12)}
.g-phones figcaption{font-size:13px;color:var(--sub);text-align:center;margin-top:8px}
.g-steps{list-style:none;margin:0;padding:0;counter-reset:st}
.g-steps>li{position:relative;background:var(--card);border:1px solid var(--line);
  border-radius:14px;padding:16px 18px 14px 62px;margin:0 0 12px;counter-increment:st}
.g-steps>li::before{content:counter(st);position:absolute;left:18px;top:16px;width:30px;height:30px;
  border-radius:50%;background:var(--green);color:#fff;font-weight:700;display:grid;place-items:center;font-size:15px}
.g-steps p{margin:4px 0 0;color:var(--ink)}
.g-steps .tip{font-size:14px;color:var(--sub)}
.g-dot{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:-1px;margin:0 2px}
.g-dot.on{background:#1f9d55}.g-dot.off{background:#d64545}
.g-note{background:var(--green-soft);border-radius:14px;padding:14px 18px}
.g-note ul{margin:0;padding-left:20px}
.g-faq dt{font-weight:700;margin-top:14px}
.g-faq dd{margin:4px 0 0;color:var(--ink)}
.guide kbd{font:inherit;font-size:14px;background:#f1f3f5;border:1px solid var(--line);
  border-radius:6px;padding:0 6px}
@media (max-width:640px){.g-toc ol{columns:1}.g-steps>li{padding-left:56px}
  .g-phones{gap:10px}.g-phones img{border-width:5px;border-radius:18px}}
</style>
"""


def build_app_guide(mts, kmap):
    """어플(등반 트래커) 사용방법 페이지. 검색 유입·홍보 링크용 독립 페이지."""
    import _appshot
    body = f"""
<article class="guide">
  <p class="crumb"><a href="index.html#tab-app">← 어플 소개로</a></p>
  <h1>블랙야크 100대명산 등반기록 어플 사용방법</h1>
  <p class="lead">다녀온 산을 날짜와 함께 기록하면 지도에서 완등한 산은 초록, 남은 산은
     빨강으로 보여 주는 무료 어플이에요. 회원가입이나 설치 없이 바로 써요.</p>
  <section class="g-why">
    <h2>엑셀·수첩 기록을 지도 위로 옮기세요</h2>
    <p>블랙야크 100대명산에 도전하면서 완등한 산을 엑셀에 따로 정리하거나 수첩에 적어 두셨다면,
       이제 그 기록을 지도와 함께 한곳에서 관리할 수 있어요. 완등한 산을 체크하면 지도에 바로 초록으로 표시되어
       <b>어느 지역이 아직 비어 있는지</b> 한눈에 보여요.</p>
    <p>지역별로 남은 산을 모아 보고, 목록의 높이와 이 사이트의 산별 <b>코스·난이도</b> 정보를 함께 살펴
       다음 목표를 정해 보세요. 초록 점이 하나씩 늘어나는 지도가 100대명산 완등까지 가는 길에
       좋은 동기부여가 돼요.</p>
  </section>
  <div class="g-cta">
    <a href="index.html#tab-app">어플 바로 열기</a>
    <a class="outline" href="app/bac100-tracker.html" download="bac100-tracker.html">파일로 내려받기</a>
  </div>

  <nav class="g-toc" aria-label="목차"><b>목차</b>
    <ol>
      <li><a href="#g-screen">화면 구성 (컴퓨터·휴대폰)</a></li>
      <li><a href="#g-open">어플 여는 법</a></li>
      <li><a href="#g-record">완등 기록하기</a></li>
      <li><a href="#g-find">산 찾기·남은 산 보기</a></li>
      <li><a href="#g-backup">백업과 복구</a></li>
      <li><a href="#g-note">꼭 알아둘 점</a></li>
      <li><a href="#g-faq">자주 묻는 질문</a></li>
    </ol>
  </nav>

  <h2 id="g-screen">1. 화면 구성 (컴퓨터·휴대폰)</h2>
  <figure class="g-shot">
    {_appshot.svg(kmap, mts)}
    <figcaption>어플과 같은 지도 데이터로 그린 화면이에요. 실제 화면과 배치는 같고 색·글꼴은 조금 다를 수 있어요.</figcaption>
  </figure>
  <ul class="g-parts">
    <li><b>맨 위 진행률</b> — <code>37 / 100 완등 (37%)</code>처럼 지금까지 오른 산의 수가 나와요.</li>
    <li><b>검색창·칩</b> — 산 이름으로 찾거나, 지역·완등 여부로 목록을 걸러요.</li>
    <li><b>왼쪽 목록</b> — 100개 산이 한 줄씩. 줄마다 <b>등반일시</b> 칸과
        <b>등반</b>·<b>미등반</b> 동그라미가 있어요.</li>
    <li><b>오른쪽 지도</b> — 같은 산이 점으로 찍혀요. <span class="g-dot on"></span>초록은 완등,
        <span class="g-dot off"></span>빨강은 미완등이에요.</li>
  </ul>

  <div class="g-mobile">
    <h3>스마트폰에서도 그대로 써요</h3>
    <p>휴대폰에서 열면 화면 폭에 맞춰 목록과 지도가 위아래로 나뉘어요. 기능은 컴퓨터와 같고,
       산행을 마치고 내려오는 길에 바로 기록할 수 있어요.</p>
    <div class="g-phones">
      <figure><img src="{img('assets/photos/app-mobile-list.jpg')}" width="600" height="891" loading="lazy"
           alt="스마트폰에서 본 어플 목록 화면. 완등한 산은 초록 줄과 등반 날짜로 표시된다">
        <figcaption>목록 — 등반 동그라미와 날짜</figcaption></figure>
      <figure><img src="{img('assets/photos/app-mobile-map.jpg')}" width="600" height="891" loading="lazy"
           alt="스마트폰에서 본 어플 지도 화면. 완등한 산은 초록, 남은 산은 빨강 점으로 표시된다">
        <figcaption>지도 — 완등 초록, 미완등 빨강</figcaption></figure>
    </div>
  </div>

  <h2 id="g-open">2. 어플 여는 법</h2>
  <ol class="g-steps">
    <li><h3>휴대폰 — 바로 열고 홈 화면에 추가</h3>
      <p><b>어플 바로 열기</b>를 누른 뒤 브라우저 메뉴에서 <b>홈 화면에 추가</b>를 고르면
         바탕화면에 아이콘이 생겨요. 다음부터는 아이콘만 누르면 돼요.</p>
      <p class="tip">아이폰: 사파리 아래쪽 공유 단추 → 홈 화면에 추가 · 안드로이드: 크롬 오른쪽 위 ⋮ → 홈 화면에 추가</p></li>
    <li><h3>컴퓨터 — 파일로 내려받아 두 번 클릭</h3>
      <p><b>파일로 내려받기</b>를 누르면 <code>bac100-tracker.html</code>(약 110KB) 파일 하나를 받게 돼요.
         두 번 누르면 브라우저에서 열리고, 인터넷이 없어도 동작해요.</p></li>
  </ol>

  <h2 id="g-record">3. 완등 기록하기</h2>
  <ol class="g-steps">
    <li><h3>다녀온 산의 <span class="g-dot on"></span>등반 동그라미 누르기</h3>
      <p>줄이 초록으로 바뀌고 지도의 점도 초록이 돼요. 날짜 칸이 비어 있으면
         <b>오늘 날짜가 자동으로</b> 들어가요.</p></li>
    <li><h3>예전에 다녀온 산은 날짜부터 넣기</h3>
      <p><b>등반일시</b> 칸을 눌러 달력에서 날짜를 고르면, 등반 동그라미를 따로 누르지 않아도
         완등으로 처리돼요.</p></li>
    <li><h3>잘못 눌렀다면 <span class="g-dot off"></span>미등반 누르기</h3>
      <p>미완등으로 되돌아가요. 적어 둔 날짜는 그대로 남으니 필요하면 날짜 칸을 지우세요.</p></li>
    <li><h3>저장 버튼은 없어요</h3>
      <p>누르는 순간 이 기기에 <b>자동 저장</b>되고, 다음에 열면 그대로 복원돼요.</p></li>
  </ol>

  <h2 id="g-find">4. 산 찾기·남은 산 보기</h2>
  <ol class="g-steps">
    <li><h3>이름으로 찾기</h3>
      <p>검색창에 <kbd>설악</kbd>처럼 일부만 넣어도 바로 걸러져요.</p></li>
    <li><h3>지역·완등 여부로 거르기</h3>
      <p>칩에서 <b>강원</b>·<b>경남</b> 같은 지역을 누르거나, <b>미완등</b>을 눌러 아직 못 간 산만 모아 봐요.
         다음 산행지를 고를 때 편해요.</p></li>
    <li><h3>지도에서 고르기</h3>
      <p>지도의 점을 누르면 목록이 그 산의 줄로 이동하고, 목록의 줄을 누르면 지도의 점이 깜빡여요.</p></li>
  </ol>

  <h2 id="g-backup">5. 백업과 복구</h2>
  <ol class="g-steps">
    <li><h3>백업(내보내기)</h3>
      <p>맨 위 <b>백업(내보내기)</b>를 누르면 <code>BAC100_등반기록_날짜.json</code> 파일이 저장돼요.
         기록이 쌓일 때마다 한 번씩 받아 두세요.</p></li>
    <li><h3>복구(불러오기)</h3>
      <p>새 휴대폰·다른 컴퓨터·다른 브라우저에서 어플을 열고 <b>복구(불러오기)</b>를 눌러
         백업 파일을 고르면 기록이 그대로 돌아와요.</p>
      <p class="tip">휴대폰 기록을 컴퓨터로 옮길 때도 같은 방법을 써요. 백업 파일을 카톡 나에게 보내기나 메일로 옮기면 돼요.</p></li>
  </ol>

  <h2 id="g-note">6. 꼭 알아둘 점</h2>
  <div class="g-note"><ul>
    <li>기록은 <b>어플을 연 브라우저 안에만</b> 저장돼요. 서버로 보내지 않으므로 다른 사람이 볼 수 없어요.</li>
    <li>브라우저의 <b>사이트 데이터·쿠키를 지우면 기록도 사라져요.</b> 백업 파일을 꼭 받아 두세요.</li>
    <li><b>바로 열기</b>로 연 어플과 <b>내려받은 파일</b>은 저장 장소가 서로 달라요. 한쪽만 정해서 쓰세요.</li>
    <li><b>전체 초기화</b>는 모든 완등 기록과 날짜를 지워요. 누르기 전에 백업하세요.</li>
  </ul></div>

  <h2 id="g-faq">7. 자주 묻는 질문</h2>
  <dl class="g-faq">
    <dt>돈이 드나요? 회원가입이 필요한가요?</dt>
    <dd>둘 다 아니에요. 무료이고 가입 없이 바로 써요.</dd>
    <dt>블랙야크 공식 인증을 대신하나요?</dt>
    <dd>아니에요. 이 어플은 개인 기록용이에요. 완등 인증은 블랙야크 공식 앱(BAC)에서 따로 해야 해요.
        <a href="index.html#tab-auth">인증방법 보기 →</a></dd>
    <dt>산속에서 인터넷이 안 돼도 되나요?</dt>
    <dd>내려받은 파일은 인터넷 없이 열려요. 산행 중 기록은 정상에서 하지 않아도 되니, 내려와서 날짜와 함께 적어도 돼요.</dd>
    <dt>휴대폰을 바꾸면 기록이 없어지나요?</dt>
    <dd>기존 휴대폰에서 백업(내보내기)한 파일을 새 휴대폰에서 복구(불러오기)하면 그대로 옮겨져요.</dd>
  </dl>

  <div class="g-cta">
    <a href="index.html#tab-app">어플 바로 열기</a>
    <a class="outline" href="index.html#tab-list">100대 명산 목록 보기</a>
  </div>
</article>
"""
    return page(GUIDE_TITLE, body, 0, GUIDE_DESC, GUIDE_CSS, path='app-guide.html')


# ---------------------------------------------------------------- 사진 출처
def build_credits(mts, photos):
    """사진 저작자 표기 페이지.

    CC BY / CC BY-SA 와 공공누리는 저작자·출처 표시가 라이선스 조건이다.
    표시 위치는 자유이므로 첫 페이지 대신 이 페이지에 모으고 푸터에서 링크한다.
    """
    name = {m['slug']: m['name'] for m in mts}
    groups = {}
    for k, v in photos.items():
        label = ('직접 촬영' if v.get('own')
                 else v.get('provider') or '위키미디어 공용')
        groups.setdefault(label, []).append((k, v))

    order = ['위키미디어 공용', '한국관광공사 포토코리아', '한국관광공사 TourAPI', '직접 촬영']
    blocks = []
    for g in order + [x for x in groups if x not in order]:
        if g not in groups:
            continue
        rows = ''.join(
            f'<li><b>{e(name.get(k, "메인 이미지"))}</b> — {credit_line(v)}</li>'
            for k, v in sorted(groups[g], key=lambda kv: name.get(kv[0], '')))
        blocks.append(f'<div class="cred-group"><h2>{e(g)} '
                      f'<span>{len(groups[g])}장</span></h2>'
                      f'<ul class="credit-list">{rows}</ul></div>')

    lic = {}
    for v in photos.values():
        lic[v['license']] = lic.get(v['license'], 0) + 1
    summary = ' · '.join(f'{e(k)} {n}장' for k, n in sorted(lic.items(), key=lambda x: -x[1]))

    body = f"""
<section class="cred-head">
  <p class="crumb"><a href="index.html">← 첫 페이지로</a></p>
  <h1>사진 출처</h1>
  <p class="lead">이 사이트에 쓰인 사진 {len(photos)}장의 저작자와 라이선스입니다.
     직접 찍은 사진을 뺀 나머지는 모두 자유 라이선스(퍼블릭 도메인 · CC0 · CC BY ·
     CC BY-SA · 공공누리) 이미지이며, 저작자 표시는 라이선스 조건입니다.</p>
  <p class="cred-sum">{summary}</p>
</section>

<section class="credits">
  {''.join(blocks)}
</section>

<section class="cred-note">
  <h2>이용 조건</h2>
  <ul>
    <li><b>CC BY</b> — 저작자를 밝히면 자유롭게 쓸 수 있습니다.</li>
    <li><b>CC BY-SA</b> — 저작자를 밝히고, 2차 저작물은 같은 조건으로 공개해야 합니다.</li>
    <li><b>CC0 · 퍼블릭 도메인</b> — 표시 의무가 없습니다. 예의로 함께 적었습니다.</li>
    <li><b>공공누리 제1유형</b> — 출처를 밝히면 상업적 이용과 변형이 가능합니다.</li>
    <li><b>공공누리 제3유형</b> — 출처를 밝혀야 하고 변형은 할 수 없습니다.
        이 사이트에서는 웹 표시를 위한 크기 축소만 했습니다.</li>
  </ul>
  <p class="muted">사진에 대한 문의는 각 항목의 원본 링크를 참고하세요.</p>
</section>
"""
    return page(f"사진 출처 | {SITE}", body, 0,
                "블랙야크 100대 명산 기록에 쓰인 사진의 저작자와 라이선스 표기.")


# ---------------------------------------------------------------- 개별 산
def minimap(m, kmap):
    """해당 산 주변만 확대해 보여주는 SVG. viewBox만 옮기면 되므로 이미지 크롭이 필요 없다."""
    h = ZOOM_W * 0.8
    x0, y0 = m['x'] - ZOOM_W / 2, m['y'] - h / 2
    vb = f"{x0:.0f} {y0:.0f} {ZOOM_W} {h:.0f}"
    win = (x0, y0, x0 + ZOOM_W, y0 + h)          # 이 창에 걸치는 폴리곤만 그린다
    shapes = ''.join(f'<path d="{d}"/>' for d in kmap['paths'] if visible(d, win))
    provs, _ = provinces_svg(kmap, win=win)
    return (f'<svg class="kmap zoom" data-region="{e(m["region"])}" viewBox="{vb}" '
            f'width="{ZOOM_W}" height="{h:.0f}" role="img" '
            f'aria-label="{e(m["name"])} 위치"><g class="land">{shapes}</g>'
            f'<g class="provs">{provs}</g>'
            f'<circle class="here" cx="{m["x"]}" cy="{m["y"]}" r="8"/></svg>')


def section(title, inner):
    return f'<section class="blk"><h2>{e(title)}</h2>{inner}</section>' if inner else ''


def parking_html(rows, mt_name=''):
    """주차장 목록을 카드로 만든다.

    지도 링크는 '이름 검색'을 기본으로 한다. 좌표를 확신할 수 있는 곳에만
    길찾기를 덧붙인다 — 어림한 좌표로 길을 안내하면 엉뚱한 곳으로 보낸다."""
    if not rows:
        return ''
    out = []
    for p in rows:
        meta = ''.join(f'<span class="pk-chip">{e(p[k])}</span>'
                       for k in ('capacity', 'fee', 'hours') if p.get(k))
        # '백운산(광양)' 의 괄호는 목록을 구분하려고 붙인 것이라 지도 검색에는 방해가 된다
        base = mt_name.split('(')[0].strip()
        q = urllib.parse.quote(p.get('query') or f'{base} {p["name"]}'.strip())
        links = (f'<a href="https://map.kakao.com/link/search/{q}"'
                 f' target="_blank" rel="noopener">카카오맵</a>'
                 f'<a href="https://map.naver.com/p/search/{q}"'
                 f' target="_blank" rel="noopener">네이버지도</a>')
        if p.get('lat') and p.get('lon'):
            n = urllib.parse.quote(p['name'])
            links += (f'<a class="go" href="https://map.kakao.com/link/to/'
                      f'{n},{p["lat"]},{p["lon"]}" target="_blank" rel="noopener">길찾기</a>')
        out.append(
            f'<li class="pk"><b class="pk-name">{e(p["name"])}</b>'
            + (f'<span class="pk-addr">{e(p["addr"])}</span>' if p.get('addr') else '')
            + (f'<div class="pk-meta">{meta}</div>' if meta else '')
            + (f'<p class="pk-note">{e(p["note"])}</p>' if p.get('note') else '')
            + f'<div class="pk-go">{links}</div></li>')
    return ('<ul class="pk-list">' + ''.join(out) + '</ul>'
            '<p class="pk-warn">주차 요금과 면수는 자주 바뀌고 성수기에는 임시 주차장·셔틀이 운영되기도 합니다. 출발 전에 지도 앱이나 공원 사무소로 한 번 더 확인하세요.</p>')


def food_html(food, mt_name=''):
    """맛집 — 지역 향토음식 설명 + 들머리 주변 음식점.

    음식점은 한국관광공사에 등록된 곳이다. 맛집 순위가 아니라는 점을
    페이지에도 밝혀 둔다. 식당은 문을 닫는 일이 잦아서다."""
    if not food:
        return ''
    out = []
    if food.get('local'):
        out.append(f'<p class="fd-local">{e(food["local"])}</p>')

    rows = []
    for f in food.get('places', []):
        meta = ''.join(f'<span class="fd-chip">{e(f[k])}</span>'
                       for k in ('menu', 'hours', 'closed') if f.get(k))
        q = urllib.parse.quote(f.get('query') or f'{f["name"]} {f.get("addr", "").split()[0]}'.strip())
        dist = (f'<span class="fd-dist">들머리에서 {f["dist"]}km</span>'
                if f.get('dist') else '')
        rows.append(
            f'<li class="fd"><b class="fd-name">{e(f["name"])}</b>{dist}'
            + (f'<span class="fd-addr">{e(f["addr"])}</span>' if f.get('addr') else '')
            + (f'<div class="fd-meta">{meta}</div>' if meta else '')
            + (f'<p class="fd-note">{e(f["note"])}</p>' if f.get('note') else '')
            + f'<div class="fd-go">'
              f'<a href="https://map.kakao.com/link/search/{q}" target="_blank"'
              f' rel="noopener">카카오맵</a>'
              f'<a href="https://map.naver.com/p/search/{q}" target="_blank"'
              f' rel="noopener">네이버지도</a></div></li>')
    if rows:
        out.append('<ul class="fd-list">' + ''.join(rows) + '</ul>')
        out.append('<p class="fd-warn">한국관광공사에 등록된 음식점입니다. 맛집 순위가'
                   ' 아니며, 영업시간과 휴무일은 바뀔 수 있으니 먼 길이라면 미리'
                   ' 전화해 보세요.</p>')
    return ''.join(out)


def log_html(logs, mt_name=''):
    """직접 다녀온 등반기록. 최근 산행이 위로 온다.

    사진은 assets/photos/ 아래 경로로 적는다. 한 문단 묶음에 사진이 한 장이면
    크게, 여러 장이면 첫 장만 크게 두고 나머지는 두 칸 격자로 놓는다."""
    if not logs:
        return ''
    out = []
    for lg in sorted(logs, key=lambda x: x.get('date', ''), reverse=True):
        d = lg.get('date', '')
        chips = ''.join(f'<span class="lg-chip">{e(x)}</span>' for x in (
            d.replace('-', '.'), lg.get('start') and f'{lg["start"]} 출발', lg.get('weather')) if x)
        stats = ''.join(f'<div class="lg-stat"><b>{e(v)}</b><span>{e(k)}</span></div>'
                        for k, v in lg.get('stats', []))
        body = []
        for s in lg.get('sections', []):
            if s.get('heading'):
                body.append(f'<h3>{e(s["heading"])}</h3>')
            body += [f'<p>{e(p)}</p>' for p in s.get('paras', [])]
            phs = s.get('photos', [])
            def fig(p, cls='lg-fig'):
                alt = p.get('caption') or f'{mt_name} 산행 사진'
                cap = f'<figcaption>{e(p["caption"])}</figcaption>' if p.get('caption') else ''
                return (f'<figure class="{cls}"><img src="../{img("assets/photos/" + p["file"])}" '
                        f'alt="{e(alt)}" loading="lazy" decoding="async">{cap}</figure>')
            if phs:
                body.append(fig(phs[0]))
            if len(phs) > 1:
                body.append('<div class="lg-grid">' + ''.join(fig(p, 'lg-cell') for p in phs[1:]) + '</div>')
        tips = lg.get('tips') or []
        tips_html = ('<h3>다음에 갈 사람을 위한 팁</h3><ul class="tips">'
                     + ''.join(f'<li>{e(x)}</li>' for x in tips) + '</ul>') if tips else ''
        r = lg.get('rating')
        verdict = ''
        if r or lg.get('verdict'):
            stars = (f'<span class="lg-stars" aria-label="별점 {r}/5">{"★" * r}{"☆" * (5 - r)}</span>'
                     if r else '')
            verdict = f'<div class="lg-verdict">{stars}<p>{e(lg.get("verdict", ""))}</p></div>'
        out.append(
            f'<article class="lg"><header class="lg-head"><b class="lg-title">{e(lg.get("title", ""))}</b>'
            + (f'<p class="lg-sub">{e(lg["sub"])}</p>' if lg.get('sub') else '')
            + f'<div class="lg-chips">{chips}</div></header>'
            + (f'<div class="lg-stats">{stats}</div>' if stats else '')
            + ''.join(body) + tips_html + verdict + '</article>')
    return ''.join(out)


def build_mountain(m, prev, nxt, kmap, photos):
    c = m['content']
    ph = photos.get(m['slug'])
    cover = (f'<figure class="cover"><img src="../{img("assets/photos/" + ph["file"])}" '
             f'alt="{e(m["name"])} 사진" decoding="async">'
             f'<figcaption>사진 {credit_line(ph)}</figcaption></figure>') if ph else (
             f'<figure class="cover illus">{ridge_svg(m, vb="0 96 400 172")}'
             f'<figcaption>사진 준비 중 — 높이와 지역으로 그린 이미지입니다</figcaption></figure>')

    if not c:
        main = f"""<p class="todo-msg">아직 글이 준비되지 않은 산입니다. 코스·인증장소·교통 정보를 정리하는 대로 업데이트합니다.</p>"""
        desc = f"{m['name']} {m['height']} · {m['region']} — 블랙야크 100대 명산"
    else:
        intro = ''.join(f'<p>{e(p)}</p>' for p in c.get('intro', []))

        hl = c.get('highlights') or []
        hl_html = ('<ul class="hl">' + ''.join(f'<li>{e(x)}</li>' for x in hl) + '</ul>') if hl else ''

        rows = []
        for co in c.get('courses', []):
            rows.append(f"""<tr>
        <td><b>{e(co['name'])}</b><br><span class="path">{e(co['path'])}</span></td>
        <td>{e(co.get('distance', '-'))}</td><td>{e(co.get('time', '-'))}</td>
        <td><span class="lv lv-{e(co.get('level', '중'))}">{e(co.get('level', '중'))}</span></td>
      </tr>""")
        courses = ("""<div class="table-scroll"><table class="courses">
      <thead><tr><th>코스</th><th>거리</th><th>소요</th><th>난이도</th></tr></thead>
      <tbody>""" + ''.join(rows) + '</tbody></table></div>') if rows else ''

        ac = c.get('access', {})
        access = ''
        if ac:
            access = '<dl class="access">'
            if ac.get('car'):
                access += f'<dt>자가용</dt><dd>{e(ac["car"])}</dd>'
            if ac.get('transit'):
                access += f'<dt>대중교통</dt><dd>{e(ac["transit"])}</dd>'
            access += '</dl>'

        tips = c.get('tips') or []
        tips_html = ('<ul class="tips">' + ''.join(f'<li>{e(x)}</li>' for x in tips) + '</ul>') if tips else ''

        src = c.get('sources') or []
        src_html = ('<ul class="sources">' + ''.join(
            f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["title"])}</a></li>'
            for s in src) + '</ul>') if src else ''

        main = f"""<div class="lede">{intro}</div>
    {section('등반기록', log_html(c.get('log'), m['name']))}
    {section('이 산의 포인트', hl_html)}
    {section('등산 코스', courses)}
    {section('인증장소', f'<p>{e(c["cert"])}</p>' if c.get('cert') else '')}
    {section('가는 길', access)}
    {section('주차장', parking_html(c.get('parking'), m['name']))}
    {section('맛집', food_html(c.get('food'), m['name']))}
    {section('언제 가면 좋은가', f'<p>{e(c["season"])}</p>' if c.get('season') else '')}
    {section('알아두면 좋은 것', tips_html)}
    {section('참고한 곳', src_html)}"""
        desc = c['summary']

    nav = '<nav class="pager">'
    nav += (f'<a class="prev" href="{e(prev["slug"])}.html"><span>이전</span>{e(prev["name"])}</a>'
            if prev else '<span></span>')
    nav += (f'<a class="next" href="{e(nxt["slug"])}.html"><span>다음</span>{e(nxt["name"])}</a>'
            if nxt else '<span></span>')
    nav += '</nav>'

    updated = (c or {}).get('updated', '')
    body = f"""
<article class="post">
  <div class="post-head">
    <p class="crumb"><a href="../index.html">전체 목록</a> › {e(m['region'])}</p>
    <h1>{e(m['name'])}</h1>
    <p class="meta"><span class="badge">100대 명산 #{m['rank']}</span>
       <span>{e(m['height'])}</span><span>{e(m['region'])}</span>
       {f'<span class="upd">{e(updated)} 기준</span>' if updated else ''}</p>
    {f'<p class="summary">{e(c["summary"])}</p>' if c else ''}
  </div>

  {cover}

  <div class="post-body">
    <div class="main">{main}</div>
    <aside class="side">
      <div class="minimap">
        <div class="minimap-frame">{minimap(m, kmap)}</div>
        <p class="cap">북위 {m['lat']:.3f}° / 동경 {m['lon']:.3f}° (정상부 근사 좌표)</p>
      </div>
      <div class="fact">
        <dl>
          <dt>높이</dt><dd>{e(m['height'])}</dd>
          <dt>지역</dt><dd>{e(m['region'])}</dd>
          <dt>번호</dt><dd>{m['rank']} / 100</dd>
          <dt>좌표</dt><dd>{m['lat']:.3f}, {m['lon']:.3f}</dd>
        </dl>
      </div>
    </aside>
  </div>
  {nav}
</article>
"""
    share = f"assets/photos/{ph['file']}" if ph else 'assets/photos/hero.jpg'  # img() 는 page() 안에서
    return page(f"{m['name']} {m['height']} — 코스·난이도·인증장소 | {SITE}", body, 1, desc,
                image=share, path=f"mountain/{m['slug']}.html")


# ---------------------------------------------------------------- CSS / JS
CSS = r"""
:root{
  --green:#1f7a4c; --green-2:#2fa76a; --green-soft:#eaf6ef;
  --ink:#161d26; --sub:#5f6b7a; --line:#e6e9ee; --bg:#fbfaf7; --card:#fff;
  --accent:#b4530a; --max:1120px;
}
*{box-sizing:border-box}
[hidden]{display:none!important}   /* display 를 지정한 요소도 확실히 숨긴다 */
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Pretendard","Apple SD Gothic Neo","Malgun Gothic",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16px;line-height:1.75;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
h1,h2,h3{line-height:1.3;letter-spacing:-.02em;margin:0}
img{max-width:100%}

/* 헤더 */
header.site{position:sticky;top:0;z-index:50;background:rgba(251,250,247,.9);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line);
  display:flex;align-items:center;justify-content:space-between;gap:16px;
  padding:12px 24px}
.brand{display:flex;align-items:center;gap:10px}
/* 뚫린 '100' 으로 이 남색이 비친다. 사진 속 하늘색과 같은 계열이라
   밝은 설벽 위에서도 숫자가 또렷하게 읽힌다. */
.mark{width:34px;height:34px;border-radius:9px;overflow:hidden;display:block;
  flex:0 0 auto;background:#14243f}
.mark svg{display:block;width:100%;height:100%}
/* 마스크의 검은 글자가 사진을 뚫어 위 배경색이 비치게 한다 */
.mark mask text{fill:#000;font:800 15px/1 system-ui,-apple-system,"Segoe UI",sans-serif;
  letter-spacing:-.04em}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);
  white-space:nowrap}
.brand-text{display:flex;flex-direction:column;line-height:1.2}
.brand-text b{font-size:15px}
.brand-text em{font-style:normal;font-size:11.5px;color:var(--sub)}
header.site nav{display:flex;gap:20px;font-size:14px;color:var(--sub)}
header.site nav a:hover{color:var(--green)}

/* 메인 비주얼 — 화면 전체 폭 사진 */
.vhero,.statbar{max-width:none;margin:0;padding:0}
.vhero{position:relative;min-height:min(78vh,660px);display:flex;align-items:flex-end;
  overflow:hidden;background:#20262e}
.vhero-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  object-position:center 55%;display:block}
.vhero-shade{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(16,20,26,.45) 0%,rgba(16,20,26,.15) 38%,rgba(16,20,26,.82) 100%)}
.vhero-inner{position:relative;width:100%;max-width:var(--max);margin:0 auto;
  padding:0 24px 76px;color:#fff}
.vhero .eyebrow{margin:0 0 16px;font-size:12px;letter-spacing:.2em;font-weight:700;
  color:#ffd9a8}
.vhero h1{font-size:clamp(34px,6vw,64px);font-weight:800;
  text-shadow:0 2px 24px rgba(0,0,0,.45)}
.vhero .lead{margin:18px 0 0;font-size:clamp(15px,1.6vw,18.5px);color:rgba(255,255,255,.9);
  max-width:34em;text-shadow:0 1px 12px rgba(0,0,0,.4)}
.btn-hero{padding:13px 24px;border-radius:999px;font-size:14.5px;font-weight:650;
  transition:.15s;border:1px solid transparent}
.vhero-credit{position:absolute;right:14px;bottom:8px;margin:0;z-index:2;max-width:calc(100% - 28px);
  font-size:10.5px;line-height:1.5;text-align:right;color:rgba(255,255,255,.62)}
.vhero-credit a{text-decoration:underline;text-underline-offset:2px}
.vhero-credit a:hover{color:#fff}
.eyebrow{margin:0 0 14px;font-size:12px;letter-spacing:.18em;color:var(--accent);font-weight:700}

/* 통계 바 */
.statbar{padding:30px 24px;border-bottom:1px solid var(--line);background:#fff;max-width:none}
.stats{display:flex;flex-wrap:wrap;gap:44px;max-width:var(--max);margin:0 auto}
.stats div{display:flex;flex-direction:column}
.stats b{font-size:28px;font-weight:800;letter-spacing:-.03em}
.stats span{font-size:12.5px;color:var(--sub)}


/* 첫 페이지 메뉴 */
.menu{max-width:var(--max);margin:0 auto;padding:44px 24px 8px;
  display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
.menu-card{position:relative;display:block;text-align:left;overflow:hidden;
  min-height:172px;padding:0;border:1px solid var(--line);border-radius:16px;
  background:#243040;cursor:pointer;font-family:inherit;transition:.18s}
.menu-card:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(20,40,30,.16)}
.mc-bg{position:absolute;inset:0;display:block}
.mc-bg img{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .5s ease}
.menu-card:hover .mc-bg img{transform:scale(1.07)}
.mc-bg::after{content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(14,20,28,.18) 0%,rgba(14,20,28,.62) 55%,rgba(14,20,28,.86) 100%)}
.mc-txt{position:relative;display:flex;flex-direction:column;gap:3px;
  height:100%;justify-content:flex-end;padding:16px 15px 16px}
.mc-txt i{font-style:normal;font-size:11px;font-weight:800;letter-spacing:.12em;
  color:#ffd9a8}
.mc-txt b{font-size:16px;font-weight:750;letter-spacing:-.03em;color:#fff;
  text-shadow:0 1px 10px rgba(0,0,0,.4)}
.mc-txt em{font-style:normal;font-size:12px;line-height:1.45;color:rgba(255,255,255,.82)}
.menu-card::after{content:"";position:absolute;left:0;right:0;bottom:0;height:4px;
  background:transparent;transition:background .16s}
.menu-card.active{border-color:var(--green);box-shadow:0 0 0 2px rgba(31,122,76,.28)}
.menu-card.active::after{background:var(--green-2)}
.menu-card.art{background:linear-gradient(160deg,#2f3d4f,#1b2530)}
.menu-card.art .mc-bg::after{
  background:linear-gradient(180deg,rgba(14,20,28,.05) 0%,rgba(14,20,28,.55) 58%,rgba(14,20,28,.9) 100%)}
.mc-svg{position:absolute;right:-6%;top:-8%;height:116%;width:auto;display:block;
  opacity:.95}
.mm-land path{fill:rgba(255,255,255,.14);stroke:rgba(255,255,255,.45);stroke-width:5;
  stroke-linejoin:round}
.mm-dot circle{fill:#7fd6a4;opacity:.9}
.mc-svg rect{opacity:.9}
.sw-서울{fill:#dbe3f2}.sw-인천{fill:#e9eff5}.sw-경기{fill:#e0eaf7}.sw-강원{fill:#dfeee4}
.sw-충북{fill:#f5f0da}.sw-충남{fill:#f8e8de}.sw-경북{fill:#eae5f3}.sw-경남{fill:#dcedf1}
.sw-전북{fill:#f4ebdf}.sw-전남{fill:#e0f0e8}.sw-지리산{fill:#e6e0f0}.sw-제주도{fill:#f1e6ef}
.ph-body{fill:rgba(255,255,255,.14);stroke:rgba(255,255,255,.55);stroke-width:3}
.ph-scr{fill:rgba(255,255,255,.1)}
.ph-btn{fill:rgba(255,255,255,.5)}
.ph-dl{fill:none;stroke:#7fd6a4;stroke-width:5;stroke-linecap:round;stroke-linejoin:round}

.tabpanel[hidden]{display:none}
.chips-map{margin:0 0 18px}

/* 인증방법 */
.steps{counter-reset:step;list-style:none;margin:24px 0 0;padding:0;
  display:flex;flex-direction:column;gap:12px}
.steps li{counter-increment:step;position:relative;background:var(--card);
  border:1px solid var(--line);border-radius:14px;padding:18px 20px 18px 64px}
.steps li::before{content:counter(step);position:absolute;left:18px;top:17px;
  width:30px;height:30px;border-radius:50%;background:var(--green);color:#fff;
  font-size:14px;font-weight:750;display:grid;place-items:center}
.steps b{display:block;font-size:16.5px;font-weight:750;letter-spacing:-.02em;margin-bottom:5px}
.steps p{margin:0;font-size:14px;color:var(--sub);line-height:1.72}
.steps em{font-style:normal;color:var(--green);font-weight:650}
.auth-note{margin-top:30px;background:#fdf9f0;border:1px solid #f0e2c8;
  border-radius:14px;padding:22px 24px}
.auth-note h3{font-size:15.5px;font-weight:750;margin-bottom:12px}
.auth-note ul{margin:0;padding-left:20px;font-size:14px;line-height:1.85;color:#6b5c3d}
.auth-note b{color:#4a3f26;font-weight:700}
.auth-note .muted{margin:16px 0 0;font-size:12.5px;color:#8a7a58;text-align:left}
.auth-note a{color:var(--green);text-decoration:underline;text-underline-offset:3px}

/* 어플 안내 */
.app-box{background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:30px;max-width:760px;margin:0 auto;text-align:left}
.app-cta{display:flex;align-items:center;gap:14px;flex-wrap:wrap;justify-content:center}
.app-cta .btn-hero{text-decoration:none;display:inline-block;background:var(--green);color:#fff;border-color:var(--green)}
.app-cta .btn-hero:hover{background:#188044;border-color:#188044;color:#fff}
.app-note{font-size:13px;color:var(--sub);text-align:center;margin:14px 0 0;line-height:1.7}
.app-cta .btn-hero.outline{background:transparent;color:var(--green);
  border-color:var(--green)}
.app-cta .btn-hero.outline:hover{background:rgba(46,160,102,.1);color:var(--green)}
.app-box code{background:#f1f3f2;padding:1px 6px;border-radius:5px;font-size:13px}
.app-install p{margin:0 0 9px}
.app-feat{list-style:none;padding:0;margin:26px 0 0;display:grid;gap:11px}
.app-feat li{font-size:14.5px;line-height:1.7;padding-left:20px;position:relative}
.app-feat li::before{content:"";position:absolute;left:2px;top:9px;width:7px;height:7px;
  border-radius:50%;background:var(--green)}
.app-feat b{display:block;font-size:13px;color:var(--green)}
.app-install{margin-top:26px;padding-top:22px;border-top:1px solid var(--line)}
.app-install h3{margin:0 0 8px;font-size:15px}
.app-install p{margin:0;font-size:14px;line-height:1.75;color:var(--sub)}
.app-warn{margin:22px 0 0;padding:12px 14px;border-radius:10px;background:#fdf3e2;
  color:#8a5a0c;font-size:13px;line-height:1.65}
@media(max-width:560px){.app-box{padding:22px 18px}}

@media (max-width:1180px){
  .menu{grid-template-columns:repeat(3,1fr);gap:12px}
  .menu-card{min-height:164px}
}
@media (max-width:760px){
  .menu{grid-template-columns:repeat(2,1fr);padding-top:32px}
}
@media (max-width:520px){
  .menu{grid-template-columns:1fr}
}

/* 사진 카드 */
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;margin-top:22px}
.pcard{position:relative;display:flex;flex-direction:column;background:var(--card);
  border:1px solid var(--line);border-radius:16px;overflow:hidden;transition:.18s}
.pcard:hover{transform:translateY(-3px);border-color:var(--green-2);
  box-shadow:0 14px 34px rgba(20,40,30,.13)}
.pcard-img{display:block;aspect-ratio:4/3;overflow:hidden;background:#e8ece9}
.pcard-img img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s ease}
.pcard:hover .pcard-img img{transform:scale(1.06)}
.pcard-body{display:flex;flex-direction:column;gap:6px;padding:16px 18px 18px}
.pc-top{display:flex;align-items:center;gap:8px;font-size:11.5px}
.pc-top i{font-style:normal;background:var(--green-soft);color:var(--green);
  padding:3px 9px;border-radius:999px;font-weight:650}
.pc-top b{color:var(--sub);font-weight:600}
.pcard-body strong{font-size:19px;font-weight:750;letter-spacing:-.02em}
.pc-sum{font-size:13.5px;color:var(--sub);line-height:1.6;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pc-go{margin-top:4px;font-size:13px;font-weight:650;color:var(--green)}
.pcard-credit{position:absolute;left:10px;top:10px;font-size:10px;color:#fff;
  background:rgba(0,0,0,.42);padding:3px 8px;border-radius:999px;opacity:0;transition:opacity .18s}
.pcard:hover .pcard-credit{opacity:1}
.more-link{margin:26px 0 0;font-size:14.5px;font-weight:650}
.more-link a{color:var(--green)}
.more-link a:hover{text-decoration:underline;text-underline-offset:3px}


/* 글 상단 커버 사진 */
.cover{margin:26px 0 0;overflow:hidden}
.cover img{width:100%;max-height:420px;object-fit:cover;border-radius:14px;display:block}
.cover figcaption{font-size:11.5px;color:var(--sub);margin:8px 2px 0;text-align:right}
.cover.illus svg{width:100%;height:300px;object-fit:cover;border-radius:14px;display:block}
.cover figcaption a{color:var(--sub);text-decoration:underline;text-underline-offset:2px}
.cover figcaption a:hover{color:var(--green)}


/* 사진 출처 페이지 */
.cred-head{max-width:var(--max);margin:0 auto;padding:48px 24px 10px}
.cred-head h1{font-size:clamp(28px,4vw,40px);font-weight:800}
.cred-head .lead{margin:14px 0 0;font-size:15.5px;color:var(--sub);max-width:46em;line-height:1.75}
.cred-sum{margin:18px 0 0;font-size:12.5px;color:var(--sub);background:#fff;
  border:1px solid var(--line);border-radius:10px;padding:10px 14px;display:inline-block}
.cred-group{margin-bottom:34px}
.cred-group h2{font-size:17px;font-weight:750;padding-bottom:8px;
  border-bottom:2px solid var(--green-soft);margin-bottom:14px}
.cred-group h2 span{font-size:12.5px;color:var(--sub);font-weight:500;margin-left:8px}
.cred-note{border-top:1px solid var(--line)}
.cred-note h2{font-size:17px;font-weight:750;margin-bottom:14px}
.cred-note ul{margin:0;padding-left:20px;font-size:14px;line-height:1.9;color:var(--sub)}
.cred-note b{color:var(--ink);font-weight:650}
.cred-note .muted{margin-top:16px;text-align:left}
.foot-link{color:var(--green);text-decoration:underline;text-underline-offset:3px;font-weight:600}
.foot-link:hover{color:var(--ink)}

.credits{padding-top:26px}
.credit-list{margin:0;padding-left:18px;font-size:13px;color:var(--sub);line-height:1.9}
.credit-list b{color:var(--ink);font-weight:650}
.credit-list a{color:var(--green);text-decoration:underline;text-underline-offset:2px}

section{max-width:var(--max);margin:0 auto;padding:56px 24px}
section h2{font-size:24px;font-weight:750}
.sub{margin:8px 0 22px;color:var(--sub);font-size:14.5px}

/* 지도 (Natural Earth 경계 데이터 기반 인라인 SVG) */
.map-box{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px}
.kmap{display:block;margin:0 auto;height:min(88vh,1040px);width:auto;max-width:100%}
.kmap.zoom{height:auto;width:100%}

/* 바탕 국토 — 시도 경계 사이 미세한 틈을 메우는 밑그림 */
.kmap .land path{fill:#e9ece9;stroke:none}

/* 시도별 면 */
.kmap .prov path{stroke:#fff;stroke-width:1.6;stroke-linejoin:round;
  vector-effect:non-scaling-stroke;transition:opacity .18s ease}
.kmap .prov[data-region="서울"] path{fill:#dbe3f2}
.kmap .prov[data-region="인천"] path{fill:#e9f0f6}
.kmap .prov[data-region="경기"] path{fill:#e0eaf7}
.kmap .prov[data-region="강원"] path{fill:#dfeee4}
.kmap .prov[data-region="충북"] path{fill:#f5f0da}
.kmap .prov[data-region="충남"] path{fill:#f8e8de}
.kmap .prov[data-region="경북"] path{fill:#eae5f3}
.kmap .prov[data-region="경남"] path{fill:#dcedf1}
.kmap .prov[data-region="전북"] path{fill:#f4ebdf}
.kmap .prov[data-region="전남"] path{fill:#e0f0e8}
.kmap .prov[data-region="제주도"] path{fill:#f1e6ef}

/* 시도 이름 */
.kmap .plabel{font-family:inherit;font-size:26px;font-weight:700;fill:#6f7a86;
  text-anchor:middle;dominant-baseline:middle;pointer-events:none;
  paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round;
  transition:opacity .18s ease}

/* 마커 */
.kmap .pins circle{fill:#1d7a4c;stroke:#fff;stroke-width:3.5;cursor:pointer;
  transition:r .12s ease,fill .12s ease,opacity .18s ease}
.kmap .pins a:hover circle{r:21;fill:var(--accent)}
.kmap .pins a:focus-visible circle{r:21;outline:none;fill:var(--accent)}

/* 지역 버튼을 누르면 그 시도만 남기고 나머지는 흐리게 */
.kmap.filtered .prov:not(.on) path{opacity:.22}
.kmap.filtered .plabel:not(.on){opacity:.2}
.kmap.filtered .pins a:not(.on) circle{opacity:.15}
.kmap.filtered .prov.on path{stroke:#8a949e;stroke-width:2.2;filter:saturate(1.8)}
.kmap.filtered .plabel.on{fill:var(--ink)}

.kmap.zoom .prov path{stroke-width:1.4}
.kmap.zoom .prov.on path{filter:saturate(1.9);stroke:#96a0a8;stroke-width:1.8}
.kmap .here{fill:var(--accent);stroke:#fff;stroke-width:3}
.attrib{font-size:11.5px;color:var(--sub);text-align:right;margin:10px 2px 0}

/* 검색 / 칩 */
.controls{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin:22px 0 10px}
#q{flex:1;min-width:240px;padding:11px 15px;border:1px solid var(--line);border-radius:10px;
  font-size:14.5px;background:#fff;font-family:inherit}
#q:focus{outline:2px solid var(--green-2);outline-offset:-1px}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 13px;
  font-size:13px;cursor:pointer;font-family:inherit;color:var(--sub);transition:.13s}
.chip i{font-style:normal;opacity:.5;font-size:11.5px}
.chip:hover{border-color:var(--green-2);color:var(--green)}
.chip.active{background:var(--green);border-color:var(--green);color:#fff}
.chip.active i{opacity:.75}
.count{font-size:13px;color:var(--sub);margin:6px 0 18px}

/* 카드 */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;
  display:flex;flex-direction:column;overflow:hidden;transition:.15s}
.card:hover{border-color:var(--green-2);transform:translateY(-2px);box-shadow:0 8px 24px rgba(20,40,30,.09)}
.card.todo{opacity:.62}
.card-thumb{position:relative;display:block;aspect-ratio:4/3;overflow:hidden;background:#e8ece9}
.pcard-img{position:relative}
.done-badge{position:absolute;top:10px;left:10px;z-index:2;background:var(--green);color:#fff;font-size:12px;font-weight:700;font-style:normal;line-height:1;padding:6px 10px;border-radius:999px;box-shadow:0 2px 8px rgba(0,0,0,.25);letter-spacing:.2px;pointer-events:none}
.card-thumb img,.card-thumb svg{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .45s ease}
.card:hover .card-thumb img{transform:scale(1.05)}
.card-body{display:flex;flex-direction:column;gap:4px;padding:14px 16px 16px}
.card-top{display:flex;justify-content:space-between;align-items:center}
.rank{font-size:11.5px;font-weight:700;color:var(--accent);font-style:normal}
.tag{font-size:11px;color:var(--sub);background:var(--green-soft);padding:2px 8px;
  border-radius:999px;font-style:normal}
.card-body strong{font-size:17.5px;font-weight:750;margin-top:3px;letter-spacing:-.02em}
.card .h{font-size:13px;color:var(--green);font-weight:650}
.card .s{margin-top:4px;font-size:13.5px;color:var(--sub);line-height:1.6;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.empty{text-align:center;color:var(--sub);padding:40px 0}

/* 지역별 */
.regions{border-top:1px solid var(--line)}
.region-block{margin-bottom:26px}
.region-block h3{font-size:15px;font-weight:700;margin-bottom:10px}
.region-pick{font:inherit;font-size:15px;font-weight:700;color:inherit;background:none;
  border:none;padding:0;cursor:pointer;border-bottom:2px solid transparent;transition:.14s}
.region-pick:hover{color:var(--green);border-bottom-color:var(--green-2)}
.region-pick span{color:var(--sub);font-weight:500;font-size:12.5px;margin-left:6px}
.pills{display:flex;flex-wrap:wrap;gap:7px}
.pills a{border:1px solid var(--line);background:#fff;border-radius:8px;padding:6px 11px;font-size:13.5px}
.pills a em{font-style:normal;color:var(--sub);font-size:12px;margin-left:5px}
.pills a:hover{border-color:var(--green-2);color:var(--green)}

/* 글 */
.post{max-width:var(--max);margin:0 auto;padding:44px 24px 72px}
.crumb{font-size:13px;color:var(--sub);margin:0 0 14px}
.crumb a:hover{color:var(--green)}
.post h1{font-size:clamp(30px,4.4vw,44px);font-weight:800}
.meta{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:14px 0 0;font-size:13.5px;color:var(--sub)}
.badge{background:var(--green);color:#fff;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:650}
.upd{margin-left:auto;font-size:12.5px}
.summary{margin:20px 0 0;font-size:18px;line-height:1.7;color:var(--ink);font-weight:550;max-width:44em}
.post-head{padding-bottom:28px;border-bottom:1px solid var(--line)}
.post-body{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,300px);gap:48px;margin-top:34px;align-items:start}
.main{min-width:0;overflow-wrap:break-word}
.main .lede p{font-size:16.5px;margin:0 0 16px}
.blk{max-width:none;margin:36px 0 0;padding:0}
.blk h2{font-size:19px;font-weight:750;padding-bottom:9px;border-bottom:2px solid var(--green-soft);margin-bottom:16px}
.hl{margin:0;padding-left:0;list-style:none}
.hl li{position:relative;padding-left:22px;margin-bottom:9px}
.hl li::before{content:"";position:absolute;left:4px;top:11px;width:7px;height:7px;border-radius:50%;background:var(--green-2)}
.tips{padding-left:20px;margin:0}
.tips li{margin-bottom:8px}
.lg{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 20px 22px}
.lg+.lg{margin-top:18px}
.lg-title{display:block;font-size:18px;font-weight:750}
.lg-sub{color:var(--sub);margin:4px 0 0;font-size:14px}
.lg-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.lg-chip{font-size:12.5px;background:var(--green-soft);color:var(--green);border-radius:999px;padding:3px 10px;font-weight:600}
.lg-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0 4px}
.lg-stat{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px 6px;text-align:center}
.lg-stat b{display:block;font-size:16px;color:var(--green)}
.lg-stat span{font-size:12px;color:var(--sub)}
.lg h3{font-size:16px;font-weight:750;margin:22px 0 8px}
.lg figure{margin:14px 0}
.lg img{width:100%;border-radius:10px;display:block}
.lg-fig img{width:auto;max-width:100%;max-height:560px;margin:0 auto}
.lg figcaption{font-size:12.5px;color:var(--sub);margin-top:6px;text-align:center}
.lg-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.lg-grid figure{margin:0}
.lg-grid figure:only-child{grid-column:1/-1}
.lg-grid figure:only-child img{aspect-ratio:auto;width:auto;max-width:100%;max-height:560px;margin:0 auto}
.lg-grid img{aspect-ratio:4/3;object-fit:cover}
.lg-verdict{margin-top:20px;padding-top:16px;border-top:1px dashed var(--line);text-align:center}
.lg-stars{color:#d9a441;font-size:20px;letter-spacing:2px}
.lg-verdict p{margin:6px 0 0}
@media(max-width:560px){.lg{padding:16px}.lg-stats{grid-template-columns:repeat(2,1fr)}.lg-grid{grid-template-columns:1fr}}
.notice{background:#fdf6e8;border:1px solid #f0dfb8;border-radius:10px;padding:11px 15px;font-size:13.5px;color:#7a5a12;margin:0 0 22px}
.todo-msg{color:var(--sub)}

.table-scroll{overflow-x:auto}
table.courses{width:100%;border-collapse:collapse;font-size:14px;min-width:460px}
table.courses th{text-align:left;font-size:12px;color:var(--sub);font-weight:650;
  padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
table.courses td{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}
table.courses .path{font-size:12.5px;color:var(--sub);line-height:1.5}
.lv{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:650;white-space:nowrap}
.lv-하{background:#e7f4ea;color:#1f7a4c}
.lv-중{background:#fdf3e2;color:#a4680d}
.lv-상{background:#fbeaea;color:#b23b3b}

dl.access{margin:0;display:grid;grid-template-columns:64px 1fr;gap:10px 14px;font-size:14.5px}
dl.access dt{font-size:12.5px;color:var(--sub);font-weight:650;padding-top:2px}
dl.access dd{margin:0}
.pk-list{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.pk{border:1px solid var(--line);border-radius:12px;padding:13px 15px;background:var(--card)}
.pk-name{display:block;font-size:15px;font-weight:700}
.pk-addr{display:block;font-size:13px;color:var(--sub);margin-top:3px}
.pk-meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
.pk-chip{font-size:12.5px;padding:3px 9px;border-radius:999px;
  background:rgba(46,160,102,.11);color:var(--green);font-weight:640}
.pk-note{margin:9px 0 0;font-size:13.5px;line-height:1.65}
.pk-go{display:flex;gap:8px;margin-top:11px}
.pk-go a{font-size:12.5px;font-weight:640;padding:5px 11px;border-radius:8px;
  border:1px solid var(--line);color:var(--sub);text-decoration:none}
.pk-go a:hover{border-color:var(--green);color:var(--green)}
.fd-local{margin:0 0 16px;font-size:14.5px;line-height:1.8}
.fd-list{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.fd{border:1px solid var(--line);border-radius:12px;padding:13px 15px;background:var(--card)}
.fd-name{font-size:15px;font-weight:700;margin-right:8px}
.fd-dist{font-size:12px;color:var(--sub)}
.fd-addr{display:block;font-size:13px;color:var(--sub);margin-top:3px}
.fd-meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
.fd-chip{font-size:12.5px;padding:3px 9px;border-radius:999px;
  background:#fbf0e4;color:#96601a;font-weight:640}
.fd-note{margin:9px 0 0;font-size:13.5px;line-height:1.65}
.fd-go{display:flex;gap:8px;margin-top:11px}
.fd-go a{font-size:12.5px;font-weight:640;padding:5px 11px;border-radius:8px;
  border:1px solid var(--line);color:var(--sub);text-decoration:none}
.fd-go a:hover{border-color:var(--green);color:var(--green)}
.fd-warn{margin:12px 0 0;font-size:12.5px;color:var(--sub);line-height:1.6}
.pk-warn{margin:12px 0 0;font-size:12.5px;color:var(--sub);line-height:1.6}
.pk-go a.go{border-color:var(--green);color:var(--green);background:rgba(46,160,102,.08)}
.sources{padding-left:20px;margin:0;font-size:13.5px}
.sources a{color:var(--green);text-decoration:underline;text-underline-offset:3px}

/* 사이드 */
.side{position:sticky;top:78px;display:flex;flex-direction:column;gap:16px;min-width:0}
.minimap{min-width:0}
.minimap-frame{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:12px;
  background:#fff;width:100%;padding:10px}
.minimap-frame .kmap{height:auto}
.cap{font-size:12px;color:var(--sub);margin:7px 2px 0}
.fact{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.fact dl{margin:0;display:grid;grid-template-columns:44px 1fr;gap:9px 12px;font-size:13.5px}
.fact dt{color:var(--sub);font-size:12.5px;padding-top:1px}
.fact dd{margin:0;font-weight:600}

.pager{display:flex;justify-content:space-between;gap:14px;margin-top:56px;padding-top:24px;border-top:1px solid var(--line)}
.pager a{max-width:46%;font-size:15px;font-weight:650}
.pager a span{display:block;font-size:11.5px;color:var(--sub);font-weight:500;margin-bottom:2px}
.pager .next{text-align:right}
.pager a:hover{color:var(--green)}

footer.site{border-top:1px solid var(--line);margin-top:40px;padding:32px 24px 56px;
  font-size:13px;color:var(--sub);text-align:center}
footer.site p{margin:0 0 6px}
.muted{font-size:12px;opacity:.8;max-width:52em;margin:0 auto}
/* footer.site p 가 .muted 보다 우선해서 margin:0 auto 를 덮어쓴다.
   그래서 글자만 가운데고 상자는 왼쪽에 붙어 있었다. */
footer.site .muted{margin:0 auto;text-align:center}

@media (max-width:700px){
  .vhero-credit .c-title{display:none}
  .cover figcaption .c-title{display:none}
}
@media (max-width:900px){
  .vhero{min-height:min(70vh,520px)}
  .vhero-inner{padding-bottom:56px}
  .stats{gap:26px}
  .pgrid{grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
  .post-body{grid-template-columns:minmax(0,1fr);gap:32px}
  .side{position:static;flex-direction:row;flex-wrap:wrap}
  .minimap{flex:1 1 260px}
  .fact{flex:1;min-width:200px}
  /* 좁은 화면에서는 메뉴를 숨기지 않고 가로로 넘기는 띠로 바꾼다.
     예전에는 통째로 감춰서 방명록 같은 곳에 갈 길이 푸터밖에 없었다. */
  header.site{flex-wrap:wrap;gap:8px 16px;padding:10px 16px}
  header.site nav{display:flex;order:3;width:100%;gap:0;font-size:13px;
    overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;
    margin:0 -16px;padding:2px 16px 0}
  header.site nav::-webkit-scrollbar{display:none}
  header.site nav a{flex:0 0 auto;padding:6px 11px;border-radius:999px;
    white-space:nowrap}
  header.site nav a:first-child{padding-left:0}
  /* 오른쪽 끝을 흐리게 해서 '더 있다'는 걸 알린다 */
  header.site nav{-webkit-mask-image:linear-gradient(to right,#000 88%,transparent);
    mask-image:linear-gradient(to right,#000 88%,transparent)}
  header.site nav.at-end{-webkit-mask-image:none;mask-image:none}
  .stats{gap:24px}
}
"""

JS = r"""
(function () {
  // 개별 산 페이지 미니맵: 그 산이 속한 시도를 강조한다
  document.querySelectorAll('.kmap.zoom').forEach(function (svg) {
    var r = svg.dataset.region;
    svg.querySelectorAll('.prov').forEach(function (g) {
      if (g.dataset.region === r) g.classList.add('on');
    });
  });
})();

(function () {
  // 좁은 화면의 상단 메뉴 띠 — 끝까지 넘기면 오른쪽 흐림을 없앤다
  var nav = document.querySelector('header.site nav');
  if (nav) {
    var mark = function () {
      var end = nav.scrollLeft + nav.clientWidth >= nav.scrollWidth - 2;
      nav.classList.toggle('at-end', end);
    };
    nav.addEventListener('scroll', mark, { passive: true });
    window.addEventListener('resize', mark);
    mark();
  }
})();

(function () {
  // 첫 페이지 4개 메뉴 — 누르면 해당 내용만 보여준다
  var menu = document.getElementById('menu');
  if (!menu) return;
  var cards = Array.prototype.slice.call(menu.querySelectorAll('.menu-card'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.tabpanel'));

  function show(id, scroll) {
    if (!document.getElementById(id)) id = 'tab-list';
    panels.forEach(function (p) { p.hidden = p.id !== id; });
    cards.forEach(function (c) { c.classList.toggle('active', c.dataset.tab === id); });
    if (history.replaceState) history.replaceState(null, '', '#' + id);
    if (scroll) {
      // 넓은 화면에서는 메뉴가 한 줄이라 메뉴 위로 가면 내용까지 함께 보인다.
      // 좁은 화면에서는 카드가 세로로 쌓여 메뉴만으로 한 화면을 넘기므로,
      // 그때는 고른 내용으로 바로 내려간다.
      var panel = document.getElementById(id);
      var tall = menu.getBoundingClientRect().height > window.innerHeight * 0.55;
      var target = (tall && panel) ? panel : menu;
      var hdr = document.querySelector('header.site');
      var off = (hdr ? hdr.getBoundingClientRect().height : 60) + 8;
      var top = target.getBoundingClientRect().top + window.pageYOffset - off;
      window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    }
  }

  cards.forEach(function (c) {
    c.addEventListener('click', function () { show(c.dataset.tab, true); });
  });
  window.showTab = show;          // '지역별로 한눈에'에서 목록 탭으로 넘어갈 때 쓴다
  // 다른 페이지에서 #tab-map 처럼 들어온 경우도 받아준다
  window.addEventListener('hashchange', function () {
    show(location.hash.slice(1), true);
  });
  show(location.hash.slice(1) || 'tab-list', false);
})();

(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var countEl = document.getElementById('count');
  var emptyEl = document.getElementById('empty');
  var region = '전체';

  function apply() {
    var term = q.value.trim().toLowerCase();
    var n = 0;
    cards.forEach(function (c) {
      var okR = region === '전체' || c.dataset.region === region;
      var okQ = !term || c.dataset.name.toLowerCase().indexOf(term) !== -1;
      var show = okR && okQ;
      c.hidden = !show;
      if (show) n++;
    });
    countEl.textContent = n + '개 표시 중' + (region === '전체' ? '' : ' · ' + region);
    emptyEl.hidden = n !== 0;
  }

  // 지역 버튼 선택을 지도에도 반영한다
  var kmap = document.getElementById('kmap');
  function paintMap() {
    if (!kmap) return;
    var all = region === '전체';
    kmap.classList.toggle('filtered', !all);
    ['.prov', '.plabel', '.pins a'].forEach(function (sel) {
      kmap.querySelectorAll(sel).forEach(function (el) {
        el.classList.toggle('on', all || el.dataset.region === region);
      });
    });
  }

  function pick(r) {
    region = r;
    chips.forEach(function (x) {
      x.classList.toggle('active', x.dataset.region === region);
    });
    apply();
    paintMap();
  }

  // '지역별로 한눈에'에서 지역 이름을 누르면 그 지역만 걸러 목록 탭으로 넘어간다
  document.querySelectorAll('.region-pick').forEach(function (b) {
    b.addEventListener('click', function () {
      pick(b.dataset.region);
      if (window.showTab) window.showTab('tab-list', true);
    });
  });

  q.addEventListener('input', apply);
  chips.forEach(function (ch) {
    // 목록 탭과 지도 탭에 같은 칩이 한 벌씩 있으므로 pick() 이 둘 다 맞춰준다
    ch.addEventListener('click', function () { pick(ch.dataset.region); });
  });
  apply();
  paintMap();
})();
"""


# ---------------------------------------------------------------- 실행
def main():
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import _guestbook, _appcount, _appshot, _visits
    mts = load()
    kmap = load_map()
    photos = load_photos()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT, ignore_errors=True)  # 로컬 서버가 폴더를 잡고 있어도 진행
    os.makedirs(os.path.join(OUT, 'mountain'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)

    def copy_images():
        """이미지를 내용 해시가 붙은 이름으로 싣고, 원래 이름으로도 남긴다.

        이름이 고정이면 사진을 갈아도 방문자 브라우저가 예전 것을 계속 쓴다.
        원래 이름을 함께 두는 이유는, 방문자에게 캐시된 옛 HTML 이 그 주소를
        찾기 때문이다. 없으면 그림이 깨진 화면을 보게 된다.
        같은 내용은 git 이 한 번만 저장하므로 저장소가 두 배가 되지는 않는다."""
        src_assets = os.path.join(ROOT, 'assets')
        if not os.path.isdir(src_assets):
            return
        for dirpath, _, names in os.walk(src_assets):
            for fn in names:
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, ROOT).replace(os.sep, '/')
                data = open(fp, 'rb').read()
                dest_dir = os.path.join(OUT, os.path.dirname(rel))
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(fp, os.path.join(OUT, rel))       # 원래 이름
                if fn.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.svg')):
                    base, ext = fn.rsplit('.', 1)
                    h = hashlib.md5(data).hexdigest()[:8]
                    hashed = f'{os.path.dirname(rel)}/{base}.{h}.{ext}'
                    shutil.copy2(fp, os.path.join(OUT, hashed))
                    IMG[rel] = hashed

    copy_images()
    def put(kind, name, text):
        """내용 해시를 파일 이름에 넣는다.

        style.css 처럼 이름이 고정이면, 내용을 고쳐도 브라우저가 예전 파일을
        계속 쓴다. 이름이 바뀌면 무조건 새로 받는다."""
        h = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        base, ext = name.rsplit('.', 1)
        rel = f'assets/{base}.{h}.{ext}'
        open(os.path.join(OUT, rel), 'w', encoding='utf-8').write(text)
        # 예전 이름으로도 같은 내용을 남긴다. 방문자 브라우저에 옛 HTML 이
        # 캐시돼 있으면 그것은 assets/style.css 를 찾는데, 그 경로가 없으면
        # 스타일이 통째로 빠진 화면을 보게 된다.
        open(os.path.join(OUT, f'assets/{name}'), 'w', encoding='utf-8').write(text)
        ASSET[kind] = rel

    gb_cfg0 = _guestbook.config()
    VISITS['js'] = _visits.js(gb_cfg0)
    VISITS['html'] = _visits.html() if gb_cfg0 else ''

    put('css', 'style.css',
        CSS + _guestbook.CSS + _appcount.CSS + _appshot.CSS + _visits.CSS)
    put('js', 'app.js', JS)

    # GitHub Pages 가 사이트를 Jekyll 로 다시 가공하지 않게 한다.
    # docs/ 를 통째로 다시 만들기 때문에 빌드할 때마다 새로 놓아야 한다.
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    src_app = os.path.join(ROOT, 'app')          # 정복 어플(PWA)
    if os.path.isdir(src_app):
        shutil.copytree(src_app, os.path.join(OUT, 'app'), dirs_exist_ok=True)
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import _app_build                        # 산 목록과 지도를 블로그 것으로 맞춘다
        pwa, solo = _app_build.build(kmap, mts, provinces_svg)
        open(os.path.join(OUT, 'app/index.html'), 'w', encoding='utf-8').write(pwa)
        open(os.path.join(OUT, 'app/bac100-tracker.html'), 'w',
             encoding='utf-8').write(solo)
        print(f'어플: 산 목록·지도를 블로그 데이터로 통일 (내려받기용 한 파일 판 포함)')

    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(build_index(mts))
    gb_cfg = _guestbook.config()
    open(os.path.join(OUT, 'guestbook.html'), 'w', encoding='utf-8').write(
        page('방명록 — ' + SITE, _guestbook.body(gb_cfg), 0,
             '블랙야크 100대 명산 기록 방명록', _guestbook.js(gb_cfg)))
    print('방명록: ' + ('Firebase 연결됨' if gb_cfg
                     else '설정 전 (data/firebase.json 없음)'))

    open(os.path.join(OUT, 'credits.html'), 'w', encoding='utf-8').write(
        build_credits(mts, photos))

    open(os.path.join(OUT, 'app-guide.html'), 'w', encoding='utf-8').write(
        build_app_guide(mts, kmap))

    for i, m in enumerate(mts):
        prev = mts[i - 1] if i > 0 else None
        nxt = mts[i + 1] if i < len(mts) - 1 else None
        open(os.path.join(OUT, 'mountain', m['slug'] + '.html'), 'w', encoding='utf-8') \
            .write(build_mountain(m, prev, nxt, kmap, photos))

    # 검색엔진용 — 어떤 주소가 있는지 알려준다
    today = datetime.date.today().isoformat()
    urls = [('', '1.0'), ('app-guide.html', '0.7'), ('guestbook.html', '0.5'), ('credits.html', '0.3')]
    urls += [(f"mountain/{m['slug']}.html", '0.8') for m in mts]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pri in urls:
        sitemap.append(f'<url><loc>{SITE_URL}{urllib.parse.quote(loc)}</loc>'
                       f'<lastmod>{today}</lastmod><priority>{pri}</priority></url>')
    sitemap.append('</urlset>')
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '\n'.join(sitemap))

    open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8').write(
        f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n'
        + (f'#DaumWebMasterTool:{DAUM_PIN}\n' if DAUM_PIN else ''))

    written = sum(1 for m in mts if m['content'])
    print(f'생성 완료: 페이지 {len(mts) + 3}개 (본문 작성 {written}/100)')
    print('→', os.path.join(OUT, 'index.html'))


if __name__ == '__main__':
    main()
