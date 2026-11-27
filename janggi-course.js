'use strict';

const symbols = {P:['포','包'], R:['차','車'], M:['마','馬'], S:['병','兵']};
const fixed = [[0,4,'K','cho'], [8,5,'K']];
const abc = ['A','B','C'];
const svgNS = 'http://www.w3.org/2000/svg';
const solved = new Set();
let index = 0, selected = false, finishedMove = false, miss = -1;
const $ = id => document.getElementById(id);

function describe(piece) {
  const side = piece[3] === 'cho';
  const names = piece[2] === 'K' ? ['궁', side ? '楚' : '漢'] :
    piece[2] === 'S' && side ? ['졸','卒'] : symbols[piece[2]];
  return [names[1], (side ? '초 ' : '한 ') + names[0]];
}

function place(el, r, c) {
  el.style.gridRow = String(r + 1);
  el.style.gridColumn = String(c + 1);
}

function svgEl(tag, attrs) {
  const el = document.createElementNS(svgNS, tag);
  Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k, v));
  return el;
}

function makeGrid() {
  const svg = svgEl('svg', {viewBox:'0 0 9 10', 'aria-hidden':'true'});
  let path = 'M3.5 .5l2 2m0 -2l-2 2M3.5 7.5l2 2m0 -2l-2 2';
  for (let r=0; r<10; r++) path += 'M.5 ' + (r+.5) + 'h8';
  for (let c=0; c<9; c++) path += 'M' + (c+.5) + ' .5v9';
  svg.append(svgEl('path', {d:path, fill:'none', stroke:'#775730', 'stroke-width':'.032'}));
  return svg;
}

function position(square) { return (square[0]+1) + '행 ' + (square[1]+1) + '열'; }
function same(a,b) { return a[0] === b[0] && a[1] === b[1]; }

function renderBoard(focusTarget) {
  const p = lessons[index], board = $('board'), dest = p.options[p.answer];
  const svg = makeGrid();
  board.setAttribute('aria-label', p.attackers && !finishedMove ? '장기 연습판, 장군 상태' : '장기 연습판');
  if (finishedMove) {
    const [r,c] = p.origin;
    svg.append(svgEl('line', {x1:c+.5,y1:r+.5,x2:dest[1]+.5,y2:dest[0]+.5,stroke:'#195340','stroke-width':'.12','stroke-dasharray':'.13 .12'}));
    svg.append(svgEl('circle',{cx:c+.5,cy:r+.5,r:'.1',fill:'#195340'}));
  }
  board.replaceChildren(svg);
  const origin = finishedMove ? [dest[0],dest[1],p.origin[2]] : p.origin;
  const others = [...(p.kings || fixed),...p.extras].filter(piece => !finishedMove || !same(piece,dest));
  [origin,...others].forEach(piece => {
    const canMove = piece === origin && !finishedMove;
    const el = document.createElement(canMove ? 'button' : 'span');
    const [glyph, name] = describe(piece);
    const threat = !finishedMove && piece[3] === 'cho' && p.attackers?.some(square => same(square,piece));
    el.className = 'token' + (piece[3] === 'cho' ? ' cho' : '') + (threat ? ' threat' : '');
    el.textContent = glyph;
    el.setAttribute('aria-label', name + ', ' + position(piece) + (canMove ? ', 움직일 말' : '') + (threat ? ', 장군을 건 말' : ''));
    if (!canMove) el.setAttribute('role','img');
    if (canMove) {
      el.id = 'origin';
      el.type = 'button';
      el.setAttribute('aria-pressed', String(selected));
      el.addEventListener('click', () => {
        selected = !selected;
        miss = -1;
        feedback(selected ? '도착점을 골라 보세요.' : '움직일 말을 먼저 눌러요.',
          selected ? 'A, B, C 중 갈 수 있는 점이 하나 있어요.' : '테두리가 두꺼운 빨강 말을 누르세요.');
        renderBoard(selected ? 'option-0' : 'origin');
      });
    }
    place(el,piece[0],piece[1]);
    board.append(el);
  });
  if (!finishedMove) p.options.forEach((option,i) => {
    const occupying = others.find(piece => same(piece,option));
    const btn = document.createElement('button'), label = document.createElement('span');
    btn.type = 'button';
    btn.id = 'option-' + i;
    btn.className = 'target' + (occupying ? ' over-piece' : '') + (miss === i ? ' miss' : '');
    btn.setAttribute('aria-label', abc[i] + ' 도착점, ' + position(option) + (occupying ? ', ' + describe(occupying)[1] : ''));
    label.textContent = abc[i];
    btn.append(label);
    place(btn, option[0], option[1]);
    btn.addEventListener('click', () => choose(i));
    board.append(btn);
  });
  if (focusTarget) $(focusTarget)?.focus({preventScroll:true});
}

function feedback(title, detail, tone = '') {
  $('response').dataset.tone = tone;
  $('status').textContent = title;
  $('detail').textContent = detail;
}

function renderSteps() {
  $('progress').textContent = solved.size + ' / ' + lessons.length + '수 완료';
  document.querySelector('progress').value = solved.size;
  const steps = $('steps');
  if (!steps.children.length) lessons.forEach((p,i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.addEventListener('click', () => openLesson(i,true));
    steps.append(b);
  });
  [...steps.children].forEach((b,i) => {
    b.textContent = (solved.has(i) ? '✓ ' : '') + (i+1) + '수';
    b.setAttribute('aria-label', (i+1) + '수: ' + lessons[i].tab + (solved.has(i) ? ', 완료' : ''));
    if (i === index && $('finish').hidden) b.setAttribute('aria-current','step');
    else b.removeAttribute('aria-current');
  });
}

function openLesson(i, focusTitle = false) {
  index = i;
  selected = finishedMove = false;
  miss = -1;
  const p = lessons[i];
  $('finish').hidden = true;
  $('lesson').hidden = false;
  $('title').textContent = (index+1) + '수. ' + p.title;
  $('prompt').textContent = p.prompt;
  $('kicker').textContent = p.attackers ? '장군! · 한(빨강) 차례' : '한(漢) 차례 · 아래에서 위로';
  $('retry').hidden = $('next').hidden = true;
  $('hint').hidden = false;
  $('hint-text').hidden = true;
  $('hint-text').textContent = p.hint;
  $('hint').textContent = '힌트 보기';
  $('hint').setAttribute('aria-expanded','false');
  feedback('움직일 말을 먼저 눌러요.', '테두리가 두꺼운 빨강 말을 눌러 시작하세요.');
  renderBoard();
  renderSteps();
  if (focusTitle) $('title').focus();
}

function choose(i) {
  if (finishedMove) return;
  if (!selected) {
    feedback('말을 먼저 골라요.', '빨강 말을 누른 다음 도착점을 눌러 보세요.');
    $('origin').focus({preventScroll:true});
    return;
  }
  const p = lessons[index];
  if (i !== p.answer) {
    miss = i;
    feedback(abc[i] + '로는 갈 수 없어요. 다시 골라 보세요.', p.options[i][2], 'wrong');
    renderBoard('option-' + i);
    $('response').scrollIntoView({block:'nearest'});
    return;
  }
  finishedMove = true;
  solved.add(index);
  renderBoard();
  renderSteps();
  feedback(p.attackers ? '멍군! 장군을 벗어났어요.' : '맞았어요!', p.rule, 'ok');
  $('hint').hidden = $('hint-text').hidden = true;
  $('retry').hidden = $('next').hidden = false;
  $('next').textContent = solved.size === lessons.length ? '완료 보기 →' : '다음 수 →';
  $('next').focus({preventScroll:true});
  $('next').scrollIntoView({block:'nearest'});
}

$('hint').addEventListener('click', () => {
  const opening = $('hint-text').hidden;
  $('hint-text').hidden = !opening;
  $('hint').textContent = opening ? '힌트 숨기기' : '힌트 보기';
  $('hint').setAttribute('aria-expanded', String(opening));
});
$('retry').addEventListener('click', () => openLesson(index,true));
$('next').addEventListener('click', () => {
  if (solved.size === lessons.length) {
    $('lesson').hidden = true;
    $('finish').hidden = false;
    renderSteps();
    $('finish-title').focus();
  } else {
    const next = lessons.findIndex((_,i) => i > index && !solved.has(i));
    openLesson(next < 0 ? lessons.findIndex((_,i) => !solved.has(i)) : next, true);
  }
});
$('again').addEventListener('click', () => {
  solved.clear();
  openLesson(0,true);
});
openLesson(0);
