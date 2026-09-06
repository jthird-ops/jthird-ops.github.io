# -*- coding: utf-8 -*-
"""산 들머리 주변의 음식점을 TourAPI 에서 조사한다.

  python tools/fetch_food.py --heads   # 1단계: 들머리 좌표 → data/trailheads.json
  python tools/fetch_food.py           # 2단계: 주변 음식점 → data/food_candidates.json

산 정상이 아니라 '들머리(첫 번째 주차장)' 를 기준으로 찾는다. 산에서 내려와
바로 갈 수 있는 곳이라야 쓸모가 있기 때문이다. 주차장 위치를 찾지 못한 산은
정상 좌표로 대신하고 그렇게 표시해 둔다.

여기서 나온 것은 '관광공사에 등록된 음식점' 이지 맛집 순위가 아니다.
사람이 한 번 보고 걸러야 한다.
"""
import glob, json, math, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = 'https://apis.data.go.kr/B551011/KorService2'
UA = {'User-Agent': 'bac100-blog/1.0 (static site build script)'}

# 주차장 이름에서 떼어내면 검색이 잘 되는 꼬리말
SUFFIX = (r'(탐방지원센터|탐방안내소|탐방센터|국립공원|도립공원|군립공원|관광지'
          r'|휴게소|매표소|공영|주차장|선착장|야영장|오토캠핑장)')

# 음식점 같지 않거나 산행과 무관한 곳을 걸러낸다
BAD = ['카페', '커피', '베이커리', '제과', '디저트', '아이스크림', '펜션', '호텔',
       '모텔', '리조트', '편의점', '마트', '주점', '호프', '노래', 'PC', '당구']


def api_key():
    p = os.path.join(ROOT, '.env')
    for line in open(p, encoding='utf-8-sig'):
        if line.strip().startswith('TOUR_API_KEY='):
            return line.strip().split('=', 1)[1]
    sys.exit('.env 에 TOUR_API_KEY 가 없습니다.')


KEY = None


def call(op, **params):
    q = {'MobileOS': 'ETC', 'MobileApp': 'bac100', '_type': 'json',
         'numOfRows': 30, 'pageNo': 1, **params}
    url = f'{HOST}/{op}?serviceKey={KEY}&' + urllib.parse.urlencode(q)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=60) as r:
                d = json.loads(r.read().decode('utf-8'))
            body = d.get('response', {}).get('body', {}) or {}
            it = (body.get('items') or {}).get('item', [])
            return (it if isinstance(it, list) else [it]), body.get('totalCount', 0)
        except Exception:
            if i == 3:
                return [], 0
            time.sleep(2 * (i + 1))
    return [], 0


def km(lat1, lon1, lat2, lon2):
    """한반도 위도대에서 쓰는 거친 거리. 순서를 매기는 데만 쓴다."""
    return math.hypot((lat1 - lat2) * 111, (lon1 - lon2) * 88)


# ------------------------------------------------------------ 1단계: 들머리
def keywords(pk):
    n = re.sub(r'\(.*?\)', '', pk['name']).replace('주차장', '').strip()
    out = [n]
    s = re.sub(SUFFIX + r'\s*$', '', n).strip()
    if s and s != n:
        out.append(s)
    if n.split():
        out.append(n.split()[0])
    addr = pk.get('addr', '').split()
    if addr:
        out.append(addr[-1])                    # 주소의 리·동 이름
    seen = set()
    return [k for k in out if k and not (k in seen or seen.add(k))]


def find_heads(mts, contents):
    out = {}
    for i, m in enumerate(mts, 1):
        c = contents[m['slug']]
        best = None
        for pk in (c.get('parking') or [])[:2]:
            for k in keywords(pk):
                rows, _ = call('searchKeyword2', keyword=k)
                for it in rows:
                    try:
                        x, y = float(it['mapx']), float(it['mapy'])
                    except Exception:
                        continue
                    d = km(y, x, m['lat'], m['lon'])
                    if d < 25 and (best is None or d < best['dist']):
                        best = {'lat': y, 'lon': x, 'dist': round(d, 2),
                                'from': it.get('title', ''), 'keyword': k}
                time.sleep(.25)
                if best and best['dist'] < 8:
                    break
            if best and best['dist'] < 8:
                break
        if best is None:                        # 못 찾으면 정상 좌표로
            best = {'lat': m['lat'], 'lon': m['lon'], 'dist': 0,
                    'from': '정상 좌표(들머리 못 찾음)', 'keyword': ''}
        out[m['slug']] = best
        print(f'[{i:>3}/100] {m["slug"]:<16} {best["from"][:24]:<26} {best["dist"]}km')

    json.dump(out, open(os.path.join(ROOT, 'data/trailheads.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
    n = sum(1 for v in out.values() if v['keyword'])
    print(f'\n들머리 좌표 {n}곳 · 정상 좌표로 대신한 곳 {100 - n}곳')


# ------------------------------------------------------------ 2단계: 음식점
def survey(mts):
    heads = json.load(open(os.path.join(ROOT, 'data/trailheads.json'),
                           encoding='utf-8'))
    out = {}
    for i, m in enumerate(mts, 1):
        h = heads[m['slug']]
        rows = []
        for radius in (8000, 15000, 25000):
            rows, _ = call('locationBasedList2', mapX=h['lon'], mapY=h['lat'],
                           radius=radius, contentTypeId=39, arrange='S')
            rows = [r for r in rows
                    if not any(b in r.get('title', '') for b in BAD)]
            if len(rows) >= 6:
                break
            time.sleep(.3)

        picked = []
        for r in rows[:10]:
            intro, _ = call('detailIntro2', contentId=r['contentid'],
                            contentTypeId=39)
            it = intro[0] if intro else {}
            picked.append({
                'name': r.get('title', ''), 'addr': r.get('addr1', ''),
                'dist': round(float(r.get('dist', 0)) / 1000, 1),
                'menu': (it.get('firstmenu') or '').strip(),
                'others': (it.get('treatmenu') or '').strip()[:80],
                'hours': (it.get('opentimefood') or '').strip()[:60],
                'closed': (it.get('restdatefood') or '').strip()[:40],
                'tel': (r.get('tel') or '').strip(),
                'cid': r.get('contentid', ''),
            })
            time.sleep(.25)
        out[m['slug']] = picked
        top = picked[0]['name'] if picked else '—'
        print(f'[{i:>3}/100] {m["slug"]:<16} {len(picked):>2}곳  {top[:22]}')
        json.dump(out, open(os.path.join(ROOT, 'data/food_candidates.json'), 'w',
                            encoding='utf-8'), ensure_ascii=False, indent=1)

    few = [s for s, v in out.items() if len(v) < 4]
    print(f'\n조사 끝 · 4곳 미만인 산: {few if few else "없음"}')


def main():
    global KEY
    KEY = api_key()
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'),
                         encoding='utf-8'))
    contents = {os.path.basename(f)[:-5]: json.load(open(f, encoding='utf-8'))
                for f in glob.glob(os.path.join(ROOT, 'content/*.json'))}
    if '--heads' in sys.argv:
        find_heads(mts, contents)
    else:
        survey(mts)


if __name__ == '__main__':
    main()
