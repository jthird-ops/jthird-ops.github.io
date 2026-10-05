"""GPX → 3D 등산코스 페이지 (assets/3d/<이름>.html)

위성사진·지형 위에 걸은 경로를 그리고 카메라가 따라가는 한 장짜리 페이지를
만든다. 틀은 tools/3d_template.html, 지도 라이브러리는 assets/3d/maplibre-gl.*

    python tools/make_3d.py <GPX> --slug 가리왕산 --out gariwangsan-2026-10-04 \
        --name 가리왕산 --sub "휴양림 → 정상 → 중봉 → 휴양림 · 16.1km" --km 16.1 \
        [--peak "가리왕산 정상 1,561m"] [--duration 120]

페이지마다 설정과 경로를 data/3d/<이름>.json 에 남긴다. 틀을 고친 뒤에는
    python tools/make_3d.py --all
로 GPX 없이 전부 다시 만든다.

만든 뒤 content/<슬러그>.json 의 해당 등반기록에
    "fly": {"file": "3d/<이름>.html", "label": "3D 코스 따라가 보기"}
를 넣고 build.py 를 돌리면 기록 카드 오른쪽 위에 버튼이 생긴다.

Pacer 가 내보낸 GPX 는 시각 끝에 Z 가 붙어 있지만 실제로는 현지 시각이라
그대로 쓴다.
"""
import argparse, hashlib, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dist(a, b):
    x = math.radians(b[0] - a[0]) * math.cos(math.radians(a[1]))
    y = math.radians(b[1] - a[1])
    return 6371000 * math.hypot(x, y)


def bgm_ver():
    """배경음악 파일의 내용 해시 — 곡을 바꾸면 방문자가 새 것을 받도록 주소에 붙인다."""
    try:
        return hashlib.md5(open(os.path.join(ROOT, 'assets', '3d', 'bgm.mp3'), 'rb').read()).hexdigest()[:8]
    except OSError:
        return '0'


def write(cfg):
    tpl = open(os.path.join(ROOT, 'tools', '3d_template.html'), encoding='utf-8').read()
    out = (tpl.replace('/*TRACK*/', json.dumps(cfg['track'], separators=(',', ':')))
              .replace('__NAME__', cfg['name']).replace('__DATE__', cfg['date'])
              .replace('__SLUG__', cfg['slug']).replace('__SUB__', cfg['sub'])
              .replace('__KM__', repr(cfg['km'])).replace('__CLOCK__', str(cfg['clock']))
              .replace('__DURATION__', str(cfg['duration']))
              .replace('__PEAK__', json.dumps(cfg['peak'], ensure_ascii=False))
              .replace('__BGM__', bgm_ver()))
    dest = os.path.join(ROOT, 'assets', '3d', cfg['out'] + '.html')
    open(dest, 'w', encoding='utf-8').write(out)
    print(f"{dest}  (점 {len(cfg['track'])}개, {cfg['date']})")


def main():
    store = os.path.join(ROOT, 'data', '3d')
    if '--all' in sys.argv:
        for fn in sorted(os.listdir(store)):
            if fn.endswith('.json'):
                write(json.load(open(os.path.join(store, fn), encoding='utf-8')))
        return
    ap = argparse.ArgumentParser()
    ap.add_argument('gpx')
    ap.add_argument('--slug', required=True, help='산 글의 슬러그 (닫기 버튼이 돌아갈 곳)')
    ap.add_argument('--out', required=True, help='출력 파일 이름 (확장자 없이, 영문 권장)')
    ap.add_argument('--name', required=True, help='제목에 쓸 산 이름')
    ap.add_argument('--sub', required=True, help='제목 아래 한 줄 (코스 요약)')
    ap.add_argument('--km', type=float, required=True, help='앱이 기록한 총 거리')
    ap.add_argument('--peak', default='', help='최고 지점 라벨. 비우면 GPS 고도로 표기')
    ap.add_argument('--duration', type=int, default=0, help="'보통' 속도 전체 재생 초")
    a = ap.parse_args()

    s = open(a.gpx, encoding='utf-8').read()
    pts = []
    for la, lo, body in re.findall(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)">(.*?)</trkpt>', s, re.S):
        el = re.search(r'<ele>([-\d.]+)', body)
        t = re.search(r'<time>(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)', body)
        pts.append((float(lo), float(la), float(el.group(1)) if el else 0.0,
                    int(t[4]) * 3600 + int(t[5]) * 60 + int(t[6]), f'{t[1]}.{t[2]}.{t[3]}'))
    if len(pts) < 2:
        raise SystemExit('GPX 에서 경로 점을 찾지 못했습니다')
    # 제자리 흔들림(3m 미만 이동)은 버린다
    keep = [pts[0]]
    for p in pts[1:]:
        if dist(keep[-1], p) >= 3:
            keep.append(p)
    keep.append(pts[-1])
    t0 = keep[0][3]
    cfg = {'out': a.out, 'slug': a.slug, 'name': a.name, 'sub': a.sub, 'km': a.km, 'peak': a.peak,
           'duration': a.duration or max(75, round(a.km * 8)), 'date': pts[0][4], 'clock': t0,
           'track': [[round(p[0], 6), round(p[1], 6), round(p[2], 1), (p[3] - t0) % 86400] for p in keep]}
    os.makedirs(store, exist_ok=True)
    json.dump(cfg, open(os.path.join(store, a.out + '.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    write(cfg)


if __name__ == '__main__':
    main()
