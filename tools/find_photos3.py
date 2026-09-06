# -*- coding: utf-8 -*-
"""3차 후보 탐색 — 한국어 위키백과 문서의 대표 이미지를 쓴다.

'설악산' 문서의 대표 사진은 설악산 사진일 수밖에 없다.
검색어 매칭이나 분류보다 훨씬 정확하다. 이미지는 위키미디어 공용에 있으므로
라이선스는 공용 API 로 다시 확인한다.

  python tools/find_photos3.py   → data/photo_candidates3.json
"""
import json, os, re, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'bac100-blog/1.0 (static site build script)'}
ALLOWED = {'Public domain', 'CC0', 'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0',
           'CC BY-SA 2.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0'}
SLEEP = 2.0


def api(host, params, tries=6):
    u = f'https://{host}/w/api.php?' + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as ex:
            if ex.code != 429 or i == tries - 1:
                raise
            time.sleep(8 * (i + 1))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(4)
    return {}


def wiki_images(title):
    """문서에 쓰인 이미지 목록. 대표 이미지가 앞쪽에 오도록 pageimages 를 먼저 본다."""
    d = api('ko.wikipedia.org', {
        'action': 'query', 'titles': title, 'prop': 'pageimages|images',
        'piprop': 'name', 'imlimit': 20, 'redirects': 1, 'format': 'json'})
    pages = d.get('query', {}).get('pages', {})
    if not pages:
        return []
    p = next(iter(pages.values()))
    if 'missing' in p:
        return []
    out = []
    lead = p.get('pageimage')
    if lead:
        out.append('File:' + lead)
    for im in p.get('images', []):
        t = im['title']
        if t.lower().endswith(('.svg', '.ogg', '.pdf', '.webm')):
            continue
        if t not in out:
            out.append(t)
    return out[:6]


def commons_info(titles):
    d = api('commons.wikimedia.org', {
        'action': 'query', 'titles': '|'.join(titles), 'prop': 'imageinfo',
        'iiprop': 'url|extmetadata|size', 'format': 'json'})
    return list(d.get('query', {}).get('pages', {}).values())


BAD = ['map', 'locator', 'sign', 'diagram', 'logo', 'flag', 'emblem', 'seal',
       '지도', '위치', 'symbol', 'icon']


def main():
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    have = json.load(open(os.path.join(ROOT, 'data/photos.json'), encoding='utf-8'))
    todo = [m for m in mts if m['slug'] not in have]

    out, found = {}, 0
    for i, m in enumerate(todo, 1):
        slug = m['slug']
        # '가야산(합천)' → '가야산' 과 '가야산 (합천)' 두 가지로 시도
        base = m['name'].split('(')[0].strip()
        paren = re.search(r'\(([^)]+)\)', m['name'])
        titles = [f'{base} ({paren.group(1)})', base] if paren else [base]

        cands = []
        for t in titles:
            try:
                files = wiki_images(t)
            except Exception as ex:
                print(f'  ! {slug} "{t}": {ex}')
                files = []
            files = [f for f in files if not any(b in f.lower() for b in BAD)]
            if not files:
                time.sleep(SLEEP)
                continue
            try:
                for p in commons_info(files):
                    ii = (p.get('imageinfo') or [None])[0]
                    if not ii:
                        continue
                    lic = ii['extmetadata'].get('LicenseShortName', {}).get('value', '?')
                    if lic not in ALLOWED or ii['width'] < 900:
                        continue
                    cands.append({"title": p['title'], "license": lic,
                                  "w": ii['width'], "h": ii['height'],
                                  "lead": p['title'] == files[0]})
            except Exception as ex:
                print(f'  ! {slug}: {ex}')
            time.sleep(SLEEP)
            if cands:
                break

        cands.sort(key=lambda c: (not c['lead'], -(c['w'] > c['h']), -c['w']))
        out[slug] = cands[:4]
        if cands:
            found += 1
        print(f'[{i:>2}/{len(todo)}] {slug:<14} 후보 {len(cands)}'
              + (f"  {cands[0]['title'][5:60]}" if cands else ''))
        json.dump(out, open(os.path.join(ROOT, 'data/photo_candidates3.json'), 'w',
                            encoding='utf-8'), ensure_ascii=False, indent=1)
        time.sleep(SLEEP)

    print(f'\n후보를 찾은 산 {found}/{len(todo)}')


if __name__ == '__main__':
    main()
