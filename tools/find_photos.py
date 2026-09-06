# -*- coding: utf-8 -*-
"""사진이 없는 산에 대해 위키미디어 공용에서 후보 이미지를 찾아 추려낸다.

  python tools/find_photos.py            → data/photo_candidates.json 생성

자동으로 내려받지 않는다. 사람이 결과를 보고 tools/fetch_photos.py 의 PICKS 에
넣을 파일을 고르는 것이 전제다.
"""
import json, os, re, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'bac100-blog/1.0 (static site build script)'}
ALLOWED = {'Public domain', 'CC0', 'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0',
           'CC BY-SA 2.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0'}

# 산 이름의 로마자 표기 (검색어로만 쓰인다)
ROMAN = {
 "가리산-홍천": "Garisan", "가리왕산": "Gariwangsan", "가야산-합천": "Gayasan Hapcheon",
 "가야산-충남": "Gayasan Seosan", "가지산": "Gajisan", "감악산-원주": "Gamaksan Wonju",
 "감악산-파주": "Gamaksan Paju", "계룡산": "Gyeryongsan", "계방산": "Gyebangsan",
 "관악산": "Gwanaksan", "광덕산": "Gwangdeoksan Cheonan", "구병산-보은": "Gubyeongsan",
 "구봉산-진안": "Gubongsan Jinan", "금수산": "Geumsusan", "금오산": "Geumosan Gumi",
 "금정산": "Geumjeongsan", "남산-경주": "Namsan Gyeongju", "내변산-변산": "Byeonsanbando",
 "내연산": "Naeyeonsan", "노인봉-오대산": "Noinbong Odaesan", "달마산": "Dalmasan",
 "대야산": "Daeyasan", "덕룡산": "Deongnyongsan Gangjin", "덕유산": "Deogyusan",
 "덕항산": "Deokhangsan", "도락산": "Doraksan", "도봉산": "Dobongsan",
 "동악산-곡성": "Dongaksan Gokseong", "두륜산": "Duryunsan", "두타산": "Dutasan",
 "마니산-강화도": "Manisan Ganghwa", "천마산": "Cheonmasan Namyangju",
 "명지산": "Myeongjisan", "모악산": "Moaksan", "민주지산": "Minjujisan",
 "바래봉-지리산": "Baraebong Jirisan", "반야봉-지리산": "Banyabong Jirisan",
 "방장산": "Bangjangsan Gochang", "방태산": "Bangtaesan", "백덕산": "Baekdeoksan",
 "백암산": "Baegamsan Jangseong", "백운산-광양": "Baegunsan Gwangyang",
 "백운산-동강": "Baegunsan Jeongseon", "불갑산-영광": "Bulgapsan",
 "비슬산": "Biseulsan", "삼악산": "Samaksan Chuncheon", "선운산": "Seonunsan",
 "소요산": "Soyosan", "수락산": "Suraksan", "신불산": "Sinbulsan",
 "연인산": "Yeoninsan", "오대산비로봉": "Odaesan Birobong", "오봉산-춘천": "Obongsan Chuncheon",
 "오서산-보령": "Oseosan", "용문산": "Yongmunsan", "용봉산-홍성": "Yongbongsan",
 "용화산": "Yonghwasan", "운악산": "Unaksan", "운장산": "Unjangsan",
 "월악산": "Woraksan", "유명산": "Yumyeongsan", "응봉산": "Eungbongsan Uljin",
 "장안산": "Jangansan", "재약산": "Jaeyaksan", "조계산": "Jogyesan",
 "조령산": "Joryeongsan", "주왕산": "Juwangsan", "주흘산": "Juheulsan",
 "천관산": "Cheongwansan", "천성산": "Cheonseongsan", "천태산": "Cheontaesan Yeongdong",
 "청계산": "Cheonggyesan", "청량산": "Cheongnyangsan Bonghwa", "청화산": "Cheonghwasan",
 "축령산-장성": "Chungnyeongsan Jangseong", "치악산": "Chiaksan", "칠갑산": "Chilgapsan",
 "칠보산": "Chilbosan Goesan", "태화산": "Taehwasan Yeongwol", "팔공산": "Palgongsan",
 "팔봉산-홍천": "Palbongsan Hongcheon", "팔영산": "Palyeongsan", "함백산": "Hambaeksan",
 "화악산-가평": "Hwaaksan", "화왕산-창녕": "Hwawangsan", "황매산-산청": "Hwangmaesan",
 "황석산-함양": "Hwangseoksan", "황악산-김천": "Hwangaksan",
}

# 산 풍경이 아닌 파일을 걸러내기 위한 제목 키워드
BAD = ['map', 'sign', 'signboard', 'diagram', 'poster', 'stamp', 'banner', 'logo',
       'chart', 'plan of', 'statue', 'buddha', 'pagoda', 'stele', 'monument',
       'interior', 'museum', 'portrait', 'painting', 'manuscript', 'document',
       'tomb', 'grave', 'bridge construction', 'parking', 'toilet', 'restaurant',
       'insect', 'butterfly', 'beetle', 'moth', 'spider', 'fungus', 'mushroom',
       'flower close', 'leaf', 'bird', 'snake', 'frog', '안내도', '지도', '표지',
       'panoramio - ', 'cropped']
GOOD = ['peak', 'summit', 'view', 'ridge', 'landscape', 'panorama', 'national park',
        'mountain', 'valley', 'autumn', 'snow', 'winter', 'sunrise', 'from']


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()


def api(params, tries=5):
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as ex:
            if ex.code != 429 or i == tries - 1:
                raise
            time.sleep(3 * (i + 1))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2)


def search(q, n=14):
    d = api({'action': 'query', 'generator': 'search', 'gsrsearch': q,
             'gsrnamespace': 6, 'gsrlimit': n, 'prop': 'imageinfo',
             'iiprop': 'url|extmetadata|size', 'format': 'json'})
    return list(d.get('query', {}).get('pages', {}).values())


def score(title, ii):
    t = title.lower()
    if any(b in t for b in BAD):
        return -1
    w, h = ii['width'], ii['height']
    if w < 1200 or w <= h:                 # 세로 사진은 카드(4:3)에 맞지 않는다
        return -1
    s = 0
    s += min(w, 4000) / 1000               # 해상도
    s += sum(2 for g in GOOD if g in t)    # 풍경다운 제목
    return s


def main():
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    have = json.load(open(os.path.join(ROOT, 'data/photos.json'), encoding='utf-8'))
    todo = [m for m in mts if m['slug'] not in have]

    out, found = {}, 0
    for i, m in enumerate(todo, 1):
        slug = m['slug']
        queries = [ROMAN.get(slug, slug), m['name'].split('(')[0]]
        cands, seen = [], set()
        for q in queries:
            try:
                pages = search(q)
            except Exception as ex:
                print(f'  ! {slug} "{q}": {ex}')
                continue
            for p in pages:
                if p['title'] in seen:
                    continue
                seen.add(p['title'])
                ii = p['imageinfo'][0]
                lic = ii['extmetadata'].get('LicenseShortName', {}).get('value', '?')
                if lic not in ALLOWED:
                    continue
                sc = score(p['title'], ii)
                if sc < 0:
                    continue
                cands.append({
                    "title": p['title'], "score": round(sc, 2), "license": lic,
                    "w": ii['width'], "h": ii['height'],
                    "author": strip_tags(ii['extmetadata'].get('Artist', {}).get('value', ''))[:40],
                })
            if len(cands) >= 4:
                break
            time.sleep(.8)
        cands.sort(key=lambda c: -c['score'])
        out[slug] = cands[:3]
        if cands:
            found += 1
        print(f'[{i:>2}/{len(todo)}] {slug:<14} 후보 {len(cands)}개'
              + (f' · {cands[0]["title"][5:60]}' if cands else ''))
        time.sleep(.8)

    json.dump(out, open(os.path.join(ROOT, 'data/photo_candidates.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n후보를 찾은 산 {found}/{len(todo)} · data/photo_candidates.json 저장')


if __name__ == '__main__':
    main()
