#!/usr/bin/env python3
"""390px 모바일 뷰포트 라이브/로컬 검증 스크립트."""
import argparse
import json
import sys
import time
from playwright.sync_api import sync_playwright

def run(url, shot_prefix, out_json):
    result = {"url": url, "checks": [], "console_errors": [], "page_errors": [], "screenshots": []}

    def check(name, ok, detail=""):
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + ((" | " + str(detail)) if detail else ""))

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                  is_mobile=True, has_touch=True,
                                  user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
        page = ctx.new_page()
        page.on("console", lambda m: result["console_errors"].append(f"{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: result["page_errors"].append(str(e)))
        page.goto(url, wait_until="load")
        page.wait_for_timeout(700)

        # 1) 기본 로드
        check("타이틀 렌더", page.title().startswith("notopened 바둑·체스"), page.title())
        tabs = page.locator(".puzzle-tab")
        check("탭 20개", tabs.count() == 20, tabs.count())
        check("오늘의 한 수 버튼 문구", len(page.locator("#dailySub").inner_text()) > 5, page.locator("#dailySub").inner_text())

        # 2) 가로 오버플로
        ov = page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, bw: document.body.scrollWidth})")
        check("가로 오버플로 없음", ov["sw"] <= ov["cw"], ov)

        # 3) 오늘의 한 수 클릭 → 해당 문항 표시
        page.locator("#dailyBtn").click()
        page.wait_for_timeout(600)
        check("오늘의 한 수 카드 강조", page.locator("#puzzleCard.is-daily").count() == 1)
        daily_title = page.locator("#puzzleTitle").inner_text()
        check("오늘의 한 수 제목 표시", len(daily_title) > 3, daily_title)

        # 4) 필터: 바둑 / 체스 / 난이도
        page.locator('#typeFilters .filter-chip[data-type="go"]').click()
        page.wait_for_timeout(200)
        check("바둑 필터 10문항", page.locator(".puzzle-tab").count() == 10, page.locator(".puzzle-tab").count())
        page.locator('#diffFilters .filter-chip[data-diff="고급"]').click()
        page.wait_for_timeout(200)
        check("바둑+고급 2문항", page.locator(".puzzle-tab").count() == 2, page.locator(".puzzle-tab").count())
        page.locator('#typeFilters .filter-chip[data-type="chess"]').click()
        page.wait_for_timeout(200)
        check("체스+고급 3문항", page.locator(".puzzle-tab").count() == 3, page.locator(".puzzle-tab").count())
        page.locator('#diffFilters .filter-chip[data-diff="all"]').click()
        page.wait_for_timeout(200)
        check("체스 전체 10문항", page.locator(".puzzle-tab").count() == 10, page.locator(".puzzle-tab").count())

        # 5) 바둑 입문 1번: 힌트 → 오답 → 정답
        page.locator('#typeFilters .filter-chip[data-type="all"]').click()
        page.wait_for_timeout(200)
        page.locator(".puzzle-tab").nth(0).click()
        page.wait_for_timeout(300)
        page.locator("#hintBtn").click()
        page.wait_for_timeout(250)
        hint_text = page.locator("#hintBox").inner_text()
        check("힌트 표시", len(hint_text) > 8, hint_text)
        check("힌트에 정답 좌표 없음", "5행 5열" not in hint_text, hint_text)
        page.locator("#hintBtn").click()
        page.wait_for_timeout(200)
        check("힌트 숨기기", page.locator("#hintBox").is_hidden())

        page.locator('circle[data-row="0"][data-col="0"]').click(force=True)
        page.wait_for_timeout(300)
        check("오답 피드백", "아쉽" in page.locator("#feedbackStatus").inner_text(), page.locator("#feedbackStatus").inner_text())
        page.locator("#retryBtn").click()
        page.wait_for_timeout(300)
        check("다시 도전 → 피드백 초기화", page.locator("#feedbackBox.show").count() == 0)

        page.locator('circle[data-row="4"][data-col="4"]').click(force=True)
        page.wait_for_timeout(400)
        check("바둑 정답 피드백", "정답" in page.locator("#feedbackStatus").inner_text(), page.locator("#feedbackStatus").inner_text())
        check("해설 표시", "양단수" in page.locator("#feedbackText").inner_text())
        check("정답 표기", "5행 5열" in page.locator("#feedbackAnswer").inner_text(), page.locator("#feedbackAnswer").inner_text())
        check("풀이 카운트 1", page.locator("#solvedCount").inner_text() == "1", page.locator("#solvedCount").inner_text())
        page.screenshot(path=f"{shot_prefix}-go-solved.png", full_page=False)

        # 6) 바둑 따내기(go-02): 정답 착수 후 백돌이 사라지는지
        page.locator(".puzzle-tab").nth(1).click()
        page.wait_for_timeout(300)
        before = page.evaluate("() => document.querySelectorAll('#boardWrap circle[fill=\"#f8fafc\"]').length")
        page.locator('circle[data-row="2"][data-col="3"]').click(force=True)
        page.wait_for_timeout(400)
        after = page.evaluate("() => document.querySelectorAll('#boardWrap circle[fill=\"#f8fafc\"]').length")
        check("따내기 후 백돌 제거", before == 1 and after == 0, f"백돌 {before} → {after}")
        check("따내기 토스트", "따냈습니다" in page.locator("#toast").inner_text(), page.locator("#toast").inner_text())
        page.wait_for_timeout(1900)

        # 7) 바둑 엔진 자충수 판정 (go-06 설명의 '백은 메울 수 없는 자리' 근거)
        suicide = page.evaluate("""() => {
          const m = new Map([['0,1','W'],['1,0','W'],['1,2','W'],['2,1','W']]);
          const r = window.goPlay(m, 1, 1, 'B', 9);
          return {ok:r.ok, reason:r.reason};
        }""")
        check("자충수 엔진 판정", suicide["ok"] is False and suicide.get("reason") == "suicide", suicide)
        page.locator(".puzzle-tab").nth(5).click()
        page.wait_for_timeout(300)
        check("go-06 문제 표시", page.locator("#puzzleTitle").inner_text().startswith("6."), page.locator("#puzzleTitle").inner_text())
        page.locator('circle[data-row="3"][data-col="4"]').click(force=True)
        page.wait_for_timeout(400)
        check("go-06 오답 → 해설 표시", page.locator("#feedbackBox.show").count() == 1)

        # 8) 체스: 2번(퀸+킹) 정답 → 기물 이동 + 체크메이트 해설
        page.locator('#typeFilters .filter-chip[data-type="chess"]').click()
        page.wait_for_timeout(300)
        page.locator(".puzzle-tab").nth(1).click()
        page.wait_for_timeout(400)
        title2 = page.locator("#puzzleTitle").inner_text()
        check("체스 2번 선택", title2.startswith("2."), title2)
        page.screenshot(path=f"{shot_prefix}-chess-q2-before.png", full_page=False)
        sq = page.locator('#boardWrap rect[aria-label="e8 칸"]')
        check("체스 e8 칸 존재", sq.count() == 1, sq.count())
        sq.click(force=True)
        page.wait_for_timeout(400)
        check("체스 정답 피드백", "정답" in page.locator("#feedbackStatus").inner_text(), page.locator("#feedbackStatus").inner_text())
        check("체스 정답 표기", "Qe8#" in page.locator("#feedbackAnswer").inner_text(), page.locator("#feedbackAnswer").inner_text())
        check("해설 체크메이트", "Qe8#" in page.locator("#feedbackText").inner_text())
        # 기물이 e8 로 이동했는지 (백 퀸 글리프가 e8 칸 중앙에 있는지)
        moved = page.evaluate("""() => {
          const nodes=[...document.querySelectorAll('#boardWrap text')];
          const whites=nodes.filter(e=>e.getAttribute('fill')==='#ffffff').map(e=>({x:+e.getAttribute('x'),y:+e.getAttribute('y'),s:e.textContent}));
          return {count:nodes.filter(e=>e.textContent.length===1&&/\\u2650-\\u265F/.test(e.textContent)).length, whites:whites};
        }""")
        exp = {"x": 16 + 4*42 + 21, "y": 0 + 0*42 + 42*0.72}
        hit = [w for w in moved["whites"] if abs(w["x"]-exp["x"]) < 1.5 and abs(w["y"]-exp["y"]) < 1.5]
        check("퀸이 e8로 이동", len(hit) == 1, moved)
        page.screenshot(path=f"{shot_prefix}-chess-q2-solved.png", full_page=False)

        # 9) 체스 오답 → 재도전
        page.locator("#retryBtn").click()
        page.wait_for_timeout(300)
        page.locator('#boardWrap rect[aria-label="a1 칸"]').click(force=True)
        page.wait_for_timeout(300)
        check("체스 오답 피드백", "아쉽" in page.locator("#feedbackStatus").inner_text())

        # 10) 다음 문제 / 하단 링크
        page.locator("#nextBtn").click()
        page.wait_for_timeout(400)
        check("다음 문제 이동", page.locator("#puzzleTitle").inner_text().startswith("3."), page.locator("#puzzleTitle").inner_text())
        links = page.evaluate("""() => [...document.querySelectorAll('.cross-promo a')].map(a=>a.href)""")
        check("웹1호 링크", "https://not-opened.github.io/quiz/" in links, links)
        check("웹3호 링크", "https://not-opened.github.io/fortune/" in links, links)

        # 11) 하단까지 스크롤 후 오버플로 재확인 + 전체 스크린샷
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(300)
        ov2 = page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
        check("하단 가로 오버플로 없음", ov2["sw"] <= ov2["cw"], ov2)
        page.locator("#affiliateSection").scroll_into_view_if_needed()
        page.wait_for_timeout(1200)
        page.screenshot(path=f"{shot_prefix}-bottom.png", full_page=False)
        page.evaluate("() => window.scrollTo(0,0)")
        page.wait_for_timeout(300)
        page.screenshot(path=f"{shot_prefix}-full.png", full_page=True)
        result["screenshots"] += [f"{shot_prefix}-full.png", f"{shot_prefix}-bottom.png", f"{shot_prefix}-go-solved.png",
                                  f"{shot_prefix}-chess-q2-before.png", f"{shot_prefix}-chess-q2-solved.png"]

        # 12) 쿠팡 파트너스 배너: 렌더/오버플로/공정위 문구
        page.wait_for_timeout(2500)
        banner = page.evaluate("""() => {
          const sec=document.getElementById('affiliateSection');
          const wrap=document.getElementById('coupangWrap');
          const slot=document.getElementById('coupangSlot');
          const f=slot?slot.querySelector('iframe'):null;
          const note=document.querySelector('.affiliate-note');
          const r=wrap?wrap.getBoundingClientRect():null;
          return {hidden: sec?sec.hidden:null, hasFrame: !!f,
                  frameW: f?f.getAttribute('width'):null, frameH: f?f.getAttribute('height'):null,
                  wrapW: wrap?wrap.clientWidth:null, wrapH: wrap?wrap.clientHeight:null,
                  wrapScrollW: wrap?wrap.scrollWidth:null,
                  scale: slot?getComputedStyle(slot).transform:null,
                  note: note?note.innerText:null,
                  docSW: document.documentElement.scrollWidth, docCW: document.documentElement.clientWidth};
        }""")
        check("쿠팡 배너 섹션 노출", banner["hidden"] is False, banner)
        check("쿠팡 배너 iframe 렌더", banner["hasFrame"] is True, banner)
        sc = banner.get("scale") or "none"
        try:
            scv = float(sc.split("(")[1].split(",")[0]) if sc.startswith("matrix") else 1.0
        except Exception:
            scv = 1.0
        expect = (banner["wrapW"] or 0) / 680.0
        check("쿠팡 배너 폭 맞춤(축소)", abs(scv - expect) < 0.05, {"scale": scv, "expect": round(expect,3)})
        check("공정위 문구 표시", "쿠팡 파트너스 활동의 일환으로" in (banner["note"] or ""), banner["note"])
        check("배너 삽입 후 가로 오버플로 0", banner["docSW"] <= banner["docCW"], banner)
        page.locator("#affiliateSection").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.locator("#affiliateSection").screenshot(path=f"{shot_prefix}-coupang-banner.png")
        result["screenshots"].append(f"{shot_prefix}-coupang-banner.png")

        # 개인정보처리방침 링크 동작
        base = url.rsplit("/", 1)[0] + "/"
        privacy = page.evaluate("() => document.querySelector('a[href=\"./privacy.html\"]').href")
        check("privacy 링크 존재", privacy.endswith("privacy.html"), privacy)

        browser.close()

    result["console_error_count"] = len(result["console_errors"])
    result["page_error_count"] = len(result["page_errors"])
    print(f"\n콘솔 에러 {len(result['console_errors'])}건 / 페이지 에러 {len(result['page_errors'])}건")
    for e in result["console_errors"][:10]:
        print("  console:", e)
    for e in result["page_errors"][:10]:
        print("  pageerror:", e)
    passed = sum(1 for c in result["checks"] if c["ok"])
    result["passed"] = passed
    result["total"] = len(result["checks"])
    print(f"체크 통과 {passed}/{len(result['checks'])}")
    if out_json:
        json.dump(result, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if (passed == len(result["checks"]) and not result["console_errors"] and not result["page_errors"]) else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8777/")
    ap.add_argument("--shot-prefix", default="/workspace/downloads/go-chess-v2-local-390")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    sys.exit(run(a.url, a.shot_prefix, a.json))
