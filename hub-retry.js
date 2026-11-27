'use strict';

// The original puzzle hub uses its stable puzzle IDs, independently of the courses.
function createHubReview({puzzles, startReview, endReview}) {
  const key='notopened.board.wrong.v1.hub';
  const byId=new Map(puzzles.map(p=>[p.id,p]));
  const find=id=>document.getElementById(id);
  let items=new Map(), persistent=true, reviewing=false;
  function moveSquare(p,r,c) {
    return p.type==='chess' ? String.fromCharCode(97+c)+(8-r) : (r+1)+'행 '+(c+1)+'열';
  }

  function read() {
    if (!persistent) return;
    let raw;
    try { raw=window.localStorage.getItem(key); } catch { persistent=false; return; }
    let rows; try { rows=JSON.parse(raw); } catch { rows=null; }
    items=new Map();
    if (!Array.isArray(rows)) return;
    rows.forEach(row=>{
      if (!Array.isArray(row)||!byId.has(row[0])||!Array.isArray(row[1])) return;
      const notes=row[1].filter(n=>Array.isArray(n)&&typeof n[0]==='string'&&typeof n[1]==='string'
        && n[0].length<=70&&n[1].length<=300).slice(-3);
      if (notes.length) items.set(row[0],notes);
    });
  }
  function write() {
    if (!persistent) return;
    try { window.localStorage.setItem(key,JSON.stringify([...items])); }
    catch { persistent=false; }
  }

  function display(announcement='') {
    const start=find('hubWrongStart');
    start.hidden=reviewing;
    start.disabled=!items.size;
    start.textContent='오답 다시 풀기 ('+items.size+')';
    find('hubWrongExit').hidden=!reviewing;
    const note=persistent?'같은 브라우저에 저장돼요.':'저장이 차단되어 이 탭에서만 남아요.';
    find('hubWrongStatus').textContent=announcement||(reviewing?'오답 연습 · 남은 문제 '+items.size+'개':
      '틀렸던 문제만 다시 풀 수 있어요. '+note);
    find('nextBtn').textContent=reviewing ? (items.size ? '➡️ 다음 오답' : '오답 연습 마치기') : '➡️ 다음 문제';
  }

  function pending() {
    read();
    return [...items.keys()].map(id=>byId.get(id));
  }

  function resetNotes() {
    find('hubWrongNotes').hidden=true;
    find('hubWrongNotes').open=false;
    find('hubWrongList').replaceChildren();
  }

  function record(p,mv,note) {
    if (!note) return;
    read();
    const to=moveSquare(p,mv.r,mv.c);
    const square=mv.from?moveSquare(p,...mv.from)+' → '+to:to;
    const history=items.get(p.id)||[];
    if (!history.some(n=>n[0]===square)) {
      items.set(p.id,[...history,[square,note]].slice(-3));
      write();
    }
    display();
  }

  function complete(p) {
    read();
    const list=find('hubWrongList');
    list.replaceChildren();
    (items.get(p.id)||[]).forEach(([square,note])=>{
      const li=document.createElement('li');
      li.textContent=square+': '+note;
      list.append(li);
    });
    find('hubWrongNotes').hidden=!list.childElementCount;
    if (reviewing) { items.delete(p.id); write(); }
    display();
  }

  function leave(restore=true,complete=false) {
    if (!reviewing) return;
    reviewing=false;
    if (restore) endReview();
    display(complete?'이번 오답 연습에서 모두 맞혔어요!':'');
    if (complete) find('hubWrongStatus').focus({preventScroll:true});
  }

  find('hubWrongStart').addEventListener('click',()=>{
    if (!pending().length) { display(); return; }
    reviewing=true;
    display();
    startReview();
  });
  find('hubWrongExit').addEventListener('click',()=>{leave();find('hubWrongStatus').focus({preventScroll:true});});
  window.addEventListener('storage',event=>{
    if (event.key===key||event.key===null) { read();display(); }
  });
  read();
  display();
  return {get active(){return reviewing;},pending,record,complete,resetNotes,leave};
}
