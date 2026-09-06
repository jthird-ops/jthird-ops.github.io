# -*- coding: utf-8 -*-
"""Natural Earth(퍼블릭 도메인) 데이터에서 대한민국 외곽선 SVG를 만든다.

입력: world-atlas countries-10m.json (Natural Earth 10m 파생, public domain)
출력: blog/data/korea_map.json  { viewBox, paths[], project: {lon0,lat0,scale} }

  python tools/make_map.py <countries-10m.json 경로>
"""
import json, math, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOR_ID = "410"          # 대한민국
LAT0 = 36.2             # 투영 기준 위도 (한반도 중앙)
WIDTH = 1000            # SVG 기준 폭


# ---------------------------------------------------------------- topojson
def decode_arcs(topo):
    tr = topo["transform"]
    sx, sy = tr["scale"]
    tx, ty = tr["translate"]
    out = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        out.append(pts)
    return out


def arc_points(arcs, idx):
    if idx >= 0:
        return arcs[idx]
    return list(reversed(arcs[~idx]))


def ring_coords(arcs, ring):
    pts = []
    for i in ring:
        seg = arc_points(arcs, i)
        pts.extend(seg if not pts else seg[1:])
    return pts


# ---------------------------------------------------------------- 투영
def project(lon, lat):
    """등거리 원통 투영(위도 보정). 한반도 정도 범위에서는 왜곡이 미미하다."""
    return lon * math.cos(math.radians(LAT0)), -lat


# ---------------------------------------------------------------- 단순화
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
    """닫힌 링은 시작점==끝점이라 rdp의 기준선이 길이 0이 되어 전체가 붕괴한다.
    시작점에서 가장 먼 점을 찾아 두 개의 열린 선분으로 나눠 단순화한다."""
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 4:
        return pts
    ax, ay = pts[0]
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - ax) ** 2 + (pts[i][1] - ay) ** 2)
    head = rdp(pts[:far + 1], eps)
    tail = rdp(pts[far:] + [pts[0]], eps)
    return head[:-1] + tail[:-1]


def main(src):
    topo = json.load(open(src, encoding='utf-8'))
    arcs = decode_arcs(topo)

    geo = next(g for g in topo["objects"]["countries"]["geometries"] if g.get("id") == KOR_ID)
    polys = [geo["arcs"]] if geo["type"] == "Polygon" else geo["arcs"]

    rings = []
    for poly in polys:
        for ring in poly:                      # [0]=외곽, 나머지=구멍
            pts = [project(lon, lat) for lon, lat in ring_coords(arcs, ring)]
            rings.append(pts)

    # 아주 작은 섬은 버려서 SVG를 가볍게 유지
    def area(p):
        return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2
    rings = [r for r in rings if area(r) > 0.0006]
    rings.sort(key=area, reverse=True)

    # 화면 범위는 본토 + 제주도 기준으로 잡는다. 울릉도·독도까지 넣으면
    # 동쪽으로 크게 늘어나 지도가 비정상적으로 납작해진다.
    frame = [r for r in rings if area(r) > 0.1] or rings[:1]
    xs = [x for r in frame for x, _ in r]
    ys = [y for r in frame for _, y in r]
    pad = 0.12
    minx, maxx = min(xs) - pad, max(xs) + pad
    miny, maxy = min(ys) - pad, max(ys) + pad

    # 화면 밖 섬(울릉도·독도 등)은 그리지 않는다
    rings = [r for r in rings
             if any(minx <= x <= maxx and miny <= y <= maxy for x, y in r)]
    scale = WIDTH / (maxx - minx)
    height = (maxy - miny) * scale

    def to_svg(pts):
        return [((x - minx) * scale, (y - miny) * scale) for x, y in pts]

    paths = []
    for r in rings:
        p = simplify_ring(to_svg(r), 0.45)
        if len(p) < 4:
            continue
        d = 'M' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in p) + 'Z'
        paths.append(d)

    out = {
        "viewBox": f"0 0 {WIDTH} {height:.1f}",
        "width": WIDTH,
        "height": round(height, 1),
        "paths": paths,
        # lon/lat → SVG 좌표 변환에 필요한 값
        "project": {"lat0": LAT0, "minx": minx, "miny": miny, "scale": scale},
        "source": "Natural Earth 1:10m (public domain) via world-atlas"
    }
    json.dump(out, open(os.path.join(ROOT, 'data/korea_map.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    print(f'korea_map.json 생성: 폴리곤 {len(paths)}개, '
          f'좌표 {sum(d.count(",") for d in paths)}점, viewBox {out["viewBox"]}')


if __name__ == '__main__':
    main(sys.argv[1])
