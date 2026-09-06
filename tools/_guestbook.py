# -*- coding: utf-8 -*-
"""방명록 페이지와 그 스크립트를 만든다.

정적 사이트라 글을 저장할 곳이 없어 Firebase Firestore 를 쓴다. 설정값은
data/firebase.json 에 두고, 없으면 페이지가 '설정 전' 안내를 보여준다.
설정 없이 빌드해도 사이트는 멀쩡히 만들어진다.

Firestore 규칙은 README 의 '방명록' 절에 있다. 규칙 없이 열면 누구나 남의
글을 지울 수 있으니 반드시 넣어야 한다.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAME_MAX, MSG_MAX = 20, 500


def config():
    p = os.path.join(ROOT, 'data/firebase.json')
    if not os.path.exists(p):
        return None
    cfg = json.load(open(p, encoding='utf-8'))
    need = ('apiKey', 'projectId', 'appId')
    if not all(cfg.get(k) for k in need):
        return None
    return cfg


def body(cfg):
    if cfg:
        form = f"""
  <form id="gb-form" class="gb-form" autocomplete="off">
    <div class="gb-row">
      <input id="gb-name" name="name" type="text" maxlength="{NAME_MAX}"
             placeholder="이름 또는 별명" required>
      <!-- 사람에게는 안 보인다. 자동 프로그램이 채우면 보내지 않는다 -->
      <input id="gb-trap" name="website" type="text" tabindex="-1"
             aria-hidden="true" autocomplete="off">
    </div>
    <textarea id="gb-msg" name="message" maxlength="{MSG_MAX}" rows="4"
              placeholder="다녀오신 산, 남기고 싶은 말을 적어주세요." required></textarea>
    <div class="gb-bar">
      <span class="gb-count"><b id="gb-left">{MSG_MAX}</b>자 남음</span>
      <button id="gb-send" type="submit">남기기</button>
    </div>
    <p id="gb-msgbox" class="gb-msgbox" hidden></p>
  </form>
  <div id="gb-list" class="gb-list"><p class="gb-loading">불러오는 중…</p></div>"""
    else:
        form = """
  <div class="gb-setup">
    <b>아직 준비 중입니다.</b>
    <p>방명록을 쓰려면 Firebase 설정이 필요합니다.
       <code>blog/data/firebase.json</code> 을 만들고 다시 빌드하면 이 자리에
       방명록이 나타납니다. 만드는 방법은 <code>README.md</code> 의 '방명록' 절에
       적어 두었습니다.</p>
  </div>"""

    return f"""
<main class="wrap gb-wrap">
  <h1>방명록</h1>
  <p class="sub">산에서 만난 것, 이 기록에 보태고 싶은 것을 남겨주세요.
     남긴 글은 모두에게 보입니다. 연락처나 개인정보는 적지 마세요.</p>
  {form}
</main>"""


def js(cfg):
    """Firebase 를 붙이는 스크립트. 설정이 없으면 빈 문자열."""
    if not cfg:
        return ''
    return f"""<script type="module">
import {{ initializeApp, getApps, getApp }} from
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import {{ getFirestore, collection, addDoc, getDocs, query, orderBy, limit,
         serverTimestamp }} from
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';

const cfg = {json.dumps(cfg, ensure_ascii=False)};
const db = getFirestore(getApps().length ? getApp() : initializeApp(cfg));
const listEl = document.getElementById('gb-list');
const form = document.getElementById('gb-form');
const box = document.getElementById('gb-msgbox');
const left = document.getElementById('gb-left');
const msg = document.getElementById('gb-msg');
const send = document.getElementById('gb-send');

function esc(s) {{
  return String(s).replace(/[&<>"']/g, c =>
    ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]);
}}
function when(ts) {{
  if (!ts || !ts.toDate) return '';
  const d = ts.toDate();
  return `${{d.getFullYear()}}.${{String(d.getMonth()+1).padStart(2,'0')}}`
       + `.${{String(d.getDate()).padStart(2,'0')}}`;
}}
function say(text, bad) {{
  box.textContent = text;
  box.className = 'gb-msgbox' + (bad ? ' bad' : ' ok');
  box.hidden = false;
}}

// 설정이 틀렸거나 망이 막히면 요청이 오류 없이 멈춘다.
// 그대로 두면 '불러오는 중…' 이 영영 남으므로 시간을 끊는다.
function within(ms, work) {{
  return Promise.race([work, new Promise((_, no) =>
    setTimeout(() => no(new Error('시간 초과')), ms))]);
}}

async function load() {{
  try {{
    const snap = await within(12000, getDocs(query(collection(db, 'guestbook'),
      orderBy('createdAt', 'desc'), limit(200))));
    if (snap.empty) {{
      listEl.innerHTML = '<p class="gb-empty">아직 남겨진 글이 없습니다. '
        + '첫 글을 남겨주세요.</p>';
      return;
    }}
    listEl.innerHTML = snap.docs.map(d => {{
      const v = d.data();
      return '<article class="gb-item"><header><b>' + esc(v.name || '익명')
        + '</b><span>' + when(v.createdAt) + '</span></header><p>'
        + esc(v.message || '') + '</p></article>';
    }}).join('');
  }} catch (err) {{
    listEl.innerHTML = '<p class="gb-empty">방명록을 불러오지 못했습니다. '
      + '잠시 뒤 새로고침해 주세요.</p>';
    console.error(err);
  }}
}}

msg.addEventListener('input', () => {{ left.textContent = {MSG_MAX} - msg.value.length; }});

form.addEventListener('submit', async (ev) => {{
  ev.preventDefault();
  if (document.getElementById('gb-trap').value) return;   // 자동 프로그램
  const name = document.getElementById('gb-name').value.trim();
  const text = msg.value.trim();
  if (!name || !text) return say('이름과 내용을 모두 적어주세요.', true);

  send.disabled = true; send.textContent = '보내는 중…';
  try {{
    await within(12000, addDoc(collection(db, 'guestbook'),
      {{ name: name.slice(0, {NAME_MAX}), message: text.slice(0, {MSG_MAX}),
         createdAt: serverTimestamp() }}));
    form.reset(); left.textContent = {MSG_MAX};
    say('남겨주셔서 고맙습니다.', false);
    load();
  }} catch (err) {{
    say('글을 남기지 못했습니다. 잠시 뒤 다시 시도해 주세요.', true);
    console.error(err);
  }} finally {{
    send.disabled = false; send.textContent = '남기기';
  }}
}});

load();
</script>"""


CSS = """
.gb-wrap{max-width:760px;padding-top:34px}
.gb-wrap h1{margin:0 0 8px;font-size:28px}
.gb-wrap .sub{margin:0 0 26px;color:var(--sub);font-size:14.5px;line-height:1.75}
.gb-form{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:18px;margin-bottom:28px}
.gb-form input[type=text],.gb-form textarea{width:100%;border:1px solid var(--line);
  border-radius:9px;padding:10px 12px;font:inherit;font-size:14.5px;background:#fff;
  color:var(--ink)}
.gb-form input:focus,.gb-form textarea:focus{outline:2px solid var(--green);
  outline-offset:-1px;border-color:var(--green)}
.gb-row{margin-bottom:10px;max-width:260px}
#gb-trap{position:absolute;left:-9999px;width:1px;height:1px}
.gb-form textarea{resize:vertical;line-height:1.7}
.gb-bar{display:flex;align-items:center;justify-content:space-between;margin-top:12px}
.gb-count{font-size:12.5px;color:var(--sub)}
.gb-bar button{border:none;background:var(--green);color:#fff;font:inherit;
  font-size:14px;font-weight:650;padding:10px 22px;border-radius:999px;cursor:pointer}
.gb-bar button:hover{background:#188044}
.gb-bar button:disabled{background:#b7c2ba;cursor:default}
.gb-msgbox{margin:12px 0 0;font-size:13.5px;padding:9px 12px;border-radius:8px}
.gb-msgbox.ok{background:rgba(46,160,102,.1);color:var(--green)}
.gb-msgbox.bad{background:#fdecec;color:#b53b3b}
.gb-list{display:grid;gap:12px}
.gb-item{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:14px 16px}
.gb-item header{display:flex;justify-content:space-between;align-items:baseline;
  gap:10px;margin-bottom:7px}
.gb-item header b{font-size:14.5px}
.gb-item header span{font-size:12.5px;color:var(--sub)}
.gb-item p{margin:0;font-size:14.5px;line-height:1.75;white-space:pre-wrap;
  overflow-wrap:anywhere}
.gb-loading,.gb-empty{color:var(--sub);font-size:14px;text-align:center;padding:26px 0}
.gb-setup{background:#fdf3e2;border-radius:12px;padding:18px 20px;color:#8a5a0c}
.gb-setup b{display:block;margin-bottom:6px}
.gb-setup p{margin:0;font-size:14px;line-height:1.75}
.gb-setup code{background:rgba(0,0,0,.06);padding:1px 6px;border-radius:5px}
"""
