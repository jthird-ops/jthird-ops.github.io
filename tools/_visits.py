# -*- coding: utf-8 -*-
"""방문자 수를 세어 푸터에 보여준다.

방명록·다운로드 카운터와 같은 Firestore 를 쓴다. 문서 두 개를 올린다.

  stats/visits            전체 누적
  stats/visits-YYYY-MM-DD 그날치

같은 브라우저에서 하루에 한 번만 센다. 그래서 '방문 횟수' 가 아니라
'그날 다녀간 브라우저 수' 에 가깝다. 정확한 통계가 아니라 대략의 눈금이다.

보안 규칙은 stats/{doc} 전체에 걸려 있어 문서가 늘어도 손댈 것이 없다.
"""
import json

SEEN = 'BAC100_VISIT'          # 마지막으로 센 날짜를 적어 둔다


def html():
    """푸터에 들어갈 자리. 숫자를 받기 전에는 보이지 않는다."""
    return '<p class="visits" id="visits" hidden></p>'


def js(cfg):
    if not cfg:
        return ''
    return f"""<script type="module">
import {{ initializeApp, getApps, getApp }} from
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import {{ getFirestore, doc, getDoc, setDoc, increment }} from
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';

// 한 페이지에 Firebase 스크립트가 둘 이상 있을 수 있다(첫 화면은 방문자 수와
// 내려받기 수를 함께 쓴다). 두 번 초기화하면 오류가 나므로 이미 있으면 쓴다.
const cfg = {json.dumps(cfg, ensure_ascii=False)};
const db = getFirestore(getApps().length ? getApp() : initializeApp(cfg));

const el = document.getElementById('visits');
const today = new Date().toLocaleDateString('sv-SE');   // YYYY-MM-DD (한국 시각 기준 지역설정)
const totalRef = doc(db, 'stats/visits');
const dayRef = doc(db, 'stats/visits-' + today);

function show(day, total) {{
  if (!el || !(total > 0)) return;
  const n = (v) => v.toLocaleString('ko-KR');
  el.textContent = (day > 0 ? '오늘 ' + n(day) + '명 · ' : '') + '전체 ' + n(total) + '명이 다녀갔습니다';
  el.hidden = false;
}}

async function read() {{
  try {{
    const [t, d] = await Promise.all([getDoc(totalRef), getDoc(dayRef)]);
    show(d.exists() ? d.data().count : 0, t.exists() ? t.data().count : 0);
  }} catch (err) {{ /* 숫자를 못 읽어도 페이지는 멀쩡해야 한다 */ }}
}}

async function count() {{
  let already = false;
  try {{
    already = localStorage.getItem('{SEEN}') === today;   // 하루 한 번만
    if (!already) localStorage.setItem('{SEEN}', today);
  }} catch (err) {{ /* 저장이 막힌 브라우저면 그냥 센다 */ }}
  if (already) return read();
  try {{
    await Promise.all([
      setDoc(totalRef, {{ count: increment(1) }}, {{ merge: true }}),
      setDoc(dayRef, {{ count: increment(1) }}, {{ merge: true }}),
    ]);
  }} catch (err) {{ /* 세는 데 실패해도 그만 */ }}
  read();
}}

count();
</script>"""


CSS = """
.visits{margin:10px 0 0!important;font-size:12px;color:var(--sub);opacity:.9}
"""
