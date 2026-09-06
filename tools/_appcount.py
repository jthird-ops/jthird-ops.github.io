# -*- coding: utf-8 -*-
"""어플 내려받기 횟수를 센다.

방명록과 같은 Firestore 를 쓴다. 문서 하나(stats/appDownloads)의 count 를
1씩 올린다. 설정이 없으면 아무것도 넣지 않아 페이지가 그대로 동작한다.

세는 것은 '내려받기 단추를 누른 횟수' 다. 실제로 파일이 다 받아졌는지,
누른 사람이 몇 명인지는 브라우저가 알려주지 않는다. 대략의 눈금으로만 쓴다.
같은 브라우저에서 여러 번 눌러도 한 번만 세도록 표시를 남긴다.
"""
import json

DOC = 'stats/appDownloads'
SEEN = 'BAC100_APP_DOWNLOADED'      # 이 브라우저에서 이미 셌는지


def html():
    """카운터 자리. 숫자를 받기 전에는 아무것도 보이지 않는다."""
    return '<p class="app-count" id="app-count" hidden></p>'


def js(cfg):
    if not cfg:
        return ''
    return f"""<script type="module">
import {{ initializeApp, getApps, getApp }} from
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import {{ getFirestore, doc, getDoc, setDoc, increment }} from
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';

// 같은 페이지의 다른 스크립트가 이미 초기화했을 수 있다
const cfg = {json.dumps(cfg, ensure_ascii=False)};
const db = getFirestore(getApps().length ? getApp() : initializeApp(cfg));
const ref = doc(db, '{DOC}');
const el = document.getElementById('app-count');

function show(n) {{
  if (!el || !(n > 0)) return;
  el.textContent = '지금까지 ' + n.toLocaleString('ko-KR') + '번 내려받았습니다.';
  el.hidden = false;
}}

async function read() {{
  try {{
    const snap = await getDoc(ref);
    if (snap.exists()) show(snap.data().count);
  }} catch (err) {{
    /* 숫자를 못 읽어도 내려받기는 되어야 하므로 조용히 넘어간다 */
  }}
}}

async function bump() {{
  // 같은 브라우저에서 여러 번 눌러도 한 번만 센다
  try {{
    if (localStorage.getItem('{SEEN}')) return;
    localStorage.setItem('{SEEN}', '1');
  }} catch (err) {{ /* 저장이 막힌 브라우저면 그냥 센다 */ }}
  try {{
    await setDoc(ref, {{ count: increment(1) }}, {{ merge: true }});
    read();
  }} catch (err) {{
    /* 세는 데 실패해도 파일은 이미 받아지고 있다 */
  }}
}}

const btn = document.querySelector('.app-cta a[download]');
if (btn) btn.addEventListener('click', bump);
read();
</script>"""


CSS = """
.app-count{margin:10px 0 0;text-align:center;font-size:12.5px;color:var(--green);
  font-weight:640}
"""
