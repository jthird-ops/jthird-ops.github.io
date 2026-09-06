# -*- coding: utf-8 -*-
"""주차장 정보를 content/<슬러그>.json 에 넣는다.

  python tools/set_parking.py data/parking/01.json

파일은 {"슬러그": [ {name, addr, lat, lon, capacity, fee, hours, note}, ... ]} 형태.
같은 슬러그를 다시 넣으면 덮어쓴다.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ('name', 'addr', 'query', 'lat', 'lon', 'capacity', 'fee', 'hours', 'note')


def main():
    if len(sys.argv) < 2:
        sys.exit('사용법: python tools/set_parking.py <주차장 JSON 파일...>')
    slugs = {m['slug'] for m in json.load(
        open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))}
    n = 0
    for src in sys.argv[1:]:
        data = json.load(open(src, encoding='utf-8'))
        for slug, rows in data.items():
            if slug not in slugs:
                sys.exit(f'없는 슬러그: {slug}')
            p = os.path.join(ROOT, 'content', slug + '.json')
            c = json.load(open(p, encoding='utf-8'))
            c['parking'] = [{k: r[k] for k in FIELDS if r.get(k) not in (None, '')}
                            for r in rows]
            json.dump(c, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f'  {slug:<16} 주차장 {len(rows)}곳')
            n += 1
    print(f'\n{n}개 산 갱신')


if __name__ == '__main__':
    main()
