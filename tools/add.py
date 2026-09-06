# -*- coding: utf-8 -*-
"""배치로 작성한 산 본문(JSON)을 content/ 에 저장한다.

  python tools/add.py <배치파일.py>

배치 파일은 D = { "산이름": {...}, ... } 딕셔너리 하나만 정의하면 된다.
"""
import json, os, sys, runpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = "2026-09-04"

REQUIRED = ["summary", "intro", "highlights", "courses", "cert", "access", "season", "tips", "sources"]


def main(batch):
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    slug = {m['name']: m['slug'] for m in mts}

    D = runpy.run_path(batch)['D']
    for name, c in D.items():
        if name not in slug:
            raise SystemExit(f'! 목록에 없는 산 이름: {name}')
        miss = [k for k in REQUIRED if not c.get(k)]
        if miss:
            raise SystemExit(f'! {name}: 누락 필드 {miss}')
        c.setdefault('updated', U)
        p = os.path.join(ROOT, 'content', slug[name] + '.json')
        json.dump(c, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    done = len(os.listdir(os.path.join(ROOT, 'content')))
    todo = [m['name'] for m in mts
            if not os.path.exists(os.path.join(ROOT, 'content', m['slug'] + '.json'))]
    print(f'이번 배치 {len(D)}개 저장 · 누적 {done}/100 · 남은 {len(todo)}개')
    if todo:
        print('남은 산:', ', '.join(todo[:12]) + (' …' if len(todo) > 12 else ''))


if __name__ == '__main__':
    main(sys.argv[1])
