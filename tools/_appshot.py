# -*- coding: utf-8 -*-
"""어플 화면을 보여주는 그림.

실제 스크린샷을 뜨려면 헤드리스 브라우저가 있어야 하는데 이 환경에는 없다.
그래서 어플과 같은 재료(같은 지도 데이터, 같은 색, 같은 배치)로 화면을
다시 그린다. **사진이 아니라 그림이며, 페이지에도 그렇게 밝힌다.**

실제 스크린샷으로 바꾸려면 assets/app-shot.png 를 두면 된다. 그러면
build.py 가 그림 대신 그 사진을 쓴다.
"""
import hashlib, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = 'assets/app-shot.png'          # 있으면 이 사진을 쓴다

GREEN, RED = '#1f9d55', '#d64545'


def real_shot():
    return SHOT if os.path.exists(os.path.join(ROOT, SHOT)) else None


def _climbed(name):
    """어느 산을 '완등' 으로 칠할지 — 이름에서 뽑아 늘 같게 나오도록."""
    return int(hashlib.md5(name.encode()).hexdigest(), 16) % 100 < 37


def svg(kmap, mts):
    """어플 화면 그림. 지도는 사이트에서 쓰는 것과 같은 데이터다."""
    W, H = kmap['width'], kmap['height']
    land = ''.join(f'<path d="{d}"/>' for d in kmap['paths'])

    dots = []
    for m in mts:
        on = _climbed(m['name'])
        dots.append(f'<circle cx="{m["x"]:.0f}" cy="{m["y"]:.0f}" r="15" '
                    f'fill="{GREEN if on else RED}" stroke="#fff" stroke-width="5"/>')

    # 왼쪽 목록에 보여줄 몇 줄
    rows = []
    for i, m in enumerate(mts[:6]):
        y = 92 + i * 34
        on = _climbed(m['name'])
        rows.append(
            f'<text class="as-nm" x="20" y="{y}">#{m["rank"]} {m["name"]}</text>'
            f'<text class="as-ht" x="250" y="{y}" text-anchor="end">{m["height"]}</text>'
            f'<circle cx="272" cy="{y - 5}" r="6" fill="{GREEN if on else RED}"/>')

    return f'''<svg class="app-shot" viewBox="0 0 760 470" role="img"
     aria-label="어플 화면 그림 — 왼쪽에 산 목록, 오른쪽에 완등 여부를 표시한 지도">
  <defs>
    <clipPath id="as-clip"><rect x="0" y="0" width="760" height="470" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#as-clip)">
    <rect width="760" height="470" fill="#f7f8fa"/>
    <rect width="760" height="46" fill="#fff"/>
    <text class="as-title" x="20" y="29">블랙야크 100대 명산 등반 트래커</text>
    <text class="as-prog" x="740" y="29" text-anchor="end">37 / 100 완등 (37%)</text>
    <rect x="0" y="45" width="760" height="1" fill="#e5e7eb"/>

    <!-- 왼쪽: 목록 -->
    <rect x="0" y="46" width="292" height="424" fill="#fff"/>
    <rect x="291" y="46" width="1" height="424" fill="#e5e7eb"/>
    <rect x="14" y="56" width="264" height="24" rx="7" fill="#f2f4f6"/>
    <text class="as-ph" x="24" y="72">산 이름 검색…</text>
    {''.join(rows)}

    <!-- 오른쪽: 지도 -->
    <svg x="300" y="52" width="452" height="410" viewBox="0 0 {W} {H}"
         preserveAspectRatio="xMidYMid meet">
      <g fill="#e4e9e5">{land}</g>
      {''.join(dots)}
    </svg>
    <g class="as-key" transform="translate(560,60)">
      <circle cx="0" cy="-4" r="6" fill="{GREEN}"/><text x="11" y="0">완등</text>
      <circle cx="58" cy="-4" r="6" fill="{RED}"/><text x="69" y="0">미완등</text>
    </g>
  </g>
  <rect x="0.5" y="0.5" width="759" height="469" rx="14" fill="none" stroke="#dfe3e8"/>
</svg>'''


def block(kmap, mts):
    """어플 설명 + 화면. 실제 스크린샷이 있으면 그것을 쓴다."""
    shot = real_shot()
    if shot:
        figure = (f'<img class="app-shot" src="{shot}" alt="어플 화면" '
                  f'loading="lazy" decoding="async">')
        caption = '어플 실제 화면입니다.'
    else:
        figure = svg(kmap, mts)
        caption = ('어플과 같은 지도 데이터로 그린 화면입니다. 사진이 아니라 그림입니다.')

    return f'''
      <div class="app-about">
        <h3>어플은 이렇게 생겼습니다</h3>
        <div class="app-about-grid">
          <figure class="app-fig">
            {figure}
            <figcaption>{caption}</figcaption>
          </figure>
          <div class="app-about-txt">
            <p>왼쪽에 100개 산이 순서대로 놓이고, 오른쪽 지도에 같은 산이 점으로
               찍힙니다. 목록에서 산을 고르면 지도의 점이, 지도에서 점을 누르면
               목록의 줄이 서로 따라 움직입니다.</p>
            <p>완등한 산은 초록, 남은 산은 빨강입니다. 지도를 한 번 보면 어느
               지역이 비어 있는지 바로 드러나서, 다음에 어디를 갈지 정하기가
               쉬워집니다.</p>
            <p>산마다 다녀온 날짜를 적을 수 있고, 위쪽 칩으로 지역이나 완등
               여부를 걸러 볼 수 있습니다. 검색창에 이름을 넣어 바로 찾을 수도
               있습니다.</p>
            <p class="app-about-note">이 블로그와 똑같은 100대 명산 목록과 지도를
               씁니다. 산 이름·높이·지역이 어긋나지 않습니다.</p>
          </div>
        </div>
      </div>'''


CSS = """
.app-about{margin-top:28px;padding-top:24px;border-top:1px solid var(--line)}
.app-about h3{margin:0 0 16px;font-size:15px}
.app-about-grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);
  gap:22px;align-items:start}
.app-fig{margin:0}
svg.app-shot,img.app-shot{display:block;width:100%;height:auto;border-radius:14px}
img.app-shot{border:1px solid #dfe3e8}
.app-fig figcaption{margin-top:8px;font-size:12px;color:var(--sub);line-height:1.6}
.app-shot .as-title{font:700 15px system-ui,sans-serif;fill:#1f2430}
.app-shot .as-prog{font:600 12px system-ui,sans-serif;fill:#6b7280}
.app-shot .as-ph{font:12px system-ui,sans-serif;fill:#9aa3ad}
.app-shot .as-nm{font:600 12.5px system-ui,sans-serif;fill:#1f2430}
.app-shot .as-ht{font:11.5px system-ui,sans-serif;fill:#6b7280}
.app-shot .as-key text{font:600 11.5px system-ui,sans-serif;fill:#6b7280}
.app-about-txt p{margin:0 0 11px;font-size:14px;line-height:1.8}
.app-about-note{color:var(--sub);font-size:13px!important}
@media(max-width:760px){.app-about-grid{grid-template-columns:1fr}}
"""
