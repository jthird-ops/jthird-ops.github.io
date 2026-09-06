# -*- coding: utf-8 -*-
"""어플(app/index.html) 을 블로그 데이터에 맞춰 build/app/ 에 낸다.

원본 app/index.html 은 건드리지 않는다. 어플 기능을 고칠 때는 원본만 바꾸면
되고, 아래 손질은 빌드할 때마다 다시 적용된다.

하는 일
  1. 산 목록(이름·높이·지역·좌표)을 블로그 데이터로 통째로 교체
  2. 지역 칩을 블로그의 지역 구분에 맞춤
  3. 배경 지도(base64 JPEG)를 블로그의 시도별 SVG 로 교체
  4. 좁은 화면용 레이아웃을 덧붙인다 (원본에는 미디어쿼리가 없다)
  5. 내려받아 혼자 쓰는 한 파일짜리 판을 따로 만든다
"""
import io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REGION_ORDER = ["서울", "인천", "경기", "강원", "충북", "충남",
                "경북", "경남", "전북", "전남", "지리산", "제주도"]

# 블로그 지도와 같은 시도 색
FILLS = {'서울': '#dbe3f2', '인천': '#e9f0f6', '경기': '#e0eaf7', '강원': '#dfeee4',
         '충북': '#f6f0dc', '충남': '#fae7db', '경북': '#e8e3f4', '경남': '#dcecf2',
         '전북': '#f5ecdf', '전남': '#dff0e8', '지리산': '#eae4f3', '제주도': '#f4e5f2'}



MOBILE_CSS = """
  /* 어플 원본에는 미디어쿼리가 없다. 좁은 화면에서는 .left 가 320px 을
     차지해 지도 자리에 20~30px 밖에 남지 않아 마커만 세로로 늘어섰다.
     세로로 쌓고, 지도를 먼저 보여준다. */
  @media (max-width: 760px) {
    body { overflow-y: auto; }
    header { padding: 12px 14px; }
    header h1 { font-size: 15px; }
    .progress-wrap { min-width: 0; width: 100%; }

    .layout { flex-direction: column; height: auto; }
    .left { width: 100%; min-width: 0; border-right: none;
      border-bottom: 1px solid var(--line); order: 2; }
    .list { overflow-y: visible; max-height: none; }
    .right { order: 1; overflow: visible; padding: 12px;
      border-bottom: 1px solid var(--line); }
    .map-wrap { width: 100%; }
    .map-wrap svg.kmap { height: auto; width: 100%; max-width: 460px;
      margin: 0 auto; }
    .legend { flex-wrap: wrap; }

    /* 표가 좁아지므로 '등반일시' 칸을 줄인다 */
    .list-head, .row { grid-template-columns: 1fr 46px 74px 32px 32px;
      gap: 4px; font-size: 12px; }
  }
"""


def mountains_js(kmap, mts):
    """블로그의 100개 산을 어플이 쓰는 모양으로 만든다.

    좌표는 지도 안의 백분율로 준다. 어플이 마커를 left/top 퍼센트로 찍기
    때문에 지도 크기가 달라져도 그대로 맞는다."""
    W, H = kmap['width'], kmap['height']
    return [{
        "rank": m['rank'], "name": m['name'], "height": m['height'],
        "region": m['region'],
        "xPct": round(m['x'] / W * 100, 2),
        "yPct": round(m['y'] / H * 100, 2),
        "approx": False,               # 블로그 좌표는 실제 위도·경도에서 나온 값이다
        "climbed": False, "date": "",
    } for m in mts]


def kmap_svg(kmap, provinces_svg):
    shapes = ''.join(f'<path d="{d}"/>' for d in kmap['paths'])
    provs, plabels = provinces_svg(kmap)
    return (f'<svg class="kmap" viewBox="{kmap["viewBox"]}" '
            f'width="{kmap["width"]}" height="{kmap["height"]}" role="img" '
            f'aria-label="대한민국 시도별 100대 명산 위치 지도">'
            f'<g class="land">{shapes}</g><g class="provs">{provs}</g>'
            f'<g class="plabels">{plabels}</g></svg>')


def kmap_css():
    rules = ''.join(f'  .kmap .prov[data-region="{r}"] path {{ fill: {c}; }}\n'
                    for r, c in FILLS.items())
    return f"""
  .kmap {{ display: block; user-select: none; }}
  .kmap .land path {{ fill: #e9ece9; stroke: none; }}
  .kmap .prov path {{ fill: #eef1ee; stroke: #fff; stroke-width: 1.6;
    stroke-linejoin: round; }}
{rules}  .kmap .plabel {{ font-size: 26px; font-weight: 700; fill: #7a8794;
    text-anchor: middle; paint-order: stroke; stroke: #fff; stroke-width: 5px; }}
  .mapsrc {{ margin: 0; padding: 10px 16px 20px; font-size: 11.5px; color: var(--sub);
    text-align: center; }}
"""


def sub(src, pattern, repl, what, flags=0):
    out, n = re.subn(pattern, repl, src, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'어플에서 {what} 을(를) 찾지 못했습니다.')
    return out


def build(kmap, mts, provinces_svg):
    """(pwa_html, standalone_html) 를 돌려준다."""
    src = io.open(os.path.join(ROOT, 'app/index.html'), encoding='utf-8').read()

    # 1. 산 목록 교체
    data = json.dumps(mountains_js(kmap, mts), ensure_ascii=False)
    src = sub(src, r'const MOUNTAINS = \[.*?\];',
              lambda _: f'const MOUNTAINS = {data};', '산 목록', re.S)

    # 2. 지역 칩 — 블로그 지역 구분에 맞춘다 ('제주' 가 아니라 '제주도')
    chips = json.dumps(['전체', '완등', '미완등'] + REGION_ORDER, ensure_ascii=False)
    src = sub(src, r"const regions = \[.*?\];",
              lambda _: f'const regions = {chips};', '지역 칩 목록', re.S)

    # 3. 산 목록이 달라졌으므로 예전에 저장한 기록이 엉뚱한 산에 붙지 않게 키를 올린다
    src = sub(src, r"BAC100_USER_DATA_V1", 'BAC100_USER_DATA_V2', '저장 키')

    # 4. 배경 지도 교체
    src = sub(src, r'<img src="data:image/jpeg;base64,[^"]*"[^>]*>',
              lambda _: kmap_svg(kmap, provinces_svg), '배경 지도')
    src = src.replace('.map-wrap img {', '.map-wrap svg.kmap {')
    src = src.replace('width: 880px;\n    max-width: none;',
                      'height: 900px;\n    width: auto;\n    max-width: 100%;')
    # 이제 모든 좌표가 실제 위도·경도에서 나오므로 '위치 추정' 범례는 쓸 일이 없다
    src = re.sub(r'\s*<div class="item"><span class="sw" style="background:#fff;'
                 r'border-style:dashed[^>]*></span>위치 추정\(\*\)</div>', '', src, count=1)
    src = src.replace('</style>', kmap_css() + MOBILE_CSS + '</style>', 1)
    src = src.replace('</body>', '  <p class="mapsrc">지도 경계: Natural Earth 1:10m'
                                 ' · 시도 경계 admin-1 (public domain)</p>\n</body>', 1)

    # 5. 내려받아 혼자 쓰는 판 — file:// 에서는 매니페스트와 서비스워커를 못 쓴다
    solo = src.replace('<link rel="manifest" href="manifest.json">',
                       '<!-- 내려받기 판: 매니페스트를 쓰지 않습니다 -->')
    solo = re.sub(r"if \('serviceWorker' in navigator\) \{.*?\n\}",
                  '// 내려받기 판: 서비스워커를 쓰지 않습니다', solo, count=1, flags=re.S)
    return src, solo
