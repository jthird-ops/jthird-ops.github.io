# -*- coding: utf-8 -*-
"""assets/photos 의 사진을 웹용으로 다시 저장한다.

위키미디어에서 받은 원본은 최적화가 되어 있지 않아 용량이 크다.
가로 폭 상한을 두고 progressive JPEG 로 다시 인코딩한다. 여러 번 돌려도
이미 목표 크기·품질이면 더 나빠지지 않도록 원본보다 커지면 되돌린다.

  python tools/optimize_photos.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO_DIR = os.path.join(ROOT, 'assets/photos')

MAX_W = {'hero': 1800, 'thumb': 480, 'full': 1200}
QUALITY = 82


def target_width(name):
    if name == 'hero.jpg':
        return MAX_W['hero']
    return MAX_W['thumb'] if name.endswith('-t.jpg') else MAX_W['full']


def main():
    before = after = 0
    changed = 0
    for name in sorted(os.listdir(PHOTO_DIR)):
        if not name.lower().endswith('.jpg'):
            continue
        path = os.path.join(PHOTO_DIR, name)
        orig = os.path.getsize(path)
        before += orig

        try:
            im = Image.open(path)
            im.load()
            im = im.convert('RGB')
        except Exception as ex:
            print(f'  ! {name}: {ex}')
            after += orig
            continue

        w = min(target_width(name), im.width)
        if w != im.width:
            im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)

        tmp = path + '.tmp'
        im.save(tmp, 'JPEG', quality=QUALITY, optimize=True, progressive=True)
        new = os.path.getsize(tmp)

        if new < orig:
            os.replace(tmp, path)
            after += new
            changed += 1
            print(f'  {name:<28} {orig // 1024:>5}KB → {new // 1024:>4}KB')
        else:
            os.remove(tmp)          # 더 커지면 원본 유지
            after += orig

    print(f'\n{changed}개 재인코딩 · 합계 {before // 1024}KB → {after // 1024}KB '
          f'({100 - after * 100 // max(before, 1)}% 감소)')


if __name__ == '__main__':
    main()
