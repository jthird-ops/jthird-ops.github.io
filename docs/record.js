const done = M.filter(m=>m.done);
const redo = M.filter(m=>m.dates.length>1);
const peakM = done.reduce((a,m)=>m.h>a.h?m:a, done[0]);
$("#hStamp").textContent = done.length + "개 찍음.";
$("#sum").innerHTML = `
  <div class="s"><b>${done.length}<small>/${M.length}</small></b><span>완등 · ${Math.round(done.length/M.length*100)}%</span></div>
  <div class="s"><b>${fmt(peakM.h)}<small>m</small></b><span>가장 높이 오른 산</span><em>${peakM.name}</em></div>
  <div class="s"><b>${redo.length}<small>곳</small></b><span>두 번 이상 오른 산</span><em>${redo.map(m=>m.name).join(" · ")}</em></div>`;

/* ── stamp book: 10x10, grouped by region, tallest first within a region ── */
const order = REGIONS.flatMap(r=>M.filter(m=>m.region===r).sort((a,b)=>b.h-a.h));
let prev = "", k = 0, ri = -1;
$("#book").innerHTML = order.map(m=>{
  const first = m.region!==prev; if(first){ ri++; prev = m.region; }
  const last = m.dates[m.dates.length-1];
  const dt = m.done ? `<span class="dt">${last}${m.dates.length>1?` <b>×${m.dates.length}</b>`:""}</span>` : "";
  const style = m.done ? ` style="--k:${k++}"` : "";
  return `<a class="cell ${m.done?"done":"todo"}${ri%2?" alt":""}" role="listitem" data-r="${m.region}" href="list.html?no=${m.no}"${style}
    title="${m.name} · ${fmt(m.h)}m · ${m.region}${m.done?" · 완등 "+m.dates.join(", "):""}">
    ${first?`<span class="rtag">${m.region}</span>`:""}
    <span class="ht">${fmt(m.h)}</span>
    <span class="nm">${m.name}</span>${dt}</a>`;
}).join("");

/* region chips highlight one region on the board */
let focusR = "전체";
function renderChips(){
  const all = [["전체",done.length,M.length],...REGIONS.map(r=>{ const ms=M.filter(m=>m.region===r); return [r,ms.filter(m=>m.done).length,ms.length]; })];
  $("#rchips").innerHTML = all.map(([r,d,n])=>`<button class="chip" data-r="${r}" aria-pressed="${focusR===r}">${r}<i>${d}/${n}</i></button>`).join("");
}
function applyFocus(){
  document.querySelectorAll("#book .cell").forEach(c=>c.classList.toggle("dim", focusR!=="전체" && c.dataset.r!==focusR));
}
$("#rchips").addEventListener("click",e=>{ const b=e.target.closest(".chip"); if(!b) return; focusR=b.dataset.r; renderChips(); applyFocus(); });
renderChips();

/* ── rhythm timeline ── */
const hikes = [];
M.forEach(m=>m.dates.forEach((d,i)=>{ const [y,mo,da]=d.split(".").map(Number); hikes.push({m,key:(2000+y)*12+mo-1,da,rev:i>0,d}); }));
hikes.sort((a,b)=>a.key-b.key||a.da-b.da);
const now = new Date();
const k0 = hikes[0].key, k1 = Math.max(hikes[hikes.length-1].key, now.getFullYear()*12+now.getMonth());
const N = k1-k0+1;
const months = Array.from({length:N},(_,i)=>({key:k0+i,hs:hikes.filter(h=>h.key===k0+i)}));
const maxC = Math.max(...months.map(x=>x.hs.length));
let cum = 0, cells = "";
months.forEach((x,i)=>{
  const col = i+2, y = Math.floor(x.key/12), mo = x.key%12+1;
  cum += x.hs.filter(h=>!h.rev).length;
  cells += `<div class="stack" style="grid-column:${col};grid-row:1">${x.hs.map(h=>`<a class="dot${h.rev?" rev":""}" href="list.html?no=${h.m.no}" title="${h.m.name} · 20${h.d}${h.rev?" (다시 오름)":""}" aria-label="${h.m.name} 20${h.d}"></a>`).join("")}</div>`;
  cells += `<div class="ml" style="grid-column:${col};grid-row:2">${mo}</div>`;
  cells += `<div class="cum" style="grid-column:${col};grid-row:4">${cum}</div>`;
});
/* year bands */
let ys = 0;
for(let i=1;i<=N;i++){
  const y = Math.floor((k0+i-1)/12), yp = Math.floor((k0+i)/12);
  if(i===N || yp!==y){ cells += `<div class="yr" style="grid-column:${ys+2} / ${i+2};grid-row:3">${y}</div>`; ys = i; }
}
/* quiet stretches (3+ months without a record) */
let run = null;
months.forEach((x,i)=>{
  if(x.hs.length===0){ run ? run.e = i : run = {s:i,e:i}; }
  if(x.hs.length>0 || i===N-1){ if(run && run.e-run.s>=2) cells += `<div class="gap" style="grid-column:${run.s+2} / ${run.e+3};grid-row:1">기록 없음</div>`; run = null; }
});
const tl = $("#tl");
tl.style.setProperty("--n", N);
tl.style.setProperty("--sh", (maxC*21)+"px");
tl.innerHTML = cells + `<div class="rowlab" style="grid-column:1;grid-row:4">누적</div><div class="rowlab" style="grid-column:1;grid-row:2">월</div>`;
const peak = months.filter(x=>x.hs.length===maxC).map(x=>`${Math.floor(x.key/12)}년 ${x.key%12+1}월`);
const f = hikes[0];
$("#tlLede").textContent = `${Math.floor(f.key/12)}년 ${f.key%12+1}월부터 모두 ${hikes.length}번 올랐고, 서로 다른 산은 ${done.length}개입니다. 가장 많이 오른 달은 ${peak.join("·")}(${maxC}번)입니다.`;
