const doneList = M.filter(m=>m.done);
$("#sDone").innerHTML = doneList.length + "<small>/100</small>";
$("#sAlt").innerHTML = (doneList.reduce((a,m)=>a+m.h,0)/1000).toFixed(1) + "<small>km</small>";
(function(){
  /* seamless loop: two copies of the clip crossfade before the end */
  const A=$("#bgv"), B=$("#bgv2"), FADE=1.6;
  let cur=A, nxt=B, ready=false, swapping=false;
  function start(){ if(ready) return; ready=true; A.classList.add("on"); if(!reduceMotion) A.play().catch(()=>{}); }
  A.addEventListener("loadeddata",start); if(A.readyState>=2) start();
  if(reduceMotion){ A.removeAttribute("loop"); return; }
  function swap(){
    swapping=true;
    nxt.currentTime=0;
    nxt.play().catch(()=>{});
    nxt.classList.add("on");
    cur.classList.remove("on");
    const old=cur; cur=nxt; nxt=old;
    setTimeout(()=>{ nxt.pause(); nxt.currentTime=0; swapping=false; }, FADE*1000+200);
  }
  function tick(){
    if(ready && !swapping && cur.duration && !cur.paused && cur.duration-cur.currentTime<=FADE) swap();
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  document.addEventListener("visibilitychange",()=>{ if(!document.hidden && cur.paused) cur.play().catch(()=>{}); });
})();

