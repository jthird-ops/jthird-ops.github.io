const params = new URLSearchParams(location.search);
const state = {region: REGIONS.includes(params.get("r")) ? params.get("r") : "전체", stat:"all", sort:"no", q:""};
const mtURL = m => "mt-"+String(m.no).padStart(3,"0")+".html";
const grid = $("#grid");
const PLACEHOLDER = '<svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M2 26 12 9l6 10 3-4 9 11z"/></svg>';
function thumb(m){
  const img = m.photo ? `<img src="${m.photo}" alt="${m.name} 대표사진" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.parentNode.classList.add('ph');this.remove()">` : "";
  return `<span class="thumb${m.photo?"":" ph"}">${img}${PLACEHOLDER}</span>`;
}
function renderChips(){
  const all = [["전체",M.length],...REGIONS.map(r=>[r,M.filter(m=>m.region===r).length])];
  $("#chips").innerHTML = all.map(([r,c])=>`<button class="chip" data-r="${r}" aria-pressed="${state.region===r}">${r}<i>${c}</i></button>`).join("");
}
function card(m){
  const date = m.done ? `<span class="badge">${CHECK}완등 ${m.dates.join(" · ")}</span>` : "<span></span>";
  return `<article class="card${m.done?' done':''}" id="m${m.no}" data-no="${m.no}">
    <div class="top"><span class="no">${String(m.no).padStart(3,"0")}</span><span class="rg">${m.region}</span></div>
    <div class="mid">
      <div class="t">
        <h3>${m.name}</h3>
        <div class="hrow"><span class="h">${fmt(m.h)}m</span><span class="meter"><i style="width:${(m.h/MAXH*100).toFixed(1)}%"></i></span></div>
      </div>
      ${thumb(m)}
    </div>
    <p>${m.note}</p>
    <div class="foot">${date}<span class="more">코스 보기 ${ARROW}</span></div>
    <a class="cover" href="${mtURL(m)}" aria-label="${m.name} 상세 페이지"></a>
  </article>`;
}
function render(){
  let list = M.filter(m=>
    (state.region==="전체"||m.region===state.region) &&
    (state.stat==="all"||(state.stat==="done")===m.done) &&
    (!state.q || m.name.replace(/\s/g,"").includes(state.q.replace(/\s/g,""))));
  if(state.sort==="h") list.sort((a,b)=>b.h-a.h);
  grid.innerHTML = list.map(card).join("");
  const d = list.filter(m=>m.done).length;
  $("#count").innerHTML = `<b>${list.length}</b>개의 산 · 완등 <b>${d}</b> · 남은 산 <b>${list.length-d}</b>`;
  $("#empty").hidden = list.length>0;
}
function syncSeg(sel,v){ document.querySelectorAll(sel+" button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.v===v)); }
$("#chips").addEventListener("click",e=>{ const b=e.target.closest(".chip"); if(!b) return; state.region=b.dataset.r; renderChips(); render(); });
$("#stat").addEventListener("click",e=>{ const b=e.target.closest("button"); if(!b) return; state.stat=b.dataset.v; syncSeg("#stat",state.stat); render(); });
$("#sort").addEventListener("click",e=>{ const b=e.target.closest("button"); if(!b) return; state.sort=b.dataset.v; syncSeg("#sort",state.sort); render(); });
$("#q").addEventListener("input",e=>{ state.q=e.target.value.trim(); render(); });
renderChips(); render();

/* deep link from the ridge: list.html?no=53 */
const want = +params.get("no");
if(want>=1 && want<=M.length){
  const el = $("#m"+want);
  if(el){
    requestAnimationFrame(()=>{
      el.scrollIntoView({behavior:"auto",block:"center"});
      el.classList.add("flash"); setTimeout(()=>el.classList.remove("flash"),2400);
    });
  }
}
