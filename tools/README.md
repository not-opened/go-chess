# tools — 문항 검산·생성 도구

이 폴더는 `index.html` 에 들어가는 20문항과 그 검산을 재현하기 위한 도구입니다.
사이트 동작에는 영향이 없습니다(정적 파일).

| 파일 | 역할 |
| --- | --- |
| `puzzle_data.py` | 20문항 원본(바둑 10 · 체스 10). 제목·문제·힌트·해설·시작 배치·정답·검산 스펙 |
| `goban.py` | 9×9 바둑 규칙 엔진(활로·따내기·자충수·집/눈) |
| `predicates.py` | 바둑 검산 프리디케이트(따내기/양단수/단수 후 사망/패/두 눈) |
| `verify_puzzles.py` | 20문항 전수 검산. `index.html` 에 박힌 JSON 을 읽어 규칙 검증 |
| `render_puzzles.py` | `site_template.html` + `puzzle_data.py` → `index.html` 생성 |
| `site_template.html` | 화면 템플릿(`__PUZZLES_JSON__` 자리에 문항 JSON 삽입) |
| `mobile_check.py` | Playwright 375·320px 모바일 검증(탭·필터·힌트·정오답·공유·가로 넘침) |

## 사용법

```bash
pip install python-chess playwright
python3 tools/render_puzzles.py     # 템플릿 + 데이터 → index.html
python3 tools/verify_puzzles.py     # 20문항 검산 (index.html 기준)
python3 tools/verify_puzzles.py --data   # 데이터 원본만 검산
python3 tools/mobile_check.py --url http://127.0.0.1:8777/
```

## 검산 기준

- **바둑**: 초기 배치의 모든 그룹이 활로 ≥1(직전 수 불법 아님), 정답 자리가 빈 점이며 흑의 합법수(자충수 아님),
  목표 달성 수가 **정답 하나뿐**임을 전수 확인.
  - `capture`: 정답이 N점을 따내고, N점 이상 따내는 다른 수가 없음
  - `double_atari`: 두 그룹이 각각 활로 1이 되는 수가 유일
  - `atari_dead`: 정답 뒤 백이 어떤 수를 두어도 다음 수에 잡힘(2수 읽기)
  - `ko`: 정답이 1점을 따내고 백의 즉시 되따냄이 같은 국면을 반복(패 규칙 위반)
  - `two_eyes` / `kill_nakade`: 정답 뒤 흑(백)의 진짜 집 개수 계산
- **체스**: python-chess 로 FEN 합법성·차례·백 체크 아님 확인, 정답 SAN 이 합법수이고 도착칸이 일치,
  화면에 그린 기물이 FEN 과 일치.
  - `mate`: 1수 메이트가 **유일**하고 그것이 정답
  - `fork`: 체크 + 목표 기물 공격 수가 유일하고, 흑의 모든 응수 뒤 목표 기물을 얻음
  - `skewer`: 같은 줄에서 킹 뒤 기물을 노리는 수가 유일하고, 흑의 모든 응수 뒤 기물을 얻음
- 모든 문항: 힌트에 정답 좌표가 노출되지 않음, 정답 표기 텍스트와 내부 좌표 일치.
