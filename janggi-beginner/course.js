'use strict';

const lessons = [
  {
    tab: '포 넘기', title: '포는 무엇을 넘을 수 있을까?',
    prompt: '가운데 한(빨강) 포를 눌러, 갈 수 있는 점을 찾아보세요.',
    hint: '도착점과 내 포 사이에 어떤 말이 몇 개 있는지 보세요.',
    origin: [5,4,'P'], extras: [[5,3,'P','cho'], [5,5,'S']],
    options: [
      [5,1,'포는 포를 뛰어넘을 수 없어요. 왼쪽에는 초의 포가 있어요.'],
      [5,7],
      [3,4,'위쪽에는 넘을 말이 없어요. 포는 빈 줄을 혼자 달릴 수 없어요.']
    ],
    answer: 1, rule: '오른쪽의 한 병(兵) 하나를 넘었어요. 포는 포가 아닌 말 딱 하나를 넘어야 움직일 수 있어요.'
  },
  {
    tab: '포 잡기', title: '포로 어떤 말을 잡을 수 있을까?',
    prompt: '한 포를 움직여 상대 말 하나를 잡아 보세요.',
    hint: '넘을 말뿐 아니라, 도착점에 있는 말이 무엇인지도 보세요.',
    origin: [4,2,'P'], extras: [[4,3,'S'], [4,5,'P','cho'], [5,2,'R'], [7,2,'S','cho']],
    options: [
      [4,5,'병 하나를 넘을 수는 있지만, 포로 상대 포를 잡을 수 없어요.'],
      [4,6,'그 점까지는 병과 포, 말 두 개가 길에 있어요. 포는 말 하나만 넘을 수 있어요.'],
      [7,2]
    ],
    answer: 2, rule: '아래쪽의 한 차(車)를 넘어 초 졸(卒)을 잡았어요. 포는 포 말고 다른 상대 말을 잡을 수 있어요.'
  },
  {
    tab: '마의 길목', title: '마도 길이 막힐까?',
    prompt: '한 마(馬)가 실제로 갈 수 있는 점을 찾으세요.',
    hint: '두 칸 가는 방향으로 먼저 한 칸 곧게 가는 길이 비어 있어야 해요.',
    origin: [6,4,'M'], extras: [[5,4,'S']],
    options: [
      [7,6],
      [4,3,'위쪽으로 가는 첫 길목을 바로 앞의 한 병이 막고 있어요.'],
      [4,5,'도착점이 비어 있어도 첫 길목이 막히면 못 가요. 위로 가는 길에 한 병이 있어요.']
    ],
    answer: 0, rule: '오른쪽 첫 길목이 비어서 갈 수 있었어요. 마의 첫 길목을 ‘멱’이라고 해요.'
  },
  {
    tab: '차와 궁성', title: '차가 대각선으로 갈 수 있을까?',
    prompt: '아래 궁성 모서리의 한 차(車)를 눌러 표시된 점 중 갈 곳을 골라 보세요.',
    hint: '판 아래쪽 궁성에서 대각선이 실제로 그어진 방향을 보세요.',
    origin: [9,3,'R'], extras: [],
    options: [
      [8,2,'왼쪽 위로는 대각선이 그어져 있지 않아요. 차가 아무 대각선이나 갈 수 있는 건 아니에요.'],
      [7,5],
      [7,4,'거기까지는 한 줄로 이어지지 않아요. 차는 한 수 안에서 방향을 꺾을 수 없어요.']
    ],
    answer: 1, rule: '궁성 모서리에서 가운데 점을 지나 반대편 모서리까지, 그어진 대각선 한 줄을 따라갔어요.'
  },
  {
    tab: '병 한 칸', title: '병은 옆으로 갈 수 있을까?',
    prompt: '움직일 한 병(兵)을 눌러, 표시된 점 중 갈 곳을 찾아보세요.',
    hint: '보통 자리에서는 앞으로 한 칸, 또는 옆으로 한 칸을 생각해 보세요.',
    origin: [4,5,'S'], extras: [],
    options: [
      [5,5,'한의 전진 방향은 화면 위쪽이에요. 바로 아래로 가는 수는 후진이라 안 돼요.'],
      [3,6,'궁성이 아닌 곳에서는 병이 대각선으로 갈 수 없어요.'],
      [4,6]
    ],
    answer: 2, rule: '오른쪽으로 한 칸 갔어요. 궁성 밖에서 졸과 병은 앞으로나 옆으로 한 칸씩 가고, 뒤로는 못 가요.'
  }
];

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
  if (finishedMove) {
    const [r,c] = p.origin;
    svg.append(svgEl('line', {x1:c+.5,y1:r+.5,x2:dest[1]+.5,y2:dest[0]+.5,stroke:'#195340','stroke-width':'.12','stroke-dasharray':'.13 .12'}));
    svg.append(svgEl('circle',{cx:c+.5,cy:r+.5,r:'.1',fill:'#195340'}));
  }
  board.replaceChildren(svg);
  const origin = finishedMove ? [dest[0],dest[1],p.origin[2]] : p.origin;
  const others = [...fixed,...p.extras].filter(piece => !finishedMove || !same(piece,dest));
  [origin,...others].forEach(piece => {
    const canMove = piece === origin && !finishedMove;
    const el = document.createElement(canMove ? 'button' : 'span');
    const [glyph, name] = describe(piece);
    el.className = 'token' + (piece[3] === 'cho' ? ' cho' : '');
    el.textContent = glyph;
    el.setAttribute('aria-label', name + ', ' + position(piece) + (canMove ? ', 움직일 말' : ''));
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
  feedback('맞았어요!', p.rule, 'ok');
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
