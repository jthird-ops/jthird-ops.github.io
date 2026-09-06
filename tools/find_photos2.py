# -*- coding: utf-8 -*-
"""2차 후보 탐색 — 위키미디어 공용의 '분류(Category)'를 이용한다.

검색어 매칭은 엉뚱한 결과(동명이산·외국 지명·동식물)를 자주 물어온다.
분류는 사람이 정리해둔 것이라 훨씬 정확하다.

  python tools/find_photos2.py   → data/photo_candidates2.json
"""
import json, os, re, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'bac100-blog/1.0 (static site build script)'}
ALLOWED = {'Public domain', 'CC0', 'CC BY 2.0', 'CC BY 3.0', 'CC BY 4.0',
           'CC BY-SA 2.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0'}

BAD = ['map', 'sign', 'diagram', 'poster', 'stamp', 'logo', 'statue', 'buddha',
       'pagoda', 'stele', 'monument', 'interior', 'museum', 'portrait', 'painting',
       'tomb', 'grave', 'insect', 'butterfly', 'beetle', 'moth', 'spider', 'fungus',
       'mushroom', 'bird', 'snake', 'frog', 'flower', 'plant', 'leaf ', 'berry',
       '안내도', '지도', '표지', '불상', '석탑', '탱화']
GOOD = ['peak', 'summit', 'view', 'ridge', 'landscape', 'panorama', 'national park',
        'mountain', 'valley', 'autumn', 'snow', 'winter', 'sunrise', '정상', '능선',
        '전경', '풍경', '설경']


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()


SLEEP = 2.5


def api(params, tries=7):
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
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


def find_category(names):
    """산 이름으로 분류를 찾는다. 정확히 일치하는 분류를 우선한다."""
    for n in names:
        d = api({'action': 'query', 'list': 'search', 'srsearch': n,
                 'srnamespace': 14, 'srlimit': 6, 'format': 'json'})
        hits = [h['title'] for h in d.get('query', {}).get('search', [])]
        for h in hits:
            t = h[9:].lower()
            if t == n.lower() or t.startswith(n.lower()):
                return h
        if hits:
            return hits[0]
        time.sleep(SLEEP)
    return None


def members(cat, limit=60):
    d = api({'action': 'query', 'generator': 'categorymembers', 'gcmtitle': cat,
             'gcmtype': 'file', 'gcmlimit': limit, 'prop': 'imageinfo',
             'iiprop': 'url|extmetadata|size', 'format': 'json'})
    return list(d.get('query', {}).get('pages', {}).values())


def score(title, ii):
    t = title.lower()
    if any(b in t for b in BAD):
        return -1
    w, h = ii['width'], ii['height']
    if w < 1200 or w <= h:
        return -1
    return min(w, 4000) / 1000 + sum(2 for g in GOOD if g in t)


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'fp', os.path.join(ROOT, 'tools/find_photos.py'))
    fp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fp)

    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    have = json.load(open(os.path.join(ROOT, 'data/photos.json'), encoding='utf-8'))
    todo = [m for m in mts if m['slug'] not in have]

    out, found = {}, 0
    for i, m in enumerate(todo, 1):
        slug = m['slug']
        names = [fp.ROMAN.get(slug, slug).split(' ')[0], m['name'].split('(')[0]]
        try:
            cat = find_category(names)
        except Exception as ex:
            print(f'  ! {slug}: 분류 검색 실패 {ex}')
            out[slug] = {"category": None, "candidates": []}
            time.sleep(10)
            continue
        cands = []
        if cat:
            try:
                for p in members(cat):
                    ii = p['imageinfo'][0]
                    lic = ii['extmetadata'].get('LicenseShortName', {}).get('value', '?')
                    if lic not in ALLOWED:
                        continue
                    sc = score(p['title'], ii)
                    if sc < 0:
                        continue
                    cands.append({"title": p['title'], "score": round(sc, 2),
                                  "license": lic, "w": ii['width'], "h": ii['height']})
            except Exception as ex:
                print(f'  ! {slug}: {ex}')
        cands.sort(key=lambda c: -c['score'])
        out[slug] = {"category": cat, "candidates": cands[:4]}
        if cands:
            found += 1
        print(f'[{i:>2}/{len(todo)}] {slug:<14} {str(cat)[9:40]:<32} 후보 {len(cands)}')
        json.dump(out, open(os.path.join(ROOT, 'data/photo_candidates2.json'), 'w',
                            encoding='utf-8'), ensure_ascii=False, indent=1)
        time.sleep(SLEEP)

    json.dump(out, open(os.path.join(ROOT, 'data/photo_candidates2.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n후보를 찾은 산 {found}/{len(todo)}')


if __name__ == '__main__':
    main()
