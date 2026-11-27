'use strict';

// A title identifies a lesson; a coordinate identifies each mistaken choice.
// A reordered lesson or answer list won't accidentally restore a different move.
function createMistakeReview({course, lessons, getIndex, open}) {
  const key = 'notopened.board.wrong.v1.' + course;
  const lessonByTitle = new Map(lessons.map((lesson, index) => [lesson.title, {lesson, index}]));
  const coord = option => option.slice(0,2).join(',');
  let items = new Map(), persistent = true, reviewing = false, returnIndex = 0;
  let reviewPool = [];
  const find = id => document.getElementById(id);
  function node(tag, attrs, text) {
    const el = document.createElement(tag);
    for (const [k,v] of Object.entries(attrs)) el.setAttribute(k,v);
    if (text) el.textContent = text;
    return el;
  }

  function read() {
    if (!persistent) return;
    let raw;
    try { raw = window.localStorage.getItem(key); } catch { persistent=false; return; }
    let records;
    try { records=JSON.parse(raw); } catch { records=null; }
    items = new Map();
    if (!Array.isArray(records)) return;
    for (const row of records) {
      if (!Array.isArray(row) || typeof row[0] !== 'string' || !Array.isArray(row[1])) continue;
      const entry = lessonByTitle.get(row[0]);
      if (!entry) continue;
      const options = new Set(entry.lesson.options.filter((_, i) => i !== entry.lesson.answer).map(coord));
      const mistakes = [...new Set(row[1].filter(value => options.has(value)))];
      if (mistakes.length) items.set(row[0],mistakes);
    }
  }

  function write() {
    if (!persistent) return;
    try { window.localStorage.setItem(key,JSON.stringify([...items])); }
    catch { persistent=false; }
  }

  const box=node('section',{class:'mistake-box','aria-label':'오답 다시 풀기'});
  const start=node('button',{type:'button',id:'mistake-start',class:'retry'},'오답 다시 풀기');
  const exit=node('button',{type:'button',id:'mistake-exit',class:'retry'},'일반 연습으로 돌아가기');
  const status=node('p',{id:'mistake-status',role:'status'});
  box.append(start,exit,status);
  find('steps').before(box);
  const details=node('details',{id:'mistake-notes',class:'mistake-notes'});
  const summary=node('summary',{},'내가 틀린 선택 살펴보기');
  const list=node('ul',{});
  details.append(summary,list);
  find('response').after(details);

  function queued() {
    return (reviewing ? reviewPool : [...items.keys()]).filter(title => items.has(title));
  }

  function display(announcement='') {
    start.hidden=reviewing;
    exit.hidden=!reviewing;
    start.disabled=!items.size;
    start.textContent='오답 다시 풀기 ('+items.size+')';
    const about=persistent?'같은 브라우저에 저장돼요.':'저장이 차단되어 이 탭에서만 남아요.';
    status.textContent=announcement || (reviewing ?
      '오답 연습 · 남은 문제 '+queued().length+'개' :
      items.size?'틀렸던 문제만 다시 풀 수 있어요. '+about :
      '틀린 문제가 생기면 여기에서 다시 풀 수 있어요. '+about);
  }

  function resetNotes() {
    details.hidden=true;
    details.open=false;
    list.replaceChildren();
  }

  function leave(reopen) {
    if (!reviewing) return;
    reviewing=false;
    reviewPool=[];
    display();
    if (reopen) open(returnIndex,true);
  }

  function record(index, choice) {
    read();
    const lesson=lessons[index], square=coord(lesson.options[choice]);
    const existing=items.get(lesson.title)||[];
    if (!existing.includes(square)) {
      items.set(lesson.title,[...existing,square]);
      write();
    }
    display();
  }

  function complete(index) {
    read();
    const lesson=lessons[index], mistakes=items.get(lesson.title)||[];
    list.replaceChildren();
    lesson.options.forEach((option,i)=>{
      if (i===lesson.answer || !mistakes.includes(coord(option)) || !option[2]) return;
      list.append(node('li',{},String.fromCharCode(65+i)+' 선택: '+option[2]));
    });
    details.hidden=!list.childElementCount;
    if (reviewing) {
      items.delete(lesson.title);
      write();
    }
    display();
  }

  function next() {
    if (!reviewing) return false;
    read();
    const pending=queued();
    if (pending.length) open(lessonByTitle.get(pending[0]).index,true);
    else {
      leave(true);
      display('이번 오답 연습에서 모두 맞혔어요!'+(items.size?' 새로 담긴 오답도 연습할 수 있어요.':''));
    }
    return true;
  }

  start.addEventListener('click',()=>{
    read();
    if (!items.size) { display(); return; }
    returnIndex=getIndex();
    reviewPool=[...items.keys()];
    reviewing=true;
    display();
    open(lessonByTitle.get(reviewPool[0]).index,true);
  });
  exit.addEventListener('click',()=>leave(true));
  window.addEventListener('storage',event=>{
    if (event.key===key || event.key===null) { read(); display(); }
  });

  read();
  resetNotes();
  display();
  return { get active(){return reviewing;}, record, complete, resetNotes, leave, next,
    nextLabel:()=>queued().length?'다음 오답 →':'오답 연습 마치기 →' };
}
