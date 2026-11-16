/* A4 페이지 자동 분배 — Claude Design 다운로드(화면 캡처→고정높이 슬라이스) 대응.
   각 .pdfpage 를 A4 비율(210:297) 전체폭으로 쌓음 → 어떤 폭으로 캡처해도 슬라이스가 페이지 경계와 맞음.
   핵심: 조상 의존 CSS(#cvid .pipe, .case .body .flow 등)가 깨지지 않도록
         각 페이지에 해당 case의 id/class 래퍼(.case > .body)를 재생성해 .sec 를 그 안에 넣는다.
   넘치는 블록은 그 블록만 축소 → 내용이 절대 잘리지 않음. */
(function(){
  function build(){
    var shell=document.querySelector('.shell'); if(!shell||document.querySelector('.pdfroot')) return;
    var hero=shell.querySelector('header.hero');
    var cases=[].slice.call(shell.querySelectorAll('.case'));
    var closing=shell.querySelector('.closing');

    var root=document.createElement('div'); root.className='pdfroot';
    document.body.insertBefore(root, document.body.firstChild);

    var curInner, pageInnerH, curCase, curWrap, nOnPage;
    function newPage(){
      var pg=document.createElement('div'); pg.className='pdfpage';
      var inner=document.createElement('div'); inner.className='pdfinner'; pg.appendChild(inner);
      root.appendChild(pg); curInner=inner; pageInnerH=inner.clientHeight;
      curCase=null; curWrap=null; nOnPage=0;
    }
    function wrapFor(caseEl){
      if(curWrap && curCase===caseEl) return curWrap;
      var w=document.createElement('div'); if(caseEl.id) w.id=caseEl.id; w.className=caseEl.className;
      var bd=document.createElement('div'); bd.className='body'; w.appendChild(bd); w._bd=bd;
      curInner.appendChild(w); curCase=caseEl; curWrap=w; return w;
    }
    function fit(el){
      var h=el.getBoundingClientRect().height; if(h<=0) return;
      var s=(pageInnerH-6)/h; if(s>=1) return;
      el.style.transformOrigin='top left'; el.style.transform='scale('+s+')';
      el.style.width=(100/s)+'%'; el.style.marginBottom=(-(h*(1-s)))+'px';
    }
    // caseEl=null → pdfinner 직접(히어로/클로징). toBody=true → .body 안에.
    function place(el, caseEl, toBody){
      var tgt;
      if(caseEl){ var w=wrapFor(caseEl); tgt=toBody?w._bd:w; } else { tgt=curInner; curCase=null; curWrap=null; }
      tgt.appendChild(el); nOnPage++;
      if(curInner.scrollHeight > pageInnerH+2){
        if(nOnPage===1){ fit(el); newPage(); }
        else {
          tgt.removeChild(el); nOnPage--; newPage();
          if(caseEl){ var w2=wrapFor(caseEl); tgt=toBody?w2._bd:w2; } else { tgt=curInner; }
          tgt.appendChild(el); nOnPage++;
          if(curInner.scrollHeight > pageInnerH+2){ fit(el); newPage(); }
        }
      }
    }

    newPage();
    if(hero){ var hw=document.createElement('div'); hw.className='u-hero'; hw.appendChild(hero); place(hw,null,false); }
    cases.forEach(function(c){
      var top=c.querySelector('.case-top'); var lead=c.querySelector(':scope > .lead');
      if(top) place(top, c, false);
      if(lead) place(lead, c, false);
      var body=c.querySelector('.body'); var secs= body? [].slice.call(body.children):[];
      secs.forEach(function(s){ place(s, c, true); });
    });
    if(closing) place(closing, null, false);

    shell.style.display='none';
    document.documentElement.classList.remove('js-motion');
    document.documentElement.classList.add('pdfmode');
  }
  if(document.readyState==='complete') setTimeout(build,300);
  else window.addEventListener('load', function(){ setTimeout(build,300); });
})();
