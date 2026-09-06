# 블랙야크 100대 명산 기록 — 정적 블로그

`bac100_app_18.html`(등반 트래커)의 산 데이터를 기반으로 만든 정적 블로그입니다.
외부 패키지 없이 파이썬 표준 라이브러리만으로 빌드됩니다.

## 빌드

```
python build.py
```

`docs/` 에 사이트가 생성됩니다. GitHub Pages 가 저장소 루트 아니면 `/docs`
만 게시할 수 있어서 그 이름을 씁니다. 배포는 아래 'GitHub Pages 로 올리기'.

## 구조

| 경로 | 설명 |
|---|---|
| `data/mountains.json` | 100개 산 (이름·높이·지역·위경도·지도좌표·슬러그) |
| `data/coords.tsv` | 산별 위경도 원본 표. 수정 후 재투영하면 지도 마커가 갱신됩니다 |
| `data/korea_map.json` | 대한민국 외곽선 + 11개 시도 경계 SVG 패스 (Natural Earth, public domain) |
| `content/<슬러그>.json` | 산별 본문. 파일이 없으면 "글 준비 중" 페이지가 생성됩니다 |
| `assets/photos/` | 메인 이미지(`hero.jpg`)와 산별 사진(`<슬러그>.jpg`) |
| `data/photos.json` | 사진별 저작자·라이선스·출처. 페이지에 표기됩니다 |
| `build.py` | 정적 사이트 생성기 (HTML/CSS/JS 포함) |
| `tools/make_map.py` | Natural Earth topojson → `korea_map.json` (국가 외곽선) 생성 |
| `tools/make_provinces.py` | Natural Earth admin-1 → `korea_map.json` 에 시도 경계 추가 |
| `tools/add.py` | 배치 파일의 `D` 딕셔너리를 `content/*.json` 으로 저장 |
| `tools/fetch_photos.py` | 위키미디어 공용에서 자유 라이선스 사진 내려받기 |
| `tools/find_photos.py` | 검색어로 사진 후보 찾기 (1차) |
| `tools/find_photos2.py` | 분류(Category)로 후보 찾기 (2차, 더 정확) |
| `tools/find_photos3.py` | 한국어 위키백과 대표 이미지로 후보 찾기 (3차) |
| `tools/fetch_kto_photos.py` | 한국관광공사 관광사진 API 에서 사진 받기 |
| `tools/check_key.py` | `.env` 의 API 인증키 확인 |
| `tools/optimize_photos.py` | 사진 리사이즈·재인코딩 |
| `tools/add_my_photo.py` | 직접 찍은 사진(HEIC 포함) 넣기 |
| `tools/contact_sheet.py` | 사진 폴더 → 번호 붙인 컨택트 시트 |

## 본문 스키마 (`content/*.json`)

```
summary     한 줄 요약
intro       도입 문단 배열
highlights  이 산의 포인트 배열
courses     [{name, path, distance, time, level(하/중/상)}]
cert        인증장소 설명
access      {car, transit}
parking     [{name, addr, capacity, fee, hours, note, query, lat, lon}]
food        {local: 지역 향토음식 설명, places: [{name, addr, dist, menu,
              hours, closed, note, query}]}
season      계절 안내
tips        알아두면 좋은 것 배열
sources     [{title, url}]
updated     기준 일자
```

## GitHub Pages 로 올리기

소스와 사이트를 한 저장소에 두고, Pages 가 `docs/` 를 게시하는 방식입니다.
빌드는 내 컴퓨터에서 하고 결과물을 함께 커밋합니다.

### 1. 저장소 만들기

<https://github.com/new> 에서 **Public** 으로 만듭니다. README 등 초기 파일은
넣지 마세요(빈 저장소로).

이름이 URL을 정합니다.

```
bac100                → https://<아이디>.github.io/bac100/
<아이디>.github.io     → https://<아이디>.github.io/
```

이 사이트는 모든 링크가 상대경로라 어느 쪽이든 그대로 동작합니다.

### 2. 올리기

`blog` 폴더에서:

```
git init
git config core.quotepath false
git add .
git commit -m "블랙야크 100대 명산 기록 사이트"
git branch -M main
git remote add origin https://github.com/<아이디>/<저장소>.git
git push -u origin main
```

`git push` 에서 로그인을 물으면 브라우저 인증을 따르거나, 비밀번호 자리에
**개인 액세스 토큰**(Settings → Developer settings → Personal access tokens)
을 넣습니다. 계정 비밀번호는 받지 않습니다.

### 3. Pages 켜기

저장소 **Settings → Pages** 에서

- Source: **Deploy from a branch**
- Branch: **main** / 폴더 **/docs** → Save

1~2분 뒤 그 화면에 주소가 뜹니다.

### 4. 고친 뒤 다시 올리기

```
python build.py
git add .
git commit -m "무엇을 고쳤는지"
git push
```

푸시하면 1분 안팎으로 반영됩니다.

### 알아둘 것

- **저장소는 공개입니다.** `.env`(TourAPI 키)는 `.gitignore` 에 있어 올라가지
  않습니다. 올리기 전에 `git status` 로 `.env` 가 목록에 없는지 확인하세요.
- **`data/firebase.json` 도 올라가지 않습니다.** 방명록·다운로드 수는 빌드할 때
  `docs/` 안으로 값이 박히므로 사이트에서는 정상 동작합니다. 다른 컴퓨터에서
  다시 빌드하려면 그 파일을 옮겨야 합니다.
- **용량 29MB**(사진 24MB)로 Pages 권장 한도 1GB에 여유가 많습니다.
- **파일명이 한글**입니다(`docs/mountain/설악산.html` 등 100개, 사진 189개).
  Pages 는 문제없이 서비스합니다. `core.quotepath false` 는 git 이 한글 이름을
  읽기 좋게 보여주게 하는 설정입니다.
- **`docs/.nojekyll`** 은 GitHub 이 사이트를 Jekyll 로 다시 가공하지 않게 막는
  빈 파일입니다. 빌드할 때마다 자동으로 만들어집니다.
- **스타일·스크립트 파일 이름에 내용 해시가 붙습니다**(`style.f6bb1837.css`).
  이름이 고정이면 내용을 고쳐도 방문자 브라우저가 예전 파일을 계속 씁니다.
  주소 뒤에 `?v=2` 를 붙이는 것으로는 해결되지 않습니다 — 그건 HTML 만 새로
  받고, HTML 이 가리키는 CSS 는 여전히 캐시된 것을 쓰기 때문입니다.
- Firestore 는 접속 도메인을 따로 등록할 필요가 없습니다. 보호는 보안 규칙이
  합니다. 다만 나중에 구글 클라우드 콘솔에서 API 키에 **HTTP 리퍼러 제한**을
  걸었다면, Pages 주소를 허용 목록에 넣어야 방명록이 동작합니다.

## 정복 어플

원본은 `app/` 의 세 파일(`index.html`, `manifest.json`, `sw.js`)입니다. **원본은
건드리지 않습니다.** 빌드할 때 `tools/_app_build.py` 가 아래를 손질해 `docs/app/`
으로 냅니다.

1. 산 목록을 `data/mountains.json` 으로 통째로 교체 — 이름·높이·지역·순번이
   블로그와 어긋나지 않게 한다
2. 좌표를 블로그 지도 기준 백분율로 다시 계산
3. 지역 칩을 블로그의 지역 구분에 맞춤(`제주` 가 아니라 `제주도`)
3-1. 좁은 화면용 레이아웃을 덧붙임 — 원본에는 미디어쿼리가 하나도 없어서
   `.left` 가 320px 을 차지하고 지도 자리에 20~30px 밖에 남지 않았다.
   760px 이하에서는 세로로 쌓고 지도를 위에 둔다.
4. 배경 지도를 블로그의 시도별 SVG 로 교체
5. `STORAGE_KEY` 를 올려 예전 기록이 엉뚱한 산에 붙지 않게 함

결과물 두 가지:

```
docs/app/index.html            첫 화면에서 바로 여는 판 (PWA)
docs/app/bac100-tracker.html   내려받기용 한 파일 판 (109KB, 외부 참조 없음)
```

내려받기 판은 매니페스트와 서비스워커를 뺐습니다 — `file://` 에서는 못 쓰기
때문입니다. 어플 기능을 고칠 때는 `app/index.html` 만 바꾸고 `python build.py`
를 돌리면 두 판 모두 다시 만들어집니다.

`_app_build.py` 는 원본에서 특정 문구를 찾아 바꾸는 방식이라, 원본을 크게
고치면 `어플에서 ... 을(를) 찾지 못했습니다` 로 빌드가 멈춥니다. 그때는
`_app_build.py` 의 해당 정규식을 원본에 맞춰 고치면 됩니다.

기록은 이용자 브라우저의 localStorage 에만 저장됩니다. 서버로 보내지 않습니다.

## 주차장

산마다 들머리 주차장을 1~3곳씩 적어 두었습니다(100개 산, 204곳). 본문의
'가는 길' 아래 별도 섹션으로 나옵니다.

`name` 과 `addr` 만 필수이고 나머지는 아는 것만 채웁니다. `capacity`·`fee`·
`hours` 는 칩으로, `note` 는 문단으로 나옵니다.

지도 링크는 **이름 검색**이 기본입니다. 어림한 좌표로 길안내를 걸면 엉뚱한
곳으로 보내기 때문에, `lat`/`lon` 은 실제로 확인한 주차장에만 넣고 그때만
'길찾기' 단추가 추가로 붙습니다. 검색어를 직접 정하고 싶으면 `query` 를
씁니다(기본값은 `<산 이름> <주차장 이름>`, 산 이름의 괄호는 뗍니다).

한 번에 여러 산을 넣을 때:

```
python tools/set_parking.py data/parking/01.json
python build.py
```

주차 요금과 면수는 자주 바뀌므로 페이지 하단에 확인을 권하는 안내가 함께
나갑니다.

## 맛집

각 산 페이지의 '주차장' 아래에 나옵니다. 두 부분입니다.

- `food.local` — 그 지역이 무엇으로 알려져 있는지. 사람이 씁니다. 식당은
  없어져도 향토음식은 잘 바뀌지 않아 오래갑니다.
- `food.places` — 한국관광공사 TourAPI 에 등록된 음식점. **맛집 순위가 아닙니다.**
  페이지에도 그렇게 밝혀 둡니다.

거리는 정상이 아니라 **들머리(첫 번째 주차장)** 기준입니다. 산에서 내려와 바로
갈 수 있어야 쓸모가 있기 때문입니다. 들머리 좌표는 `data/trailheads.json` 에
있고, 주차장 위치를 못 찾은 산은 정상 좌표로 대신하며 그렇게 적어 둡니다.

수집은 두 단계입니다.

```
python tools/fetch_food.py --heads   # 들머리 좌표  → data/trailheads.json
python tools/fetch_food.py           # 주변 음식점  → data/food_candidates.json
```

두 번째 결과는 **그대로 쓰지 않습니다.** 카페·펜션 같은 것은 자동으로 걸러내지만
산행과 무관한 곳이 남으므로, 사람이 보고 고른 뒤 `content/<슬러그>.json` 의
`food` 에 넣습니다.

## 방명록

`docs/guestbook.html` 로 나가고 상단 메뉴와 푸터에서 이어집니다. 정적 사이트라
글을 저장할 곳이 없어 **Firebase Firestore** 를 씁니다.

`data/firebase.json` 이 없으면 '아직 준비 중입니다' 안내만 나옵니다. 설정 없이
빌드해도 사이트는 멀쩡히 만들어지므로, 호스팅을 정한 뒤에 붙여도 됩니다.

### 1. 프로젝트 만들기

1. <https://console.firebase.google.com> 에서 **프로젝트 추가** (구글 계정 필요)
2. 애널리틱스는 꺼도 됩니다
3. 왼쪽 **빌드 → Firestore Database → 데이터베이스 만들기**
4. **프로덕션 모드**로 시작합니다 (테스트 모드는 30일 뒤 막힙니다)
5. 위치는 `asia-northeast3 (서울)` 을 고릅니다

### 2. 설정값 가져오기

프로젝트 설정(톱니바퀴) → **내 앱** → 웹 아이콘 `</>` 으로 앱을 등록하면
`firebaseConfig` 값이 나옵니다. 그 값을 `data/firebase.json` 으로 저장합니다.
`data/firebase.example.json` 이 본보기입니다.

```
cp data/firebase.example.json data/firebase.json   # 값을 채워 넣는다
python build.py
```

> `apiKey` 는 비밀번호가 아닙니다. 웹 앱에 실려 브라우저로 내려가는 값이라
> 감출 수 없고, 감출 필요도 없습니다. **실제 보호는 아래 규칙이 합니다.**

### 3. 보안 규칙 — 반드시 넣으세요

Firestore → **규칙** 에 아래를 붙여넣고 게시합니다. 이걸 넣지 않으면 누구나
남의 글을 지우거나 고칠 수 있습니다.

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /guestbook/{entry} {
      allow read: if true;
      allow create: if request.resource.data.keys().hasOnly(['name','message','createdAt'])
                    && request.resource.data.name is string
                    && request.resource.data.name.size() > 0
                    && request.resource.data.name.size() <= 20
                    && request.resource.data.message is string
                    && request.resource.data.message.size() > 0
                    && request.resource.data.message.size() <= 500
                    && request.resource.data.createdAt == request.time;
      allow update, delete: if false;
    }

    // 어플 내려받기 횟수 — 1씩 올리는 것만 허용한다
    match /stats/{doc} {
      allow read: if true;
      allow create: if request.resource.data.keys().hasOnly(['count'])
                    && request.resource.data.count == 1;
      allow update: if request.resource.data.keys().hasOnly(['count'])
                    && request.resource.data.count == resource.data.count + 1;
      allow delete: if false;
    }
  }
}
```

방명록은 읽기 누구나, 쓰기는 형식이 맞을 때만, 수정·삭제는 아무도 못 합니다.
`stats` 는 값을 **정확히 1 올리는 것만** 허용하므로 아무 숫자나 써 넣을 수
없습니다. 다만 여러 번 눌러 올리는 것까지는 막지 못합니다.

### 4. 글 지우기

규칙이 클라이언트 삭제를 막으므로 **Firebase 콘솔의 Firestore → guestbook**
에서 직접 지웁니다. 스팸은 반드시 오니 가끔 들여다보세요.

### 무료 한도

읽기 하루 5만 건, 쓰기 2만 건까지 무료입니다. 이 규모의 블로그에서는 넘길 일이
거의 없습니다. 걱정되면 콘솔에서 예산 알림을 걸어 두세요.

### 스팸 막이

폼에 사람 눈에 안 보이는 칸(`gb-trap`)을 두고, 거기에 값이 채워지면 보내지
않습니다. 자동 프로그램 상당수를 막아 주지만 전부는 아닙니다. 더 필요해지면
Firebase App Check 를 붙이는 것이 다음 단계입니다.

## 어플 소개 화면

`06 정복 어플` 패널 아래쪽에 어플 설명과 화면이 나옵니다.

지금 들어가는 그림은 **사진이 아니라 그림**입니다. 스크린샷을 자동으로 뜨려면
헤드리스 브라우저가 필요한데 없어서, 어플과 같은 지도 데이터·같은 색·같은
배치로 다시 그렸습니다. 캡션에도 그렇게 밝혀 둡니다.

**실제 스크린샷으로 바꾸려면** `assets/app-shot.png` 로 저장하고 다시 빌드하면
됩니다. 파일이 있으면 그림 대신 그 사진을 쓰고 캡션도 '어플 실제 화면입니다'
로 바뀝니다.

```
# 어플을 띄우고 화면을 잘라 저장 (윈도우: Win+Shift+S)
python build.py
```

가로로 넓은 화면(1000px 안팎)을 담으면 목록과 지도가 함께 보여 좋습니다.

## 방문자 수

모든 페이지 푸터에 `오늘 N명 · 전체 M명이 다녀갔습니다` 로 나옵니다. 방명록과
같은 Firebase 설정을 쓰며, `data/firebase.json` 이 없으면 자리째 숨깁니다.

```
stats/visits             전체 누적
stats/visits-YYYY-MM-DD  그날치
```

보안 규칙은 `stats/{doc}` 전체에 걸려 있어 문서가 늘어도 손댈 것이 없습니다.

**세는 것이 무엇인지 분명히 해 둡니다.** 같은 브라우저에서 하루에 한 번만
세므로 '방문 횟수' 가 아니라 **그날 다녀간 브라우저 수**에 가깝습니다.
`localStorage` 를 지우거나 다른 기기·다른 브라우저로 오면 다시 셉니다.
규칙이 '1씩 올리기' 만 허용하므로 임의의 숫자를 넣을 수는 없지만, 마음먹고
반복해 올리는 것은 막지 못합니다. **대략의 눈금**입니다.

숫자를 되돌리려면 Firebase 콘솔에서 `stats/visits` 문서의 `count` 를 직접
고치면 됩니다.

### 어느 페이지가 인기 있는지 보고 싶다면

이 카운터로는 알 수 없습니다. 그럴 때는 GoatCounter 같은 도구를 붙입니다.
개인 사이트는 무료이고 쿠키를 쓰지 않아 동의 배너가 필요 없으며, 스크립트가
3KB 라 페이지가 느려지지 않습니다. <https://www.goatcounter.com> 에서 가입해
받은 스크립트 한 줄을 `page()` 의 `extra_head` 에 넣으면 됩니다.

## 어플 내려받기 횟수

첫 화면 `06 정복 어플` 의 내려받기 단추를 누르면 Firestore 의
`stats/appDownloads` 문서에서 `count` 가 1 올라가고, 그 숫자가 단추 아래
`지금까지 N번 내려받았습니다` 로 나옵니다.

방명록과 같은 Firebase 설정을 씁니다. `data/firebase.json` 이 없으면 스크립트를
아예 넣지 않고 카운터 자리도 숨겨진 채로 둡니다.

**세는 것이 무엇인지 분명히 해 둡니다.**

- 세는 것은 **단추를 누른 횟수**입니다. 파일이 끝까지 받아졌는지는 브라우저가
  알려주지 않으므로 알 수 없습니다.
- 같은 브라우저에서 여러 번 눌러도 한 번만 세도록 `localStorage` 에 표시를
  남깁니다. 하지만 표시를 지우거나 다른 브라우저로 오면 다시 셉니다.
- 규칙이 '1씩 올리기' 만 허용하므로 임의의 숫자를 써 넣을 수는 없지만,
  마음먹고 반복해 올리는 것은 막지 못합니다.

즉 **대략의 눈금**이지 정확한 통계가 아닙니다. 정확한 수치가 필요하면
호스팅 쪽 접근 로그나 별도 분석 도구를 봐야 합니다.

숫자를 방문자에게 보이고 싶지 않다면 `tools/_appcount.py` 의 `show()` 에서
`el.hidden = false` 줄을 지우면 됩니다. 세는 것은 계속하고 표시만 안 합니다.

## 사진

첫 페이지 상단의 메인 이미지와 대표 명산 카드에 사진이 쓰입니다.

- `assets/photos/hero.jpg` → 메인 이미지
- `assets/photos/<슬러그>.jpg` → 글 상단 커버 사진 (1200px)
- `assets/photos/<슬러그>-t.jpg` → 목록 카드 썸네일 (480px). 없으면 원본을 씁니다.

파일을 넣으면 빌드가 자동으로 인식합니다.

**사진이 없는 산**은 `build.py` 의 `ridge_svg()` 가 그린 능선 일러스트가 들어갑니다.
산의 높이와 지역으로 모양·색이 정해지므로 산마다 다르고, 빌드할 때마다 같은 그림이 나옵니다.
사진인 척하는 이미지가 아니라 명백한 그래픽입니다. 해당 산의 사진 파일을 넣으면 자동으로 대체됩니다.

현재 상태: **실사진 92곳 / 일러스트 8곳**.

| 출처 | 장수 | 라이선스 |
|---|---|---|
| 위키미디어 공용 | 53 | 퍼블릭 도메인 · CC0 · CC BY · CC BY-SA |
| 한국관광공사 포토코리아 | 17 | 공공누리 제1유형 |
| 한국관광공사 TourAPI | 22 | 공공누리 제1유형 3, 제3유형 19 |

모두 저작자 표시가 의무라, 카드·글·첫 페이지 '사진 출처'에 촬영자와 라이선스를 표기합니다.
공공누리 제3유형은 '변경금지' 조건이 있어 파일은 웹 표시용 크기 축소만 하고
자르거나 편집하지 않습니다.

일러스트로 남은 8곳: 가리산(홍천) · 감악산(원주) · 구병산(보은) · 동악산(곡성) ·
백덕산 · 응봉산 · 칠갑산 · 황석산(함양). 세 곳 모두에서 산 풍경 사진을 찾지 못했거나,
있어도 시설물(레포츠파크·장승공원·수련원) 사진뿐이라 넣지 않았습니다.

### 직접 찍은 사진으로 바꾸기

1. `assets/photos/<슬러그>.jpg` 를 덮어씁니다.
2. `data/photos.json` 에서 해당 항목을 지우거나, `author` 를 본인 이름으로 고칩니다.
3. `python build.py`

### 자유 라이선스 사진 받기

**위키미디어 공용**

```
python tools/fetch_photos.py
```

`tools/fetch_photos.py` 의 `PICKS` 에 적힌 위키미디어 공용 파일만 받습니다.
퍼블릭 도메인 / CC0 / CC BY / CC BY-SA 가 아니면 자동으로 건너뜁니다.
받은 사진의 저작자와 라이선스는 첫 페이지 하단 '사진 출처'와 각 글 하단에 표기됩니다.

**한국관광공사** (공공데이터포털 인증키 필요 — 아래 두 API는 각각 활용신청해야 합니다)

*① 관광사진 갤러리* — 사진작가 작품 위주

```
python tools/check_key.py                     # .env 에 인증키가 들어갔는지 확인
python tools/fetch_kto_photos.py              # 후보 검색 → data/kto_candidates.json
python tools/fetch_kto_photos.py --download   # data/kto_picked.json 대로 내려받기
```

1. [공공데이터포털](https://www.data.go.kr/data/15101914/openapi.do)에서
   '한국관광공사_관광사진 정보_GW' 활용신청 (개발계정 자동승인, 일 1,000건)
2. 발급받은 인증키를 `blog/.env` 에 `TOUR_API_KEY=...` 형식으로 저장
3. 후보를 검색한 뒤 **촬영지까지 확인해서** `data/kto_picked.json` 에
   `"슬러그": "사진 제목"` 으로 적습니다. 같은 제목이 여러 장이면
   `{"title": "함백산", "id": "3583212"}` 처럼 콘텐츠 ID 로 특정합니다.

> 검색 결과에는 이름만 같은 다른 산(거창 감악산, 광양 구봉산)이나
> 시설 사진(천문대·레포츠파크·야영장)이 섞여 들어옵니다. 자동으로 1순위를
> 쓰지 말고 촬영지를 대조해서 고르세요.

*② TourAPI 관광정보* — 산이 '관광지'로 등록된 대표 이미지. 갤러리보다 커버리지가 넓다

```
python tools/fetch_tourapi_photos.py                        # 조사 → data/tour_candidates.json
python tools/fetch_tourapi_photos.py --download             # 제1유형만 내려받기
python tools/fetch_tourapi_photos.py --download --allow-type3   # 제3유형도 포함
```

[한국관광공사_국문 관광정보 서비스_GW](https://www.data.go.kr/data/15101578/openapi.do) 를
따로 활용신청해야 합니다(자동승인). 인증키는 같은 것을 씁니다.

주소(시군구)까지 함께 오므로 동명이산이 정확히 걸러집니다 — 가야산(서산)과 가야산(합천),
칠보산(괴산)과 북한 칠보산, 팔봉산(홍천)이 제대로 구분됩니다.
`data/tour_picked.json` 에 `"슬러그": 후보순번` 으로 다른 후보를 고르거나
`-1` 로 제외할 수 있습니다.

### 사진 용량 줄이기

```
python tools/optimize_photos.py
```

가로 폭 상한(원본 1200px, 썸네일 480px, 메인 1800px)으로 줄이고
progressive JPEG 로 다시 저장합니다. 원본보다 커지면 되돌리므로 여러 번 돌려도 안전합니다.

> **주의**: 다른 사이트(블랙야크 공식 홈페이지 포함)의 사진을 그대로 가져다 쓰면
> 저작권 침해가 됩니다. 직접 찍은 사진이나 자유 라이선스 사진만 넣으세요.

## 이어서 할 일 (2026-09-05 기준)

### 1. 직접 찍은 사진으로 교체 — 진행 중

`Desktop@대명산` 에 23개 산의 촬영 폴더가 있습니다. 가리산 하나만 반영했고
나머지 22곳이 남았습니다.

후보를 고르기 위한 컨택트 시트를 `_sheets/` 에 만들어 두었습니다
(폴더당 12장을 산행 순서대로 균등 추출). 시트를 보고 번호를 정한 뒤:

```
python tools/add_my_photo.py <슬러그> "<사진 경로>"
python build.py
```

시트를 다시 만들려면:

```
python tools/contact_sheet.py "<사진 폴더>" "_sheets/이름.jpg"
```

폴더 번호(블랙야크 공식 번호)와 이 사이트의 번호(가나다순)는 다릅니다.
`07_감악산` 폴더는 **파주** 감악산입니다(정상석 675m 양주시·파주시).

### 2. 등반 기록 — 연동하지 않음 (2026-09-06 결정)

한때 트래커 앱의 진행 파일을 읽어 '나의 등반기록' 페이지와 완등 배지를 넣었으나,
등반 기록은 사이트 밖에서 따로 관리하기로 하여 전부 걷어냈습니다.
`data/progress.json` 과 `tools/import_progress.py` 도 삭제했습니다.

이 사이트는 **산 정보(코스·난이도·인증장소·사진)만** 다룹니다.
다시 넣고 싶다면 `Desktop@대명산@대명산ac100_progress*.json` 을
읽어 붙이면 됩니다.

## 주의

- 코스 거리·소요시간·교통 정보는 작성 시점(2026-09-04) 기준의 공개 자료를 정리한 것입니다.
  산행 전 국립공원공단·지자체 공지로 재확인이 필요합니다.
- 위경도는 정상부 근사 좌표입니다.
- 사진은 위키미디어 공용(자유 라이선스)과 한국관광공사 포토코리아(공공누리 제1유형)에서 가져왔으며,
  저작자와 라이선스를 페이지에 표기합니다.
- `.env` 의 API 인증키는 `.gitignore` 로 저장소에서 제외됩니다. 절대 공개하지 마세요.
- 지도 경계 데이터 출처: Natural Earth 1:10m — 국가 외곽선(world-atlas 파생), 시도 경계(admin-1). 모두 public domain.

## 지도 다시 만들기

경계 데이터를 갱신하려면 원본을 받아 두 스크립트를 순서대로 실행합니다.

```
python tools/make_map.py <countries-10m.json>
python tools/make_provinces.py <ne_10m_admin_1_states_provinces.geojson>
```

`make_provinces.py` 는 `make_map.py` 가 저장해둔 투영 파라미터를 그대로 쓰므로
산 마커 좌표(`mountains.json` 의 x/y)는 다시 계산할 필요가 없습니다.
단, `make_map.py` 를 다시 돌려 투영이 바뀌면 마커도 재투영해야 합니다.

## 시도 색 구분

`build.py` 의 CSS에서 `.kmap .prov[data-region="강원"] path{fill:...}` 형태로
11개 지역의 색을 지정합니다. 지역 버튼을 누르면 해당 시도만 진하게 남고
나머지는 흐려집니다(`.kmap.filtered`).
