
(function () {
  // 등산지도: 누르면 화면 가득 띄우고, 한 번 더 누르면 원본 크기로 키워 끌어서 본다
  document.querySelectorAll('.tmap').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var box = document.createElement('div');
      box.className = 'zoombox';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
      var bar = document.createElement('div'); bar.className = 'zoombox-bar';
      var cap = document.createElement('span'); cap.textContent = btn.dataset.cap + ' · 지도를 누르면 더 크게';
      var x = document.createElement('button'); x.type = 'button'; x.textContent = '닫기';
      bar.appendChild(cap); bar.appendChild(x);
      var sc = document.createElement('div'); sc.className = 'zoombox-scroll';
      var im = document.createElement('img'); im.src = btn.dataset.zoom; im.alt = btn.dataset.cap;
      sc.appendChild(im); box.appendChild(bar); box.appendChild(sc);
      var close = function () {
        box.remove(); document.removeEventListener('keydown', onKey);
        document.documentElement.style.overflow = ''; btn.focus();
      };
      var onKey = function (ev) { if (ev.key === 'Escape') close(); };
      im.addEventListener('click', function (ev) { ev.stopPropagation(); box.classList.toggle('big'); });
      bar.addEventListener('click', function (ev) { ev.stopPropagation(); });
      x.addEventListener('click', close);
      box.addEventListener('click', close);
      document.addEventListener('keydown', onKey);
      document.documentElement.style.overflow = 'hidden';
      document.body.appendChild(box); x.focus();
    });
  });
})();

(function () {
  // 개별 산 페이지 미니맵: 그 산이 속한 시도를 강조한다
  document.querySelectorAll('.kmap.zoom').forEach(function (svg) {
    var r = svg.dataset.region;
    svg.querySelectorAll('.prov').forEach(function (g) {
      if (g.dataset.region === r) g.classList.add('on');
    });
  });
})();

(function () {
  // 좁은 화면의 상단 메뉴 띠 — 끝까지 넘기면 오른쪽 흐림을 없앤다
  var nav = document.querySelector('header.site nav');
  if (nav) {
    var mark = function () {
      var end = nav.scrollLeft + nav.clientWidth >= nav.scrollWidth - 2;
      nav.classList.toggle('at-end', end);
    };
    nav.addEventListener('scroll', mark, { passive: true });
    window.addEventListener('resize', mark);
    mark();
  }
})();

(function () {
  // 첫 페이지 4개 메뉴 — 누르면 해당 내용만 보여준다
  var menu = document.getElementById('menu');
  if (!menu) return;
  var cards = Array.prototype.slice.call(menu.querySelectorAll('.menu-card'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.tabpanel'));

  function show(id, scroll) {
    if (!document.getElementById(id)) id = 'tab-list';
    panels.forEach(function (p) { p.hidden = p.id !== id; });
    cards.forEach(function (c) { c.classList.toggle('active', c.dataset.tab === id); });
    if (history.replaceState) history.replaceState(null, '', '#' + id);
    if (scroll) {
      // 넓은 화면에서는 메뉴가 한 줄이라 메뉴 위로 가면 내용까지 함께 보인다.
      // 좁은 화면에서는 카드가 세로로 쌓여 메뉴만으로 한 화면을 넘기므로,
      // 그때는 고른 내용으로 바로 내려간다.
      var panel = document.getElementById(id);
      var tall = menu.getBoundingClientRect().height > window.innerHeight * 0.55;
      var target = (tall && panel) ? panel : menu;
      var hdr = document.querySelector('header.site');
      var off = (hdr ? hdr.getBoundingClientRect().height : 60) + 8;
      var top = target.getBoundingClientRect().top + window.pageYOffset - off;
      window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    }
  }

  cards.forEach(function (c) {
    c.addEventListener('click', function () { show(c.dataset.tab, true); });
  });
  window.showTab = show;          // '지역별로 한눈에'에서 목록 탭으로 넘어갈 때 쓴다
  // 다른 페이지에서 #tab-map 처럼 들어온 경우도 받아준다
  window.addEventListener('hashchange', function () {
    show(location.hash.slice(1), true);
  });
  show(location.hash.slice(1) || 'tab-list', false);
})();

(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var countEl = document.getElementById('count');
  var emptyEl = document.getElementById('empty');
  var region = '전체';

  function apply() {
    var term = q.value.trim().toLowerCase();
    var n = 0;
    cards.forEach(function (c) {
      var okR = region === '전체' || c.dataset.region === region;
      var okQ = !term || c.dataset.name.toLowerCase().indexOf(term) !== -1;
      var show = okR && okQ;
      c.hidden = !show;
      if (show) n++;
    });
    countEl.textContent = n + '개 표시 중' + (region === '전체' ? '' : ' · ' + region);
    emptyEl.hidden = n !== 0;
  }

  // 지역 버튼 선택을 지도에도 반영한다
  var kmap = document.getElementById('kmap');
  function paintMap() {
    if (!kmap) return;
    var all = region === '전체';
    kmap.classList.toggle('filtered', !all);
    ['.prov', '.plabel', '.pins a'].forEach(function (sel) {
      kmap.querySelectorAll(sel).forEach(function (el) {
        el.classList.toggle('on', all || el.dataset.region === region);
      });
    });
  }

  // 지역을 고르면 그 시도 쪽으로 지도를 확대한다 ('전체'면 원래대로)
  var vb0 = kmap ? kmap.getAttribute('viewBox').split(' ').map(Number) : null, vbNow = vb0, anim = 0;
  function setVB(v) {
    vbNow = v;
    kmap.setAttribute('viewBox', v.map(function (n) { return n.toFixed(1); }).join(' '));
    var s = Math.max(0.3, Math.min(1, 1.6 * v[2] / vb0[2]));   // 확대할수록 점·글자를 줄여 화면 크기를 비슷하게
    kmap.style.setProperty('--s', s.toFixed(3));
    kmap.querySelectorAll('.pins circle').forEach(function (c) { c.setAttribute('r', (14 * s).toFixed(1)); });
  }
  function zoomMap() {
    if (!kmap || !vb0) return;
    var to = vb0.slice();
    if (region !== '전체') {
      var x1 = 1e9, y1 = 1e9, x2 = -1e9, y2 = -1e9;
      kmap.querySelectorAll('.prov.on, .pins a.on circle').forEach(function (el) {
        try { var b = el.getBBox(); } catch (err) { return; }
        if (!b.width && !b.height && el.tagName !== 'circle') return;
        x1 = Math.min(x1, b.x); y1 = Math.min(y1, b.y);
        x2 = Math.max(x2, b.x + b.width); y2 = Math.max(y2, b.y + b.height);
      });
      if (x2 > x1) {
        var w = x2 - x1, h = y2 - y1, p = Math.max(w, h) * 0.12 + 30;
        to = [x1 - p, y1 - p, w + 2 * p, h + 2 * p];
      }
    }
    var from = vbNow.slice(), t0 = performance.now(), id = ++anim;
    (function step(t) {
      if (id !== anim) return;
      var k = Math.min(1, (t - t0) / 550), q = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      setVB(from.map(function (a, i) { return a + (to[i] - a) * q; }));
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }
  // 지도 위 시도를 직접 눌러도 그 지역으로 확대된다. 확대된 지역을 다시 누르면 전체로.
  if (kmap) kmap.querySelectorAll('.prov').forEach(function (g) {
    g.style.cursor = 'pointer';
    g.addEventListener('click', function () { pick(region === g.dataset.region ? '전체' : g.dataset.region); });
  });

  function pick(r) {
    region = r;
    chips.forEach(function (x) {
      x.classList.toggle('active', x.dataset.region === region);
    });
    apply();
    paintMap();
    zoomMap();
  }

  // '지역별로 한눈에'에서 지역 이름을 누르면 그 지역만 걸러 목록 탭으로 넘어간다
  document.querySelectorAll('.region-pick').forEach(function (b) {
    b.addEventListener('click', function () {
      pick(b.dataset.region);
      if (window.showTab) window.showTab('tab-list', true);
    });
  });

  q.addEventListener('input', apply);
  chips.forEach(function (ch) {
    // 목록 탭과 지도 탭에 같은 칩이 한 벌씩 있으므로 pick() 이 둘 다 맞춰준다
    ch.addEventListener('click', function () { pick(ch.dataset.region); });
  });
  apply();
  paintMap();
})();
