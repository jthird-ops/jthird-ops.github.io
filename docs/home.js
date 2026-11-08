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
})();


/* ambient music: synthesized soft pad (Web Audio, no files) */
(function(){
  const btn=document.getElementById("snd"); if(!btn) return;
  let ctx,master,timer,on=false,step=0;
  const CH=[[220,261.63,329.63,392],[174.61,220,261.63,329.63],[196,246.94,293.66,392],[164.81,207.65,246.94,329.63]];
  function note(f,t,d){
    const o=ctx.createOscillator(),g=ctx.createGain();
    o.type="sine";o.frequency.value=f;o.detune.value=(Math.random()-.5)*8;
    g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.05,t+d*.35);g.gain.linearRampToValueAtTime(0,t+d);
    o.connect(g);g.connect(master);o.start(t);o.stop(t+d+.1);
  }
  function bar(){
    const t=ctx.currentTime,c=CH[step%CH.length],d=8;
    c.forEach((f,i)=>note(f,t+i*.4,d)); note(c[0]/2,t,d);
    if(step%2===0) note(c[3]*2,t+3,4);
    step++;
  }
  function start(){
    if(!ctx){
      ctx=new (window.AudioContext||window.webkitAudioContext)();
      master=ctx.createGain();master.gain.value=0;
      const lp=ctx.createBiquadFilter();lp.type="lowpass";lp.frequency.value=1400;
      const dl=ctx.createDelay(1);dl.delayTime.value=.45;const fb=ctx.createGain();fb.gain.value=.45;
      dl.connect(fb);fb.connect(dl);
      master.connect(lp);lp.connect(ctx.destination);lp.connect(dl);dl.connect(ctx.destination);
    }
    ctx.resume();
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.linearRampToValueAtTime(1,ctx.currentTime+3);
    bar();timer=setInterval(bar,7000);on=true;ui();
  }
  function stop(){
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.linearRampToValueAtTime(0,ctx.currentTime+1);
    clearInterval(timer);setTimeout(()=>{ if(!on) ctx.suspend(); },1200);on=false;ui();
  }
  function ui(){btn.classList.toggle("on",on);btn.setAttribute("aria-pressed",on);btn.querySelector("span:last-child").textContent=on?"음악 끄기":"음악 켜기";}
  btn.addEventListener("click",()=>{ try{localStorage.setItem("snd",on?"0":"1")}catch(e){} on?stop():start(); });
  /* autoplay is blocked until a gesture: resume on first touch if the visitor had it on */
  let pref="1"; try{pref=localStorage.getItem("snd")||"1"}catch(e){}
  if(pref==="1"){ ["pointerdown","keydown","scroll"].forEach(e=>addEventListener(e,ev=>{ if(!on&&!ctx&&!(ev.target.closest&&ev.target.closest("#snd"))) start(); },{once:true,passive:true})); }
  document.addEventListener("visibilitychange",()=>{ if(!ctx||!on) return; document.hidden?ctx.suspend():ctx.resume(); });
})();
