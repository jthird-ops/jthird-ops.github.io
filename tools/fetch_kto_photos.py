# -*- coding: utf-8 -*-
"""한국관광공사 관광사진 API(포토코리아)에서 산 사진을 받아온다.

  python tools/fetch_kto_photos.py            # 후보를 찾아 data/kto_candidates.json 에 저장
  python tools/fetch_kto_photos.py --download # 확정된 것을 내려받아 photos.json 에 기록

사진은 공공누리 제1유형(출처 표시 시 상업적 이용·변형 가능)이다.
촬영자와 출처를 페이지에 표기해야 한다.
"""
import io, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO_DIR = os.path.join(ROOT, 'assets/photos')
UA = {'User-Agent': 'bac100-blog/1.0 (static site build script)'}
API = 'https://apis.data.go.kr/B551011/PhotoGalleryService1/gallerySearchList1'

LICENSE = '공공누리 제1유형'
LICENSE_URL = 'https://www.kogl.or.kr/info/license.do#01'
PROVIDER = '한국관광공사 포토코리아'

# 산 풍경이 아닌 사진을 걸러낸다
BAD = ['축제', '행사', '음식', '먹거리', '숙박', '펜션', '호텔', '박물관', '전시',
       '체험', '공연', '마을', '시장', '카페', '해수욕장', '해변', '항구', '포구',
       '온천', '스키', '골프', '경기장', '터미널', '역사(驛)', '기차', '공항',
       '야경', '불꽃', '드론쇼', '조형물', '동상', '기념관']
# 산 사진일 가능성을 높이는 낱말
GOOD = ['정상', '능선', '전경', '풍경', '설경', '운해', '일출', '일몰', '단풍',
        '암릉', '봉', '계곡', '폭포', '등산', '산행', '국립공원', '군립공원',
        '도립공원', '바위', '억새', '철쭉', '진달래']


def api_key():
    p = os.path.join(ROOT, '.env')
    if not os.path.exists(p):
        sys.exit('.env 파일이 없습니다. tools/check_key.py 로 먼저 확인하세요.')
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


def search(key, keyword, rows=30):
    """인증키는 이미 URL 인코딩된 값(Encoding 키)이므로 다시 인코딩하지 않는다."""
    qs = (f'?serviceKey={key}&numOfRows={rows}&pageNo=1&MobileOS=ETC'
          f'&MobileApp=bac100&arrange=A'
          f'&keyword={urllib.parse.quote(keyword)}&_type=json')
    d = json.loads(get(API + qs).decode('utf-8'))
    body = d.get('response', {}).get('body', {})
    items = (body.get('items') or {})
    if not items:
        return []
    it = items.get('item', [])
    return it if isinstance(it, list) else [it]


def score(item, m):
    title = item.get('galTitle', '')
    loc = item.get('galPhotographyLocation', '')
    base = m['name'].split('(')[0].strip()
    if any(b in title for b in BAD):
        return -1
    s = 0
    if base in title:
        s += 6                       # 제목에 산 이름이 있으면 확실하다
    if base in loc:
        s += 2
    # 지역이 맞는지 (강원 → 강원특별자치도 등 앞 두 글자로 확인)
    if m['region'][:2] in loc:
        s += 3
    s += sum(1.5 for g in GOOD if g in title)
    return s


def find(argv):
    key = api_key()
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    have = json.load(open(os.path.join(ROOT, 'data/photos.json'), encoding='utf-8'))
    todo = [m for m in mts if m['slug'] not in have]

    out, found = {}, 0
    for i, m in enumerate(todo, 1):
        base = m['name'].split('(')[0].strip()
        cands = []
        try:
            for it in search(key, base):
                sc = score(it, m)
                if sc < 3:                     # 산 이름·지역 어느 쪽도 안 맞으면 버린다
                    continue
                cands.append({
                    "score": round(sc, 1),
                    "title": it.get('galTitle', ''),
                    "url": it.get('galWebImageUrl', ''),
                    "photographer": it.get('galPhotographer', '') or '미상',
                    "location": it.get('galPhotographyLocation', ''),
                    "id": it.get('galContentId', ''),
                })
        except Exception as ex:
            print(f'  ! {m["slug"]}: {ex}')
        cands.sort(key=lambda c: -c['score'])
        out[m['slug']] = cands[:5]
        if cands:
            found += 1
        top = cands[0]['title'] if cands else ''
        print(f'[{i:>2}/{len(todo)}] {m["slug"]:<14} 후보 {len(cands):>2}  {top[:40]}')
        time.sleep(.4)

    json.dump(out, open(os.path.join(ROOT, 'data/kto_candidates.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n후보를 찾은 산 {found}/{len(todo)} · data/kto_candidates.json 저장')


def download(argv):
    """data/kto_picked.json 에 적힌 '슬러그 → 사진 제목' 대로 내려받는다.

    후보 목록의 순번이 아니라 제목으로 지정하므로, 검색 결과 순서가 바뀌어도
    같은 사진을 다시 받는다."""
    from PIL import Image
    key = api_key()
    mts = {m['slug']: m for m in json.load(
        open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))}
    picked = json.load(open(os.path.join(ROOT, 'data/kto_picked.json'), encoding='utf-8'))
    photos_p = os.path.join(ROOT, 'data/photos.json')
    photos = json.load(open(photos_p, encoding='utf-8'))
    os.makedirs(PHOTO_DIR, exist_ok=True)

    n = 0
    for slug, want in picked.items():
        if slug.startswith('_') or slug in photos:
            continue
        # 값은 제목 문자열이거나 {"title":.., "id":..} 형태. 같은 제목이 여러 장일 때
        # 콘텐츠 ID 로 한 장을 콕 집는다.
        want_id = None
        if isinstance(want, dict):
            want, want_id = want['title'], str(want.get('id') or '')
        m = mts[slug]
        base = m['name'].split('(')[0].strip()
        hit = None
        for q in (want, base):
            try:
                for it in search(key, q, 60):
                    if it.get('galTitle', '').strip() != want:
                        continue
                    if want_id and str(it.get('galContentId')) != want_id:
                        continue
                    hit = it
                    break
            except Exception as ex:
                print(f'  ! {slug}: {ex}')
            if hit:
                break
            time.sleep(.4)
        if not hit:
            print(f'  ! {slug}: "{want}" 사진을 찾지 못했습니다')
            continue

        try:
            im = Image.open(io.BytesIO(get(hit['galWebImageUrl']))).convert('RGB')
        except Exception as ex:
            print(f'  ! {slug}: 내려받기 실패 {ex}')
            continue

        for suffix, width in (('', 1200), ('-t', 480)):
            w = min(width, im.width)
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(
                os.path.join(PHOTO_DIR, f'{slug}{suffix}.jpg'), 'JPEG',
                quality=82, optimize=True, progressive=True)

        photos[slug] = {
            "file": slug + '.jpg',
            "title": hit.get('galTitle', ''),
            "author": hit.get('galPhotographer', '') or '미상',
            "license": LICENSE,
            "license_url": LICENSE_URL,
            "source": 'https://api.visitkorea.or.kr/',
            "provider": PROVIDER,
        }
        sz = os.path.getsize(os.path.join(PHOTO_DIR, slug + '.jpg')) // 1024
        st = os.path.getsize(os.path.join(PHOTO_DIR, slug + '-t.jpg')) // 1024
        print(f'  {slug:<14} {sz:>4}KB + {st:>3}KB  {photos[slug]["author"][:12]:<14}'
              f'{im.width}x{im.height}  {hit.get("galTitle","")[:26]}')
        n += 1
        time.sleep(.4)

    json.dump(photos, open(photos_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n{n}장 추가 · 전체 {len(photos)}장')


if __name__ == '__main__':
    (download if '--download' in sys.argv else find)(sys.argv)
