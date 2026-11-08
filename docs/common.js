/* photos keep natural aspect ratio; rows share one height */
(function(){
  function fit(img){ if(!img.naturalWidth) return; const f=img.closest(".pic"); if(!f) return;
    img.style.aspectRatio="auto"; f.style.setProperty("--ar",(img.naturalWidth/img.naturalHeight).toFixed(4)); }
  document.addEventListener("load",e=>{ if(e.target.tagName==="IMG") fit(e.target); },true);
  document.querySelectorAll(".pic img").forEach(i=>{ if(i.complete) fit(i); });
})();
/* reveal on scroll (content stays visible if IntersectionObserver is unavailable) */
(function(){
  const rev = document.querySelectorAll(".reveal");
  if(!("IntersectionObserver" in window)){ rev.forEach(el=>el.classList.add("in")); return; }
  const io = new IntersectionObserver(es=>es.forEach(en=>{ if(en.isIntersecting){ en.target.classList.add("in"); io.unobserve(en.target);} }),{threshold:.12});
  rev.forEach((el,i)=>{ el.style.transitionDelay = (el.classList.contains("rt")? (i%4)*.06 : 0)+"s"; io.observe(el); });
  setTimeout(()=>rev.forEach(el=>{ const r=el.getBoundingClientRect(); if(r.top<innerHeight) el.classList.add("in"); }),60);
})();
