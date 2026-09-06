
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
      var top = menu.getBoundingClientRect().top + window.pageYOffset - 70;
      window.scrollTo({ top: top, behavior: 'smooth' });
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

  function pick(r) {
    region = r;
    chips.forEach(function (x) {
      x.classList.toggle('active', x.dataset.region === region);
    });
    apply();
    paintMap();
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
