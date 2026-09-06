# -*- coding: utf-8 -*-
"""TourAPI 국문 관광정보 서비스에서 산 사진을 받아온다.

관광사진 갤러리(fetch_kto_photos.py)와 데이터가 다르다. 이쪽은 산 자체가
'관광지'로 등록되어 있고 대표 이미지가 붙어 있는 경우가 많다.

  python tools/fetch_tourapi_photos.py            # 조사 → data/tour_candidates.json
  python tools/fetch_tourapi_photos.py --download # data/tour_picked.json 대로 내려받기

저작권 구분(cpyrhtDivCd)
  Type1 : 공공누리 제1유형 — 출처표시, 변형 가능
  Type3 : 공공누리 제3유형 — 출처표시, 변형 금지
기본적으로 Type1 만 쓴다. Type3 는 --allow-type3 를 줘야 포함한다.
"""
import io, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO_DIR = os.path.join(ROOT, 'assets/photos')
UA = {'User-Agent': 'bac100-blog/1.0 (static site build script)'}
HOST = 'https://apis.data.go.kr/B551011/KorService2'

KOGL = {
    'Type1': ('공공누리 제1유형', 'https://www.kogl.or.kr/info/license.do#01'),
    'Type3': ('공공누리 제3유형', 'https://www.kogl.or.kr/info/license.do#03'),
}
PROVIDER = '한국관광공사 TourAPI'

# 블로그의 지역 구분 → 주소에 나타날 수 있는 표기
REGION_MATCH = {
    '서울': ['서울'], '인천': ['인천'], '경기': ['경기'], '강원': ['강원'],
    '충북': ['충청북', '충북'], '충남': ['충청남', '충남', '대전', '세종'],
    '경북': ['경상북', '경북', '대구'], '경남': ['경상남', '경남', '부산', '울산'],
    '전북': ['전라북', '전북'], '전남': ['전라남', '전남', '광주'],
    '제주도': ['제주'], '지리산': ['전라', '경상', '전북', '전남', '경남'],
}


def api_key():
    p = os.path.join(ROOT, '.env')
    for line in open(p, encoding='utf-8-sig'):
        if line.strip().startswith('TOUR_API_KEY='):
            return line.strip().split('=', 1)[1]
    sys.exit('.env 에 TOUR_API_KEY 가 없습니다.')


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def call(key, op, **params):
    q = {'serviceKey': key, 'MobileOS': 'ETC', 'MobileApp': 'bac100',
         '_type': 'json', 'numOfRows': 20, 'pageNo': 1, **params}
    # serviceKey 는 이미 인코딩된 값이라 다시 인코딩하면 안 된다
    qs = 'serviceKey=' + q.pop('serviceKey') + '&' + urllib.parse.urlencode(q)
    d = json.loads(get(f'{HOST}/{op}?{qs}').decode('utf-8'))
    body = d.get('response', {}).get('body', {})
    items = body.get('items') or {}
    if not items:
        return []
    it = items.get('item', [])
    return it if isinstance(it, list) else [it]


def region_ok(addr, region):
    return any(t in (addr or '') for t in REGION_MATCH.get(region, [region]))


def survey(key, mts, have):
    todo = [m for m in mts if m['slug'] not in have]
    out, found = {}, 0
    for i, m in enumerate(todo, 1):
        base = m['name'].split('(')[0].strip()
        rows = []
        try:
            items = call(key, 'searchKeyword2', keyword=base, contentTypeId=12)
        except Exception as ex:
            print(f'  ! {m["slug"]}: {ex}')
            items = []
        for it in items:
            img = it.get('firstimage') or ''
            if not img:
                continue
            addr = it.get('addr1', '')
            if not region_ok(addr, m['region']):
                continue
            if base not in it.get('title', ''):
                continue
            rows.append({
                "title": it.get('title', ''), "addr": addr,
                "image": img, "contentid": it.get('contentid', ''),
                "copyright": it.get('cpyrhtDivCd', '') or '?',
            })
        out[m['slug']] = rows[:4]
        if rows:
            found += 1
            r = rows[0]
            print(f'[{i:>2}/{len(todo)}] {m["slug"]:<14} {r["copyright"]:<6} '
                  f'{r["title"][:22]:<24} {r["addr"][:24]}')
        else:
            print(f'[{i:>2}/{len(todo)}] {m["slug"]:<14} —')
        time.sleep(.4)

    json.dump(out, open(os.path.join(ROOT, 'data/tour_candidates.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
    t1 = sum(1 for v in out.values() if v and v[0]['copyright'] == 'Type1')
    print(f'\n사진을 찾은 산 {found}/{len(todo)} (그중 Type1 자유이용 {t1}곳)')


def download(key, mts, have, allow3):
    from PIL import Image
    cands = json.load(open(os.path.join(ROOT, 'data/tour_candidates.json'), encoding='utf-8'))
    p_picked = os.path.join(ROOT, 'data/tour_picked.json')
    picked = json.load(open(p_picked, encoding='utf-8')) if os.path.exists(p_picked) else {}
    photos_p = os.path.join(ROOT, 'data/photos.json')
    photos = json.load(open(photos_p, encoding='utf-8'))
    os.makedirs(PHOTO_DIR, exist_ok=True)

    n = 0
    for slug, rows in cands.items():
        if slug in photos or not rows:
            continue
        if picked.get(slug) == -1:            # 사람이 '쓰지 않음'으로 표시
            continue
        r = rows[picked[slug]] if isinstance(picked.get(slug), int) else rows[0]
        if r['copyright'] not in ('Type1',) and not allow3:
            continue
        lic, lic_url = KOGL.get(r['copyright'], ('공공누리', ''))
        try:
            im = Image.open(io.BytesIO(get(r['image']))).convert('RGB')
        except Exception as ex:
            print(f'  ! {slug}: {ex}')
            continue

        for suffix, width in (('', 1200), ('-t', 480)):
            w = min(width, im.width)
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
                os.path.join(PHOTO_DIR, f'{slug}{suffix}.jpg'), 'JPEG',
                quality=82, optimize=True, progressive=True)

        photos[slug] = {
            "file": slug + '.jpg', "title": r['title'], "author": '한국관광공사',
            "license": lic, "license_url": lic_url,
            "source": f"https://korean.visitkorea.or.kr/detail/ms_detail.do?cotid={r['contentid']}",
            "provider": PROVIDER,
        }
        sz = os.path.getsize(os.path.join(PHOTO_DIR, slug + '.jpg')) // 1024
        print(f'  {slug:<14} {sz:>4}KB  {r["copyright"]:<6} {im.width}x{im.height}  {r["title"][:24]}')
        n += 1
        time.sleep(.3)

    json.dump(photos, open(photos_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n{n}장 추가 · 전체 {len(photos)}장')


def main():
    key = api_key()
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    have = json.load(open(os.path.join(ROOT, 'data/photos.json'), encoding='utf-8'))
    if '--download' in sys.argv:
        download(key, mts, have, '--allow-type3' in sys.argv)
    else:
        survey(key, mts, have)


if __name__ == '__main__':
    main()
