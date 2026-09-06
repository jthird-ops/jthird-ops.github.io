# -*- coding: utf-8 -*-
"""직접 찍은 사진을 블로그에 넣는다.

  python tools/add_my_photo.py <슬러그> <사진경로> [--date 2026-09-05]

HEIC(아이폰), JPG, PNG 모두 받는다. EXIF 회전 정보를 반영하고
커버(1200px)와 카드 썸네일(480px)을 만든 뒤 data/photos.json 에 기록한다.
기존 사진이 있으면 덮어쓴다.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO_DIR = os.path.join(ROOT, 'assets/photos')


def load_image(path):
    from PIL import Image, ImageOps
    if path.lower().endswith(('.heic', '.heif')):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            sys.exit('HEIC 를 읽으려면 pillow-heif 가 필요합니다:  pip install pillow-heif')
    im = Image.open(path)
    return ImageOps.exif_transpose(im).convert('RGB')      # 세로로 찍은 사진 바로 세우기


def shot_date(path):
    """EXIF 촬영일 → 없으면 폴더 이름의 날짜(예: 01_가리산_260905)를 쓴다."""
    try:
        from PIL import Image
        exif = Image.open(path).getexif()
        for tag in (36867, 306):                            # DateTimeOriginal, DateTime
            v = exif.get(tag)
            if v:
                return str(v)[:10].replace(':', '-')
    except Exception:
        pass
    m = re.search(r'_(\d{2})(\d{2})(\d{2})(?:\D|$)', os.path.basename(os.path.dirname(path)))
    if m:
        return f'20{m.group(1)}-{m.group(2)}-{m.group(3)}'
    return ''


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        sys.exit('사용법: python tools/add_my_photo.py <슬러그> <사진경로> [--date YYYY-MM-DD]')
    slug, src = args[0], args[1]
    date = ''
    if '--date' in sys.argv:
        date = sys.argv[sys.argv.index('--date') + 1]

    mts = {m['slug']: m for m in json.load(
        open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))}
    if slug not in mts:
        near = [s for s in mts if slug in s]
        sys.exit(f'"{slug}" 은 목록에 없는 슬러그입니다.'
                 + (f' 혹시 이것인가요: {", ".join(near)}' if near else ''))
    if not os.path.exists(src):
        sys.exit(f'사진을 찾을 수 없습니다: {src}')

    from PIL import Image
    im = load_image(src)
    os.makedirs(PHOTO_DIR, exist_ok=True)
    for suffix, width in (('', 1200), ('-t', 480)):
        w = min(width, im.width)
        im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
            os.path.join(PHOTO_DIR, f'{slug}{suffix}.jpg'), 'JPEG',
            quality=85, optimize=True, progressive=True)

    photos_p = os.path.join(ROOT, 'data/photos.json')
    photos = json.load(open(photos_p, encoding='utf-8'))
    photos[slug] = {
        "file": slug + '.jpg',
        "title": os.path.basename(src),
        "author": '직접 촬영',
        "license": '직접 촬영',
        "license_url": '',
        "source": '',
        "own": True,
        "date": date or shot_date(src),
    }
    json.dump(photos, open(photos_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    sz = os.path.getsize(os.path.join(PHOTO_DIR, slug + '.jpg')) // 1024
    st = os.path.getsize(os.path.join(PHOTO_DIR, slug + '-t.jpg')) // 1024
    print(f'{mts[slug]["name"]} ← {os.path.basename(src)}')
    print(f'  원본 {im.width}x{im.height} → 커버 {sz}KB + 썸네일 {st}KB'
          + (f'  · 촬영 {photos[slug]["date"]}' if photos[slug]['date'] else ''))
    print('\npython build.py 로 다시 빌드하세요.')


if __name__ == '__main__':
    main()
