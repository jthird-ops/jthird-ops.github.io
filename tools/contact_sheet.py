# -*- coding: utf-8 -*-
"""사진 폴더에서 후보를 골라 번호를 붙인 한 장의 '컨택트 시트'를 만든다.

  python tools/contact_sheet.py <폴더> [출력파일] [--n 12]

산행 순서대로 고르게 뽑아 산행 전 구간이 들어가도록 한다.
연속 촬영(버스트)으로 거의 같은 사진이 이어지는 경우를 피하려고
전체를 균등 간격으로 샘플링한다.
"""
import os, re, sys

TILE_W, TILE_H, COLS = 400, 300, 4
PAD, HEAD = 10, 54
EXT = ('.heic', '.heif', '.jpg', '.jpeg', '.png')


def register_heif():
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass


def pick(folder, n):
    files = [f for f in os.listdir(folder) if f.lower().endswith(EXT)]
    files.sort(key=lambda f: (os.path.getmtime(os.path.join(folder, f)), f))
    if len(files) <= n:
        return files
    # 처음과 끝을 포함해 균등 간격으로 n장
    step = (len(files) - 1) / (n - 1)
    return [files[round(i * step)] for i in range(n)]


def main():
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    register_heif()

    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    folder = args[0]
    out = args[1] if len(args) > 1 else os.path.join(folder, '_contact_sheet.jpg')
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 12

    names = pick(folder, n)
    if not names:
        sys.exit(f'이미지가 없습니다: {folder}')

    rows = (len(names) + COLS - 1) // COLS
    W = COLS * TILE_W + (COLS + 1) * PAD
    H = HEAD + rows * (TILE_H + 26) + (rows + 1) * PAD
    sheet = Image.new('RGB', (W, H), '#1c2128')
    d = ImageDraw.Draw(sheet)

    def font(size):
        for p in (r'C:\Windows\Fonts\malgun.ttf', r'C:\Windows\Fonts\arial.ttf'):
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    d.text((PAD + 4, 16), os.path.basename(folder.rstrip('\\/')),
           fill='#e8eef5', font=font(24))

    for i, name in enumerate(names):
        r, c = divmod(i, COLS)
        x = PAD + c * (TILE_W + PAD)
        y = HEAD + PAD + r * (TILE_H + 26 + PAD)
        try:
            im = Image.open(os.path.join(folder, name))
            if name.lower().endswith(('.jpg', '.jpeg')):
                im.draft('RGB', (TILE_W * 2, TILE_H * 2))     # JPEG 는 빠르게 축소 디코딩
            im = ImageOps.exif_transpose(im).convert('RGB')
            im = ImageOps.fit(im, (TILE_W, TILE_H), Image.LANCZOS, centering=(.5, .5))
            sheet.paste(im, (x, y))
        except Exception as ex:
            d.rectangle([x, y, x + TILE_W, y + TILE_H], fill='#333')
            d.text((x + 10, y + 10), f'열기 실패\n{ex}'[:60], fill='#f88', font=font(14))

        # 번호 배지
        d.rectangle([x, y, x + 46, y + 34], fill='#111820')
        d.text((x + 14, y + 6), str(i + 1), fill='#ffd9a8', font=font(20))
        d.text((x + 2, y + TILE_H + 5), name, fill='#93a1b0', font=font(14))

    sheet.save(out, 'JPEG', quality=78, optimize=True, progressive=True)
    print(f'{out}  ({len(names)}장, {sheet.width}x{sheet.height},'
          f' {os.path.getsize(out)//1024}KB)')
    for i, name in enumerate(names, 1):
        print(f'  {i:>2}. {name}')


if __name__ == '__main__':
    main()
