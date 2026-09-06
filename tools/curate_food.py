# -*- coding: utf-8 -*-
"""조사한 음식점을 다듬어 고르기 좋은 초안으로 만든다.

  python tools/curate_food.py            # data/food_draft.json 생성
  python tools/curate_food.py --apply    # 초안을 content/*.json 의 food 에 넣기

TourAPI 원자료를 그대로 쓰면 안 되는 이유가 셋 있다.
  - 영업시간에 <br> 같은 태그와 '- ' 머리표가 섞여 있다
  - 이름에 '카페' 가 없는 디저트 가게가 걸러지지 않는다
  - 가까운 순으로만 뽑으면 산행과 어울리지 않는 곳이 앞에 온다

그래서 손질하고, 산행 뒤 먹을 만한 음식에 가산점을 줘 순서를 다시 매긴다.
그래도 마지막에는 사람이 한 번 봐야 한다.
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = 5                      # 산마다 남길 곳
MAX_KM = 15                   # 이보다 멀면 뺀다 (남는 게 없으면 완화)

# 산에서 내려와 먹기 좋은 음식 — 가산점
GOOD = ['산채', '정식', '한정식', '비빔밥', '국밥', '해장', '칼국수', '보리밥',
        '두부', '순두부', '백숙', '닭', '오리', '추어탕', '매운탕', '어탕',
        '메밀', '막국수', '곤드레', '더덕', '버섯', '전골', '찌개', '국수',
        '한우', '갈비', '쌈밥', '묵', '전', '막걸리', '토속', '향토', '식당']
# 산행 뒤 끼니로 보기 어려운 곳 — 아예 뺀다
DROP = ['케이크', '베이커리', '제빵', '빵', '피낭시에', '디저트', '빙수', '와플',
        '마카롱', '도넛', '파스타', '피자', '스테이크', '버거', '샌드위치',
        '브런치', '아이스크림', '요거트', '스무디', '주스', '초콜릿', '에이드',
        '커피', '라떼', '카푸치노', '와인', '칵테일', '샐러드', '오므라이스']


def clean(t):
    """<br> 태그와 '- ' 머리표를 없애고 한 줄로 만든다."""
    if not t:
        return ''
    t = re.sub(r'<br\s*/?>', ' / ', t, flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('&amp;', '&').replace('&nbsp;', ' ')
    t = re.sub(r'(^|/)\s*-\s*', r'\1 ', t)
    t = re.sub(r'\s+', ' ', t).strip(' /')
    return t.strip()


def text_of(f):
    return f['name'] + ' ' + f.get('menu', '') + ' ' + f.get('others', '')


def is_bad(f):
    """산행 뒤 끼니로 보기 어려운 곳인가."""
    return any(d in text_of(f) for d in DROP)


def score(f):
    """순서를 매기는 점수. 제외 여부와는 따로 본다.

    예전에는 점수 하나로 제외까지 판정했는데, 거리 감점이 쌓이면 멀쩡한
    식당도 잘려나갔다(칠갑산이 0곳이 된 이유). 이제 둘을 나눈다."""
    return sum(2 for g in GOOD if g in text_of(f)) - f['dist'] * 0.3


def draft():
    cands = json.load(open(os.path.join(ROOT, 'data/food_candidates.json'),
                           encoding='utf-8'))
    out, thin = {}, []
    for slug, rows in cands.items():
        for f in rows:
            f['menu'] = clean(f.get('menu'))
            f['hours'] = clean(f.get('hours'))
            f['closed'] = clean(f.get('closed'))
        ok = [f for f in rows if not is_bad(f)]
        near = [f for f in ok if f['dist'] <= MAX_KM]
        pool = near if len(near) >= 3 else ok      # 가까운 곳이 적으면 거리를 푼다
        ranked = sorted(pool, key=lambda f: -score(f))[:KEEP]
        out[slug] = {
            'local': '',                        # 지역 향토음식 설명 — 사람이 쓴다
            'places': [{k: f[k] for k in
                        ('name', 'addr', 'dist', 'menu', 'hours', 'closed')
                        if f.get(k) not in (None, '')} for f in ranked],
        }
        if len(ranked) < 3:
            thin.append(f'{slug}({len(ranked)})')

    p = os.path.join(ROOT, 'data/food_draft.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n = sum(len(v['places']) for v in out.values())
    print(f'{len(out)}개 산 · 음식점 {n}곳 → data/food_draft.json')
    if thin:
        print(f'3곳 미만: {", ".join(thin)}')
    print('\nfood_draft.json 의 local 을 채운 뒤 --apply 로 반영하세요.')


def apply():
    draft_p = os.path.join(ROOT, 'data/food_draft.json')
    data = json.load(open(draft_p, encoding='utf-8'))
    n = 0
    for slug, food in data.items():
        p = os.path.join(ROOT, 'content', slug + '.json')
        c = json.load(open(p, encoding='utf-8'))
        c['food'] = {k: v for k, v in food.items() if v}
        json.dump(c, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        n += 1
    empty = [s for s, f in data.items() if not f.get('local')]
    print(f'{n}개 산에 맛집 반영')
    if empty:
        print(f'향토음식 설명이 비어 있는 산 {len(empty)}곳: {", ".join(empty[:8])}'
              + (' …' if len(empty) > 8 else ''))


if __name__ == '__main__':
    (apply if '--apply' in sys.argv else draft)()
