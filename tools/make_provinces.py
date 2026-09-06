# -*- coding: utf-8 -*-
"""Natural Earth admin-1(퍼블릭 도메인)에서 대한민국 시도 경계를 추출해
korea_map.json 에 'provinces' 로 덧붙인다.

korea_map.json 에 이미 저장된 투영 파라미터를 그대로 쓰므로
산 마커 좌표(mountains.json 의 x/y)는 다시 계산할 필요가 없다.

  python tools/make_provinces.py <ne_10m_admin_1_states_provinces.geojson>
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPS = 0.35          # 단순화 허용오차(SVG 좌표 기준)
MIN_AREA = 3.0      # 이보다 작은 조각(작은 섬)은 버린다
LON_MAX = 130.5     # 울릉도·독도는 화면 밖이라 제외

# Natural Earth 이름 → 블로그에서 쓰는 지역 구분
REGION = {
    "Seoul": "서울", "Incheon": "인천", "Gyeonggi": "경기", "Gangwon": "강원",
    "North Chungcheong": "충북",
    "South Chungcheong": "충남", "Daejeon": "충남", "Sejong": "충남",
    "North Gyeongsang": "경북", "Daegu": "경북",
    "South Gyeongsang": "경남", "Busan": "경남", "Ulsan": "경남",
    "North Jeolla": "전북",
    "South Jeolla": "전남", "Gwangju": "전남",
    "Jeju": "제주도",
}
# 지도에 이름을 적을 지역 (서울·인천은 면적이 작아 라벨을 생략한다)
LABELLED = ["경기", "강원", "충북", "충남", "경북", "경남", "전북", "전남", "제주도"]


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    ax, ay = pts[0]
    bx, by = pts[-1]
    dx, dy = bx - ax, by - ay
    den = math.hypot(dx, dy) or 1e-12
    imax, dmax = 0, -1.0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * px - dx * py + bx * ay - by * ax) / den
        if d > dmax:
            imax, dmax = i, d
    if dmax <= eps:
        return [pts[0], pts[-1]]
    return rdp(pts[:imax + 1], eps)[:-1] + rdp(pts[imax:], eps)


def simplify_ring(pts, eps):
    """닫힌 링은 기준선 길이가 0이 되어 rdp가 붕괴하므로 두 조각으로 나눠 처리한다."""
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 4:
        return pts
    ax, ay = pts[0]
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - ax) ** 2 + (pts[i][1] - ay) ** 2)
    return rdp(pts[:far + 1], eps)[:-1] + rdp(pts[far:] + [pts[0]], eps)[:-1]


def area(p):
    return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1]
                   for i in range(len(p)))) / 2


def centroid(p):
    a = sx = sy = 0.0
    for i in range(len(p)):
        x0, y0 = p[i - 1]
        x1, y1 = p[i]
        cr = x0 * y1 - x1 * y0
        a += cr
        sx += (x0 + x1) * cr
        sy += (y0 + y1) * cr
    if abs(a) < 1e-9:
        return p[0]
    return sx / (3 * a), sy / (3 * a)


def main(src):
    mp = json.load(open(os.path.join(ROOT, 'data/korea_map.json'), encoding='utf-8'))
    pr = mp['project']
    k = math.cos(math.radians(pr['lat0']))

    def project(lon, lat):
        return ((lon * k - pr['minx']) * pr['scale'],
                (-lat - pr['miny']) * pr['scale'])

    feats = [f for f in json.load(open(src, encoding='utf-8'))['features']
             if f['properties'].get('admin') == 'South Korea']

    groups = {}                       # 지역명 → 링 목록
    for f in feats:
        name = f['properties']['name']
        region = REGION.get(name)
        if not region:
            print(f'  ! 매핑 없는 시도: {name}')
            continue
        geom = f['geometry']
        polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
        for poly in polys:
            for ring in poly:
                if max(c[0] for c in ring) > LON_MAX:      # 울릉도·독도
                    continue
                pts = [project(lon, lat) for lon, lat in ring]
                if area(pts) < MIN_AREA:
                    continue
                groups.setdefault(region, []).append(pts)

    provinces = []
    for region, rings in groups.items():
        rings.sort(key=area, reverse=True)
        paths = []
        for r in rings:
            p = simplify_ring(r, EPS)
            if len(p) < 4:
                continue
            paths.append('M' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in p) + 'Z')
        if not paths:
            continue
        cx, cy = centroid(rings[0])
        provinces.append({
            "region": region,
            "paths": paths,
            "label": ({"x": round(cx, 1), "y": round(cy, 1)} if region in LABELLED else None),
        })

    provinces.sort(key=lambda p: -len(p['paths']))
    mp['provinces'] = provinces
    mp['source'] = ("Natural Earth 1:10m — 국가 경계 via world-atlas, "
                    "시도 경계 admin-1 (public domain)")
    json.dump(mp, open(os.path.join(ROOT, 'data/korea_map.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)

    pts = sum(d.count(',') for p in provinces for d in p['paths'])
    print(f'시도 경계 {len(provinces)}개 지역 · 폴리곤 '
          f'{sum(len(p["paths"]) for p in provinces)}개 · 좌표 {pts}점')
    print('지역:', ', '.join(p['region'] for p in provinces))


if __name__ == '__main__':
    main(sys.argv[1])
