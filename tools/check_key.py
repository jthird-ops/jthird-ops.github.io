# -*- coding: utf-8 -*-
"""`.env` 에 인증키가 제대로 들어갔는지 확인한다.

  python tools/check_key.py

키 값 자체는 화면에 찍지 않는다(길이와 앞뒤 몇 글자만 보여준다).
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, '.env')


def read_env(path):
    """아주 단순한 .env 파서. KEY=VALUE 한 줄씩."""
    out = {}
    if not os.path.exists(path):
        return out
    # 메모장이 UTF-8 BOM 을 붙이는 경우가 많아 utf-8-sig 로 읽는다
    for line in open(path, encoding='utf-8-sig'):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, _, v = line.partition('=')
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main():
    print(f'확인할 파일: {ENV}')

    if not os.path.exists(ENV):
        print('\n[X] .env 파일이 없습니다.')
        # 흔한 실수: 메모장이 .env.txt 로 저장한 경우
        for wrong in ('.env.txt', 'env', 'env.txt', '.ENV'):
            p = os.path.join(ROOT, wrong)
            if os.path.exists(p):
                print(f'    → 대신 "{wrong}" 파일이 있습니다. 이름을 ".env" 로 바꿔주세요.')
        print('    → blog 폴더 바로 아래에 ".env" 라는 이름으로 만들어야 합니다.')
        sys.exit(1)

    env = read_env(ENV)
    key = env.get('TOUR_API_KEY', '')

    if not key:
        print('\n[X] 파일은 있는데 TOUR_API_KEY 값이 없습니다.')
        print('    → 파일 내용이 "TOUR_API_KEY=키값" 형식인지 확인하세요.')
        sys.exit(1)

    if key.startswith('여기에') or key == '발급받은_인증키':
        print('\n[X] 예시 문구가 그대로 들어 있습니다. 실제 인증키로 바꿔주세요.')
        sys.exit(1)

    if len(key) < 40:
        print(f'\n[!] 키 길이가 {len(key)}자로 짧습니다. 값이 잘렸을 수 있습니다.')
        print('    → 공공데이터포털의 인증키는 보통 80자 안팎입니다.')

    masked = key[:6] + '…' + key[-4:]
    print(f'\n[O] 인증키를 읽었습니다.  길이 {len(key)}자,  {masked}')
    if '%' in key:
        print('    (Encoding 키로 보입니다. 그대로 두어도 스크립트가 알아서 처리합니다.)')
    print('\n준비 완료입니다. 이제 사진을 받아올 수 있습니다.')


if __name__ == '__main__':
    main()
