const doneList = M.filter(m=>m.done);
$("#sDone").innerHTML = doneList.length + "<small>/100</small>";
$("#sAlt").innerHTML = (doneList.reduce((a,m)=>a+m.h,0)/1000).toFixed(1) + "<small>km</small>";
(function(){
  /* seamless loop: two copies of the clip crossfade before the end */
  const A=$("#bgv"), B=$("#bgv2"), FADE=1.6;
  let cur=A, nxt=B, ready=false, swapping=false;
  function start(){ if(ready) return; ready=true; A.classList.add("on"); A.play().catch(()=>{}); }
  A.addEventListener("loadeddata",start);A.addEventListener("playing",()=>{ if(B.preload!=="auto"){ B.preload="auto"; B.load(); } },{once:true}); if(A.readyState>=2) start();
    function swap(){
    swapping=true;
    nxt.currentTime=0;
    nxt.play().catch(()=>{});
    nxt.classList.add("on");A.classList.add("sw");
    cur.classList.remove("on");
    const old=cur; cur=nxt; nxt=old;
    setTimeout(()=>{ nxt.pause(); nxt.currentTime=0; swapping=false; }, FADE*1000+200);
  }
  function tick(){
    if(ready && !swapping && cur.duration && !cur.paused && cur.duration-cur.currentTime<=FADE) swap();
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  /* low-power / autoplay-blocked phones: start on first touch */
  ["touchstart","click","scroll"].forEach(e=>addEventListener(e,()=>{ if(cur.paused) cur.play().catch(()=>{}); },{once:true,passive:true}));
  document.addEventListener("visibilitychange",()=>{ if(!document.hidden && cur.paused) cur.play().catch(()=>{}); });
  /* autoplay blocked (low-power mode): drift the still frame until the video can play */
  const hero=document.querySelector(".hero");
  [A,B].forEach(v=>v.addEventListener("playing",()=>hero.classList.remove("kb")));
  setTimeout(()=>{ if(cur.paused) hero.classList.add("kb"); },1200);
})();


/* background music (bgm.mp3, loop, fade-in) */
(function(){
  const btn=document.getElementById("snd"); if(!btn) return;
  const au=new Audio("bgm.mp3"); au.loop=true; au.preload="none"; au.volume=0;
  const VOL=.5; let on=false, fade;
  function ramp(to,done){ clearInterval(fade); fade=setInterval(()=>{ const d=to-au.volume; if(Math.abs(d)<.03){ au.volume=to; clearInterval(fade); done&&done(); } else au.volume=Math.max(0,Math.min(1,au.volume+Math.sign(d)*.03)); },60); }
  function ui(){btn.classList.toggle("on",on);btn.setAttribute("aria-pressed",on);btn.querySelector("span:last-child").textContent=on?"음악 끄기":"음악 켜기";}
  function start(){ on=true; ui(); const r=au.play(); if(r&&r.catch) r.catch(()=>{ on=false; ui(); }); ramp(VOL); }
  function stop(){ on=false; ui(); ramp(0,()=>au.pause()); }
  btn.addEventListener("click",()=>{ try{localStorage.setItem("snd",on?"0":"1")}catch(e){} on?stop():start(); });
  let pref="1"; try{pref=localStorage.getItem("snd")||"1"}catch(e){}
  if(pref==="1"){ ["pointerdown","keydown"].forEach(e=>addEventListener(e,ev=>{ if(!on&&!(ev.target.closest&&ev.target.closest("#snd"))) start(); },{once:true,passive:true})); }
  document.addEventListener("visibilitychange",()=>{ if(!on) return; document.hidden?au.pause():au.play().catch(()=>{}); });
})();
