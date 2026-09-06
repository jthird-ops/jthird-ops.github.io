# -*- coding: utf-8 -*-
"""위키미디어 공용(Wikimedia Commons)에서 자유 라이선스 사진을 받아온다.

  python tools/fetch_photos.py

- 아래 PICKS 에 적힌 파일만 받는다(자동 검색이 아니라 사람이 고른 목록).
- 허용 라이선스(퍼블릭 도메인 / CC0 / CC BY / CC BY-SA)가 아니면 건너뛴다.
- 받은 파일은 assets/photos/ 에, 출처·저작자·라이선스는 data/photos.json 에 저장한다.

사진을 직접 찍은 것으로 바꾸려면 assets/photos/<슬러그>.jpg 를 덮어쓰고
data/photos.json 의 해당 항목을 지우거나 credit 을 본인 것으로 고치면 된다.
"""
import json, os, re, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO_DIR = os.path.join(ROOT, 'assets/photos')
UA = {'User-Agent': 'bac100-blog/1.0 (static site build script)'}

ALLOWED = {'Public domain', 'CC0', 'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0',
           'CC BY-SA 2.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0'}

# 키 → (Commons 파일 제목, 내려받을 가로 픽셀)
PICKS = {
    "hero":          ("File:Everest Nuptse sunset panorama.jpg", 1800),
    "설악산":         ("File:Landscape in Seoraksan National Park 2.jpg", 1200),
    "북한산":         ("File:Baegundae Terrace of Bukhansan in Spring in Korea.jpg", 1200),
    "한라산":         ("File:Baengnokdam (2025-01) 3.jpg", 1200),
    "지리산천왕봉":    ("File:Jirisan National Park4.jpg", 1200),
    "무등산":         ("File:View from Mudeungsan.jpg", 1200),
    "월출산":         ("File:Wolchulsan Cloud Bridge 3.jpg", 1200),
    "내장산":         ("File:내장산 (Naejangsan).jpg", 1200),
    "태백산":         ("File:Taebaeksan 2016 12 30 winter.jpg", 1200),
    "소백산":         ("File:Snow in Sobaeksan national park.jpg", 1200),
    "속리산":         ("File:Songnisan.jpg", 1200),
    "마이산-진안":     ("File:Maisan.jpg", 1200),
    "대둔산":         ("File:Chilseongbong at Daedunsan.jpg", 1200),
    "감악산-파주":    ("File:Gamaksan Suspension Bridge in Paju South Korea.jpg", 1200),
    "가리왕산":       ("File:Jeongseon Alpine Center.jpg", 1200),
    "계룡산":         ("File:Gyeryongsan national park, Panoramic view.jpg", 1400),
    "관악산":         ("File:Gwanaksan Mountain 05 (17176328590).jpg", 1200),
    "금정산":         ("File:Geumjeong Mountain in Busan 2.jpg", 1200),
    "남산-경주":      ("File:Gyeongju from Namsan Mountain.jpg", 1200),
    "내연산":         ("File:Naeyeonsan.jpg", 1200),
    "달마산":         ("File:Mihwngsa's Tosolam 11-03838&39&40.JPG", 1200),
    "덕유산":         ("File:Korea-Snow in Mt. Deogyu-Stairway-01.jpg", 1200),
    "도락산":         ("File:도락산 원경.JPG", 1200),
    "도봉산":         ("File:Peak on Mount Dobongsan.JPG", 1200),
    "두타산":         ("File:청옥~두타 백두대간 능선 2020년 11월.jpg", 1200),
    "모악산":         ("File:Layer of mountains and Geumsansa temple - Moaksan.jpg", 1200),
    "민주지산":       ("File:Minjujisan Muju.jpg", 1200),
    "비슬산":         ("File:Peak of Cheonwangbong at Biseulsan.jpg", 1200),
    "삼악산":         ("File:삼악산 정상 3.jpg", 1200),
    "선운산":         ("File:선운산.jpg", 1200),
    "수락산":         ("File:Madangbawi at Suraksan in 206.jpg", 1200),
    "신불산":         ("File:신불산 1.jpg", 1200),
    "연인산":         ("File:Yeoninsan Mountain 01.jpg", 1200),
    "오대산비로봉":    ("File:View From Birobong.jpg", 1200),
    "오서산-보령":     ("File:Oseosan recrational forest in 2026 (3).jpg", 1200),
    "용봉산-홍성":     ("File:Yongbongsan 2005.JPG", 1200),
    "월악산":         ("File:Chungjuho Lake and Woraksan (5).jpg", 1200),
    "유명산":         ("File:Peak of Yumyeong Mountain.JPG", 1200),
    "장안산":         ("File:장안산.jpg", 1200),
    "조령산":         ("File:Saejae Bubong.jpg", 1200),
    "주왕산":         ("File:주왕산.jpg", 1200),
    "청계산":         ("File:Cheonggyesan Clear Forest Park 01.jpg", 1200),
    "치악산":         ("File:Chiaksan as seen from Birobong Peak (2).jpg", 1200),
    "팔공산":         ("File:Inbong in Palgong Mt.jpg", 1200),
    "화악산-가평":     ("File:Hwaaksan 2014.jpg", 1200),
    "화왕산-창녕":     ("File:Changnyeong Hwawangsan wide.jpg", 1200),
    "황매산-산청":     ("File:Hwangmaesan Mountain in autumn.jpg", 1200),
    "천마산":         ("File:Summit marker and Taegeukgion Cheonmasan Mountain (2025).jpg", 1200),
    "축령산-장성":     ("File:View from Chukryeongsan 2.jpg", 1200),
    "오봉산-춘천":     ("File:20241108 Nakjibibimbap 오봉산.jpg", 1200),
    "가지산":         ("File:Yeongnam Alps in Summer.jpg", 1200),
    "가야산-합천":     ("File:Kayasan04.JPG", 1200),
    "소요산":         ("File:Soyosan.jpg", 1200),
    "천성산":         ("File:Cheonsung.JPG", 1200),
}

LICENSE_URL = {
    'CC0': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'CC BY 2.0': 'https://creativecommons.org/licenses/by/2.0/',
    'CC BY 3.0': 'https://creativecommons.org/licenses/by/3.0/',
    'CC BY 4.0': 'https://creativecommons.org/licenses/by/4.0/',
    'CC BY-SA 2.0': 'https://creativecommons.org/licenses/by-sa/2.0/',
    'CC BY-SA 3.0': 'https://creativecommons.org/licenses/by-sa/3.0/',
    'CC BY-SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
}


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()


def info(title, width):
    u = ('https://commons.wikimedia.org/w/api.php?action=query&titles='
         + urllib.parse.quote(title)
         + f'&prop=imageinfo&iiprop=url%7Cextmetadata%7Csize&iiurlwidth={width}&format=json')
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        pages = json.load(r)['query']['pages']
    p = next(iter(pages.values()))
    if 'imageinfo' not in p:
        raise RuntimeError('파일을 찾을 수 없음')
    return p['imageinfo'][0]


SLEEP = 2.5          # Commons 는 연속 요청에 429 를 준다. 넉넉히 쉰다.


def fetch(url, tries=6):
    """Commons 는 연속 요청에 429 를 돌려주므로 간격을 늘려가며 재시도한다."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as ex:
            if ex.code != 429 or i == tries - 1:
                raise
            time.sleep(4 * (i + 1))


def main():
    os.makedirs(PHOTO_DIR, exist_ok=True)
    prev = os.path.join(ROOT, 'data/photos.json')
    out = json.load(open(prev, encoding='utf-8')) if os.path.exists(prev) else {}
    for key, (title, width) in PICKS.items():
        path0 = os.path.join(PHOTO_DIR, key + '.jpg')
        thumb0 = os.path.join(PHOTO_DIR, key + '-t.jpg')
        full_ok = key in out and os.path.exists(path0)
        thumb_ok = key == 'hero' or os.path.exists(thumb0)
        if full_ok and thumb_ok:
            continue                              # 둘 다 있으면 건너뛴다
        if full_ok and not thumb_ok:              # 썸네일만 보충
            try:
                ti = info(title, 480)
                td = fetch(ti.get('thumburl') or ti['url'])
                open(thumb0, 'wb').write(td)
                print(f'  {key:<14} 썸네일 {len(td)//1024:>3}KB')
            except Exception as ex:
                print(f'  ! {key}: 썸네일 실패 {ex}')
            time.sleep(SLEEP)
            continue
        for i in range(4):
            try:
                ii = info(title, width)
                break
            except urllib.error.HTTPError as ex:
                if ex.code != 429 or i == 3:
                    print(f'  ! {key}: {ex}')
                    ii = None
                    break
                time.sleep(6 * (i + 1))
            except Exception as ex:
                print(f'  ! {key}: {ex}')
                ii = None
                break
        if ii is None:
            continue
        meta = ii['extmetadata']
        lic = meta.get('LicenseShortName', {}).get('value', '?')
        if lic not in ALLOWED:
            print(f'  ! {key}: 허용되지 않는 라이선스({lic}) — 건너뜀')
            continue

        url = ii.get('thumburl') or ii['url']
        path = os.path.join(PHOTO_DIR, key + '.jpg')
        try:
            data = fetch(url)
        except Exception as ex:
            print(f'  ! {key}: 내려받기 실패 {ex}')
            continue
        open(path, 'wb').write(data)

        # 목록 카드는 작게 쓰므로 480px 썸네일을 따로 받아둔다
        tdata = b''
        if key != 'hero':
            try:
                ti = info(title, 480)
                tdata = fetch(ti.get('thumburl') or ti['url'])
                open(os.path.join(PHOTO_DIR, key + '-t.jpg'), 'wb').write(tdata)
            except Exception as ex:
                print(f'  ! {key}: 썸네일 실패 {ex}')

        author = strip_tags(meta.get('Artist', {}).get('value', '')) or '미상'
        out[key] = {
            "file": key + '.jpg',
            "title": title[5:],
            "author": author,
            "license": lic,
            "license_url": LICENSE_URL.get(lic, ''),
            "source": 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_')),
        }
        print(f'  {key:<14} {len(data)//1024:>4}KB'
              + (f' + {len(tdata)//1024:>3}KB' if tdata else '        ')
              + f'  {lic:<14} {author[:32]}')
        time.sleep(SLEEP)

    json.dump(out, open(os.path.join(ROOT, 'data/photos.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    total = sum(os.path.getsize(os.path.join(PHOTO_DIR, v['file'])) for v in out.values())
    print(f'\n사진 {len(out)}장 · 합계 {total//1024}KB · data/photos.json 기록 완료')


if __name__ == '__main__':
    main()
