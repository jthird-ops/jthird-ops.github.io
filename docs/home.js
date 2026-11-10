const doneList = M.filter(m=>m.done);
$("#sDone").innerHTML = doneList.length + "<small>/100</small>";
$("#sAlt").innerHTML = (doneList.reduce((a,m)=>a+m.h,0)/1000).toFixed(1) + "<small>km</small>";
(function(){
  /* hero: the clip plays, then the Huiyangsan photo drifts by depth, then back — on a loop */
  const A=$("#bgv"), cv=$("#gl"), FADE=1.6, HOLD=32;
  const RM=matchMedia("(prefers-reduced-motion:reduce)").matches;
  A.muted=true; A.defaultMuted=true; A.setAttribute("muted",""); A.setAttribute("playsinline","");
  const kick=()=>A.play().catch(()=>{});
  const gl=cv.getContext("webgl",{antialias:false,alpha:false,powerPreference:"high-performance"});
  if(!gl){                                   /* no WebGL: keep the clip looping as before */
    A.loop=true; A.addEventListener("playing",()=>A.classList.add("on")); kick();
    ["touchstart","click","scroll"].forEach(e=>addEventListener(e,()=>{ if(A.paused) kick(); },{once:true,passive:true}));
    document.addEventListener("visibilitychange",()=>{ if(!document.hidden && A.paused) kick(); });
    return;
  }
  const vs=`attribute vec2 p;varying vec2 s;void main(){s=p*.5+.5;gl_Position=vec4(p,0.,1.);}`;
  const fs=`precision highp float;varying vec2 s;
  uniform sampler2D P,D;uniform vec2 R;uniform float T,TY,Z,TM,MO;
  float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
  float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
  float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<4;i++){v+=a*n(p);p=p*2.03+vec2(1.7,9.2);a*=.5;}return v;}
  void main(){
    float ar=R.x/R.y; vec2 sc=ar>=1.?vec2(1.,1./ar):vec2(ar,1.);
    vec2 fo=ar>=1.?vec2(.5,.58):vec2(.6,.5);
    vec2 uv=fo+(s-.5)*sc/Z;
    /* depth-driven parallax: one photo, no cut-outs — near rock slides, far ridges hold */
    vec2 A=vec2(T*.030,TY*.011);
    vec2 p=uv;
    for(int i=0;i<6;i++){
      float d=texture2D(D,clamp(p,0.,1.)).r;
      vec2 t=uv-A*pow(max(0.,1.-d),1.6);
      p=mix(p,t,.75);
    }
    vec3 col=texture2D(P,clamp(p,0.,1.)).rgb;
    /* valley mist, drifting right */
    vec2 mc=(uv-vec2(.33,.555))/vec2(.17,.062);
    float em=exp(-dot(mc,mc)*1.6);
    float m1=fbm(uv*vec2(9.,14.)+vec2(TM*.018,TM*.003));
    float m2=fbm(uv*vec2(17.,26.)-vec2(TM*.011,0.));
    float mist=smoothstep(.42,.78,m1*.65+m2*.35)*em*.62;
    col=mix(col,vec3(.86,.90,.95),mist*MO);
    /* faint haze band over the far ridges */
    vec2 hc=(uv-vec2(.6,.63))/vec2(.6,.05);
    float eh=exp(-dot(hc,hc)*1.2);
    float hz=smoothstep(.45,.8,fbm(uv*vec2(5.,9.)+vec2(TM*.009,0.)))*eh*.16;
    col=mix(col,vec3(.72,.80,.90),hz*MO);
    col=pow(col,vec3(1.04));
    gl_FragColor=vec4(col,1.);
  }`;
  function sh(t,src){const o=gl.createShader(t);gl.shaderSource(o,src);gl.compileShader(o);return o;}
  const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);gl.useProgram(pr);
  const buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  const lp=gl.getAttribLocation(pr,"p");gl.enableVertexAttribArray(lp);gl.vertexAttribPointer(lp,2,gl.FLOAT,false,0,0);
  const U=n=>gl.getUniformLocation(pr,n);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);
  function tex(unit,img){const t=gl.createTexture();gl.activeTexture(gl.TEXTURE0+unit);gl.bindTexture(gl.TEXTURE_2D,t);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,img);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);return t;}
  const srcs={P:"assets/hero-photo.77264867.jpg",D:"assets/hero-depth.1a8cc027.png"}, imgs={}; let left=2, ready=false;
  Object.keys(srcs).forEach(k=>{const im=new Image();im.onload=()=>{imgs[k]=im;if(--left===0)init();};im.onerror=()=>{A.loop=true;};im.src=srcs[k];});
  /* the clip starts right away; the parallax takes over once its textures are in */
  A.addEventListener("playing",()=>{ if(phase===0){ clearTimeout(bail); A.classList.add("on"); } });
  A.addEventListener("ended",()=>toParallax());
  A.addEventListener("error",()=>toParallax());
  ["touchstart","click","scroll"].forEach(e=>addEventListener(e,()=>{ if(phase===0 && A.paused) kick(); },{once:true,passive:true}));
  document.addEventListener("visibilitychange",()=>{ if(!document.hidden && phase===0 && A.paused) kick(); });
  kick();
  let phase=0, lit=false, seeking=false, et=0, last=0, bailed=false;
  const bail=setTimeout(()=>{ bailed=true; toParallax(); },3500);   /* autoplay blocked or slow: show the parallax */
  function toParallax(){
    if(phase===1||!ready) return; phase=1;
    clearTimeout(bail);
    et=0;                                /* restart the drift from its resting point */
    cv.classList.add("on"); lit=true;
    A.classList.remove("on");
    setTimeout(()=>{ if(phase===1){ try{ A.pause(); }catch(e){} } },FADE*1000+300);
  }
  function toVideo(){
    if(phase===0||A.error||!lit||!A.duration) return;
    phase=0;
    const go=()=>{ seeking=false; kick(); A.classList.add("on"); };
    if(A.currentTime>0.05){ seeking=true; A.addEventListener("seeked",go,{once:true}); A.currentTime=0; } else go();
  }
  function init(){
    ["P","D"].forEach((k,i)=>{tex(i,imgs[k]);gl.uniform1i(U(k),i);});
    gl.uniform1f(U("MO"),1); ready=true;
    function size(){const dpr=Math.min(devicePixelRatio||1,innerWidth<760?1.5:2);const w=Math.round(cv.clientWidth*dpr),h=Math.round(cv.clientHeight*dpr);if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h;gl.viewport(0,0,w,h);gl.uniform2f(U("R"),w,h);}}
    function frame(now){
      size();
      if(!last) last=now;
      const dt=Math.min(now-last,50); last=now;
      if(!RM) et+=dt/1000;
      const t=et;
      const T=0.86*Math.sin(t/16*6.2832-1.2)+0.14*Math.sin(t/6.8*6.2832);
      const TY=Math.sin(t/21*6.2832+.8);
      const Z=1.045+0.015*Math.sin(t/27*6.2832);
      gl.uniform1f(U("T"),T);gl.uniform1f(U("TY"),TY);gl.uniform1f(U("Z"),Z);gl.uniform1f(U("TM"),t+40);
      gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    (function watch(){
      if(phase===0){
        if(!seeking && A.duration && !A.paused && A.currentTime>FADE && A.duration-A.currentTime<=FADE) toParallax();
      }else if(!RM && et>=HOLD){ toVideo(); }
      requestAnimationFrame(watch);
    })();
    if(bailed && !A.classList.contains("on")) toParallax();   /* clip never started */
  }
})();


/* background music (bgm.mp3, loop, fade-in) */
(function(){
  const btn=document.getElementById("snd"); if(!btn) return;
  const au=new Audio("bgm.mp3"); au.loop=true; au.preload="none"; au.volume=0;
  const VOL=.5; let on=false, fade;
  /* iOS ignores volume changes on an <audio> element, so never wait on the fade to finish */
  function ramp(to,done){
    clearInterval(fade);
    let prev=au.volume, stuck=0, steps=0;
    const end=()=>{ try{ au.volume=to; }catch(e){} clearInterval(fade); done&&done(); };
    fade=setInterval(()=>{
      if(Math.abs(to-au.volume)<.03 || ++steps>40 || stuck>2){ end(); return; }
      try{ au.volume=Math.max(0,Math.min(1,au.volume+Math.sign(to-au.volume)*.03)); }catch(e){ end(); return; }
      stuck = Math.abs(au.volume-prev)<.001 ? stuck+1 : 0;
      prev=au.volume;
    },60);
  }
  function ui(){btn.classList.toggle("on",on);btn.setAttribute("aria-pressed",on);btn.querySelector("span:last-child").textContent=on?"음악 끄기":"음악 켜기";}
  let volOK=null;
  function canFade(){                      /* iOS: setting volume does nothing, so don't fade there */
    if(volOK===null){ const v=au.volume, probe=v>.4?.2:.6;
      try{ au.volume=probe; }catch(e){}
      volOK=Math.abs(au.volume-probe)<.01;
      try{ au.volume=v; }catch(e){} }
    return volOK;
  }
  function kill(){ try{ au.pause(); }catch(e){} }
  function start(){
    on=true; ui(); clearInterval(fade);
    const r=au.play();
    /* a rejected play() does not always mean it is silent — only step back if it really is */
    if(r&&r.catch) r.catch(()=>{ if(au.paused){ on=false; ui(); } });
    ramp(VOL);
  }
  function stop(){
    on=false; ui(); clearInterval(fade);
    if(canFade()) ramp(0,kill); else kill();
    setTimeout(()=>{ if(!on) kill(); },900);   /* never leave it playing */
  }
  btn.addEventListener("click",()=>{
    const playing = on || !au.paused;        /* trust the audio, not just the flag */
    try{localStorage.setItem("snd",playing?"0":"1")}catch(e){}
    playing?stop():start();
  });
  let pref="1"; try{pref=localStorage.getItem("snd")||"1"}catch(e){}
  if(pref==="1"){ ["pointerdown","keydown"].forEach(e=>addEventListener(e,ev=>{ if(!on&&!(ev.target.closest&&ev.target.closest("#snd"))) start(); },{once:true,passive:true})); }
  document.addEventListener("visibilitychange",()=>{ if(!on) return; document.hidden?au.pause():au.play().catch(()=>{}); });
})();
