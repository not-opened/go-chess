'use strict';
const $ = id => document.getElementById(id);
const topic = document.body.dataset.topic;
const go = topic === 'go';
const size = go ? 9 : 8;
const name = go ? '바둑' : '체스';
const modes = ['공격','수비'];
const abc = ['A','B','C'];
const glyphs = {K:'♚',Q:'♛',R:'♜',B:'♝',N:'♞',P:'♟'};
const piecesKo = {K:'킹',Q:'퀸',R:'룩',B:'비숍',N:'나이트',P:'폰'};
const solved = new Set();
let index=0, selected=false, done=false, miss=-1, result=false;

const same = (a,b) => a[0]===b[0] && a[1]===b[1];
const matches = (squares,sq) => (squares || []).some(a=>same(a,sq));
const locationText = ([r,c]) => go ? (r+1)+'행 '+(c+1)+'열' : String.fromCharCode(97+c)+(8-r);
const current = () => lessons[index];
const modeOf = i => i < 5 ? 0 : 1;
const startOf = mode => mode*5;
const groupSolved = mode => [...solved].filter(i=>modeOf(i)===mode).length;

function text(id,value){$(id).textContent=value;}
function feedback(title,detail,tone=''){
  $('response').dataset.tone=tone;
  text('status',title);
  text('detail',detail);
}

function place(el,[r,c]){
  el.style.gridRow=String(r+1);
  el.style.gridColumn=String(c+1);
}

function svgEl(tag,props){
  const e=document.createElementNS('http://www.w3.org/2000/svg',tag);
  Object.entries(props).forEach(([k,v])=>e.setAttribute(k,v));
  return e;
}

function drawGrid(p){
  const svg=svgEl('svg',{viewBox:'0 0 '+size+' '+size, 'aria-hidden':'true'});
  if(go){
    let path='';
    for(let i=0;i<9;i++) path+='M.5 '+(i+.5)+'h8M'+(i+.5)+' .5v8';
    svg.append(svgEl('path',{d:path,fill:'none',stroke:'#775730','stroke-width':'.035'}));
    [[2,2],[6,2],[4,4],[2,6],[6,6]].forEach(([x,y])=>svg.append(svgEl('circle',{cx:x+.5,cy:y+.5,r:'.07',fill:'#775730'})));
  }else{
    for(let r=0;r<8;r++)for(let c=0;c<8;c++)if((r+c)%2)svg.append(svgEl('rect',{x:c,y:r,width:1,height:1,fill:'#97aa93'}));
    for(let i=0;i<8;i++){
      const rank=svgEl('text',{x:'.10',y:i+.25,fill:'#20392d','font-size':'.19','font-weight':'800'});
      rank.textContent=String(8-i);svg.append(rank);
      const file=svgEl('text',{x:i+.82,y:'7.91',fill:'#20392d','font-size':'.19','font-weight':'800'});
      file.textContent=String.fromCharCode(97+i);svg.append(file);
    }
  }
  if(done){
    const [r,c]=p.options[p.answer];
    if(!go){
      const [oldR,oldC]=p.origin;
      svg.append(svgEl('line',{x1:oldC+.5,y1:oldR+.5,x2:c+.5,y2:r+.5,stroke:'#195340','stroke-width':'.13','stroke-dasharray':'.14 .14'}));
    }else{
      const mark=svgEl('circle',{cx:c+.5,cy:r+.5,r:'.44',stroke:'#106047','stroke-width':'.13',fill:'none'});
      svg.append(mark);
    }
  }
  return svg;
}

function pieceName(piece){
  if(go)return piece[2]==='B'?'흑돌':'백돌';
  return (piece[3]==='w'?'백 ':'흑 ')+piecesKo[piece[2]];
}
function boardPieces(p){
  if(go)return done?p.after:p.stones;
  if(!done)return p.pieces;
  const dest=p.options[p.answer];
  const mover=p.pieces.find(piece=>same(piece,p.origin));
  return p.pieces.filter(piece=>!same(piece,p.origin)&&!same(piece,dest)).concat([[dest[0],dest[1],mover[2],mover[3]]]);
}

function renderBoard(focusId){
  const p=current(), board=$('board'), pieces=boardPieces(p);
  board.className='tactics-board '+topic;
  board.style.setProperty('--size',size);
  board.replaceChildren(drawGrid(p));
  const marks=go?p.targets:p.attackers;
  const label=modeOf(index)===0?'목표 돌':go?'위험한 돌':'체크를 건 말';
  pieces.forEach(piece=>{
    const mover=!go&&!done&&same(piece,p.origin);
    const marked=!done&&matches(marks,piece);
    const e=document.createElement(mover?'button':'span');
    const dark=go?piece[2]==='B':piece[3]==='b';
    e.className=(go?'stone':'piece')+' '+(dark?'black':'white')+(mover?' origin':'')+(marked?' threat':'');
    e.setAttribute('aria-label',pieceName(piece)+', '+locationText(piece)+(mover?', 움직일 말':'')+(marked?', '+label:''));
    if(!go)e.textContent=glyphs[piece[2]];
    if(mover){
      e.id='origin';e.type='button';
      e.setAttribute('aria-pressed',String(selected));
      e.addEventListener('click',()=>{
        selected=!selected;miss=-1;
        feedback(selected?'도착할 곳을 골라 보세요.':'움직일 말을 눌러요.',selected?'A, B, C 중 한곳을 골라 보세요.':'파란 테두리로 표시된 백 기물을 눌러 시작하세요.');
        renderBoard(selected?'option-0':'origin');
      });
    }else e.setAttribute('role','img');
    place(e,piece);board.append(e);
  });
  if(!done) p.options.forEach((op,i)=>{
    const at=pieces.find(piece=>same(piece,op));
    const b=document.createElement('button'), badge=document.createElement('span');
    b.type='button';b.id='option-'+i;
    b.className='candidate'+(at?' over-piece':'')+(i===miss?' miss':'');
    b.setAttribute('aria-label',abc[i]+' '+(go?'착수점':'도착점')+', '+locationText(op)+(at?', '+pieceName(at):''));
    badge.textContent=abc[i];b.append(badge);
    b.addEventListener('click',()=>choose(i));
    place(b,op);board.append(b);
  });
  if(focusId)$(focusId)?.focus({preventScroll:true});
}

function renderSteps(){
  const nav=$('steps');
  if(!nav.children.length) modes.forEach((mode,m)=>{
    const section=document.createElement('section');
    section.className='step-group';
    const title=document.createElement('h2'), progress=document.createElement('span');
    title.className='step-title';
    progress.id='section-progress-'+m;
    progress.setAttribute('aria-live','polite');
    title.append(mode+' ',progress);
    const grid=document.createElement('div');grid.className='step-grid';
    for(let j=0;j<5;j++){
      const i=m*5+j,b=document.createElement('button');
      b.type='button';b.dataset.index=i;
      b.addEventListener('click',()=>{ review.leave(false); open(i,true); });grid.append(b);
    }
    section.append(title,grid);nav.append(section);
  });
  modes.forEach((_,m)=>text('section-progress-'+m,groupSolved(m)+' / 5'));
  nav.querySelectorAll('button').forEach(b=>{
    const i=Number(b.dataset.index), num=i%5+1, finished=solved.has(i);
    b.textContent=finished?'✓'+num:String(num);
    b.classList.toggle('solved',finished);
    b.setAttribute('aria-label',modes[modeOf(i)]+' '+num+'수: '+lessons[i].tab+(finished?', 완료':''));
    if(i===index&&!result)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');
  });
}

function open(i,focus=false){
  index=i;done=selected=result=false;miss=-1;
  const p=current(), mode=modes[modeOf(index)];
  review.resetNotes();
  $('lesson').hidden=false;$('finish').hidden=true;
  text('title',(index%5+1)+'수. '+p.title);
  text('kicker',(review.active?'오답 · ':'')+mode+' 연습 · '+(go?'흑':'백')+' 차례');
  text('prompt',p.prompt);
  text('hint-text',p.hint);
  $('hint-text').hidden=$('next').hidden=$('retry').hidden=true;
  $('hint').hidden=false;
  text('hint','힌트 보기');
  $('hint').setAttribute('aria-expanded','false');
  feedback(go?'놓을 곳을 골라 보세요.':'움직일 말을 눌러요.',go?'A, B, C 중 한곳을 눌러 흑돌을 두세요.':'파란 테두리로 표시된 백 기물을 눌러 시작하세요.');
  const marks=go?p.targets:p.attackers;
  document.querySelector('.tactics-legend').textContent=(go?'흑 차례 · 교차점에 돌을 둬요.':'백 차례 · 말을 누르고 도착점을 골라요.')+
    (marks?.length?' 주황색: '+(modeOf(index)===0?'목표 돌':go?'위험한 돌':'체크를 건 말')+'.':'');
  renderBoard();
  renderSteps();
  if(focus)$('title').focus();
}

function choose(i){
  if(done)return;
  if(!go&&!selected){
    feedback('말을 먼저 골라요.','파란 테두리의 백 기물을 누른 뒤 도착점을 고르세요.');
    $('origin').focus({preventScroll:true});return;
  }
  const p=current();
  if(i!==p.answer){
    miss=i;
    review.record(index,i);
    feedback('다시 골라 보세요.',p.options[i][2],'wrong');
    renderBoard('option-'+i);
    $('response').scrollIntoView({block:'nearest'});
    return;
  }
  done=true;solved.add(index);
  review.complete(index);
  renderBoard();renderSteps();
  feedback('맞았어요!',p.rule,'ok');
  $('hint').hidden=$('hint-text').hidden=true;
  $('next').hidden=$('retry').hidden=false;
  text('next',review.active?review.nextLabel():groupSolved(modeOf(index))===5?'코스 결과 보기 →':'다음 수 →');
  $('next').focus({preventScroll:true});
  $('next').scrollIntoView({block:'nearest'});
}

function firstIncomplete(mode){
  const start=startOf(mode);
  return [0,1,2,3,4].map(n=>n+start).find(i=>!solved.has(i));
}

function finish(){
  result=true;$('lesson').hidden=true;$('finish').hidden=false;
  const mode=modeOf(index), both=solved.size===lessons.length;
  text('finish-label',both?'10 / 10수 완료':modes[mode]+' 5 / 5수 완료');
  text('finish-title',both?name+' 공격과 수비, 모두 완료!':modes[mode]+' 5수를 마쳤어요!');
  text('continue',modes[1-mode]+(both?' 다시 보기 →':' 이어서 풀기 →'));
  renderSteps();$('finish-title').focus();
}

$('hint').addEventListener('click',()=>{
  const show=$('hint-text').hidden;
  $('hint-text').hidden=!show;text('hint',show?'힌트 숨기기':'힌트 보기');
  $('hint').setAttribute('aria-expanded',String(show));
});
$('next').addEventListener('click',()=>{
  if(review.next())return;
  const m=modeOf(index);
  if(groupSolved(m)===5){finish();return;}
  const start=startOf(m);
  const next=[1,2,3,4].map(n=>start+(index-start+n)%5).find(i=>!solved.has(i));
  if(next!==undefined)open(next,true);
});
$('retry').addEventListener('click',()=>open(index,true));
$('continue').addEventListener('click',()=>{
  const m=1-modeOf(index);open(firstIncomplete(m)??startOf(m),true);
});
$('again').addEventListener('click',()=>{
  const m=modeOf(index), start=startOf(m);
  for(let i=start;i<start+5;i++)solved.delete(i);
  open(start,true);
});
const review=createMistakeReview({course:topic,lessons,getIndex:()=>index,open});
open(new URLSearchParams(location.search).get('mode')==='defense'?5:0);
