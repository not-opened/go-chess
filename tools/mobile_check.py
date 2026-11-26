#!/usr/bin/env python3
"""375px·320px 모바일 검증. 문항·공유·쿠팡 배너·가로 넘침을 확인한다."""
import argparse
import json
import sys

from playwright.sync_api import sync_playwright

FORBIDDEN = ("adsbygoogle", "googletagmanager", "gtag(", "웹 1호", "웹 3호", "Zero-PII")


def run(url, shot_prefix, out_json):
    result = {"url": url, "checks": [], "console_errors": [], "page_errors": [], "requests": [], "screenshots": []}

    def check(name, ok, detail=""):
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + ((" | " + str(detail)) if detail else ""))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=["--no-sandbox"])
        ctx = browser.new_context(
            viewport={"width": 375, "height": 812},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        )
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        page = ctx.new_page()
        page.on("console", lambda m: result["console_errors"].append(f"{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: result["page_errors"].append(str(e)))

        def on_request(req):
            u = req.url
            if u.startswith(url) or u.startswith("data:") or u.startswith("blob:"):
                return
            result["requests"].append(u)

        page.on("request", on_request)
        page.goto(url, wait_until="load")
        page.wait_for_timeout(400)

        html = page.content()
        for word in FORBIDDEN:
            check(f"페이지에 '{word}' 없음", word not in html)
        check("쿠팡 스크립트 1회", html.count("https://ads-partners.coupang.com/g.js") == 1)
        check("쿠팡 파트너 id", html.count('"id":1059927') == 1 and html.count('"trackingCode":"AF2725831"') == 1)
        check("수수료 문구", html.count("이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.") == 1)

        check("한국어 제목", "바둑·체스 한 수 미니" in page.title(), page.title())
        check("canonical", page.locator('link[rel="canonical"]').get_attribute("href") == "https://not-opened.github.io/go-chess/")
        check("og:image", (page.locator('meta[property="og:image"]').get_attribute("content") or "").endswith("/og.png"))
        check("twitter card", page.locator('meta[name="twitter:card"]').get_attribute("content") == "summary_large_image")
        check("JSON-LD", "WebApplication" in (page.locator('script[type="application/ld+json"]').inner_text() or ""))
        check("lang=ko", page.locator("html").get_attribute("lang") == "ko")

        tabs = page.locator(".puzzle-tab")
        check("탭 20개", tabs.count() == 20, tabs.count())
        check("오늘의 한 수 버튼 문구", len(page.locator("#dailySub").inner_text()) > 5, page.locator("#dailySub").inner_text())

        def overflow():
            return page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")

        ov = overflow()
        check("375 가로 넘침 없음", ov["sw"] <= ov["cw"] + 1, ov)

        page.locator("#dailyBtn").click()
        page.wait_for_timeout(300)
        check("오늘의 한 수 카드 강조", page.locator("#puzzleCard.is-daily").count() == 1)

        page.locator('#typeFilters .filter-chip[data-type="go"]').click()
        page.wait_for_timeout(150)
        check("바둑 필터 10문항", page.locator(".puzzle-tab").count() == 10)
        page.locator('#diffFilters .filter-chip[data-diff="고급"]').click()
        page.wait_for_timeout(150)
        check("바둑+고급 2문항", page.locator(".puzzle-tab").count() == 2)
        page.locator('#typeFilters .filter-chip[data-type="chess"]').click()
        page.wait_for_timeout(150)
        check("체스+고급 3문항", page.locator(".puzzle-tab").count() == 3)
        page.locator('#typeFilters .filter-chip[data-type="all"]').click()
        page.locator('#diffFilters .filter-chip[data-diff="all"]').click()
        page.wait_for_timeout(150)

        page.locator(".puzzle-tab").nth(0).click()
        page.wait_for_timeout(200)
        page.locator("#hintBtn").click()
        page.wait_for_timeout(150)
        hint_text = page.locator("#hintBox").inner_text()
        check("힌트 표시", len(hint_text) > 8, hint_text)
        check("힌트에 정답 좌표 없음", "5행 5열" not in hint_text, hint_text)
        page.locator("#hintBtn").click()
        page.wait_for_timeout(100)
        check("힌트 숨기기", page.locator("#hintBox").is_hidden())

        page.locator('[data-row="0"][data-col="0"]').click(force=True)
        page.wait_for_timeout(200)
        check("오답 피드백", "아쉽" in page.locator("#feedbackStatus").inner_text())
        page.locator("#retryBtn").click()
        page.wait_for_timeout(150)
        check("다시 도전 → 피드백 초기화", page.locator("#feedbackBox.show").count() == 0)

        page.locator('[data-row="4"][data-col="4"]').click(force=True)
        page.wait_for_timeout(250)
        check("바둑 정답 피드백", "정답" in page.locator("#feedbackStatus").inner_text())
        check("해설 표시", "양단수" in page.locator("#feedbackText").inner_text())
        check("정답 표기", "5행 5열" in page.locator("#feedbackAnswer").inner_text())
        check("풀이 카운트 1", page.locator("#solvedCount").inner_text() == "1")
        page.screenshot(path=f"{shot_prefix}-go-solved.png")

        page.locator(".puzzle-tab").nth(1).click()
        page.wait_for_timeout(200)
        before = page.evaluate("() => document.querySelectorAll('#boardWrap circle[fill=\"#f8fafc\"]').length")
        page.locator('[data-row="2"][data-col="3"]').click(force=True)
        page.wait_for_timeout(250)
        after = page.evaluate("() => document.querySelectorAll('#boardWrap circle[fill=\"#f8fafc\"]').length")
        check("따내기 후 백돌 제거", before == 1 and after == 0, f"백돌 {before} → {after}")

        suicide = page.evaluate("""() => {
          const m = new Map([['0,1','W'],['1,0','W'],['1,2','W'],['2,1','W']]);
          const r = window.goPlay(m, 1, 1, 'B', 9);
          return {ok:r.ok, reason:r.reason};
        }""")
        check("자충수 엔진 판정", suicide["ok"] is False and suicide.get("reason") == "suicide", suicide)

        page.locator('#typeFilters .filter-chip[data-type="chess"]').click()
        page.wait_for_timeout(200)
        page.locator(".puzzle-tab").nth(1).click()
        page.wait_for_timeout(250)
        check("체스 2번 선택", page.locator("#puzzleTitle").inner_text().startswith("2."))
        page.locator('#boardWrap rect[aria-label="e8 칸"]').click(force=True)
        page.wait_for_timeout(250)
        check("체스 정답 피드백", "정답" in page.locator("#feedbackStatus").inner_text())
        moved = page.evaluate("""() => !!document.querySelector('#boardWrap [data-piece="Q"][data-side="W"][data-square="e8"]')""")
        check("퀸이 e8로 이동", moved is True)
        page.screenshot(path=f"{shot_prefix}-chess-solved.png")

        page.locator("#retryBtn").click()
        page.wait_for_timeout(150)
        page.locator('#boardWrap rect[aria-label="a1 칸"]').click(force=True)
        page.wait_for_timeout(200)
        check("체스 오답 피드백", "아쉽" in page.locator("#feedbackStatus").inner_text())
        page.locator("#nextBtn").click()
        page.wait_for_timeout(200)
        check("다음 문제 이동", page.locator("#puzzleTitle").inner_text().startswith("3."))

        page.locator('#typeFilters .filter-chip[data-type="all"]').click()
        page.wait_for_timeout(200)
        puzzles = page.evaluate("""() => window.miniPuzzles.map(p => ({id:p.id, type:p.type, r:p.answer.r, c:p.answer.c}))""")
        bad = []
        for i, pzl in enumerate(puzzles):
            page.locator(".puzzle-tab").nth(i).click()
            page.wait_for_timeout(80)
            if pzl["type"] == "go":
                page.locator(f'[data-row="{pzl["r"]}"][data-col="{pzl["c"]}"]').click(force=True)
            else:
                file = chr(97 + pzl["c"])
                rank = 8 - pzl["r"]
                page.locator(f'#boardWrap rect[aria-label^="{file}{rank} "]').click(force=True)
            page.wait_for_timeout(80)
            status = page.locator("#feedbackStatus").inner_text()
            if "정답" not in status:
                bad.append(pzl["id"] + ":" + status)
        check("20문항 정답 탭 모두 정답", not bad, bad)
        check("20문항 모두 푼 것으로 기록", page.locator("#solvedCount").inner_text() == "20")

        page.locator("#shareBtn").click()
        page.wait_for_timeout(300)
        clip = page.evaluate("() => navigator.clipboard.readText()")
        check("공유 문구에 결과", "바둑·체스 한 수 미니" in clip and "푼 문제" in clip, clip)
        check("공유 문구에 링크", "https://not-opened.github.io/go-chess/" in clip, clip)

        footer = page.evaluate("""() => [...document.querySelectorAll('footer a')].map(a => a.textContent.trim() + ' ' + a.href)""")
        joined = " | ".join(footer)
        check("푸터 유튜브", any("youtube.com/@notopened" in x for x in footer), joined)
        check("푸터 사주", any("사주·꿈풀이·MBTI 궁합" in x and "fortune" in x for x in footer), joined)
        check("푸터 퀴즈", any("1일 1상식 두뇌 퀴즈" in x and "/quiz/" in x for x in footer), joined)

        def touch_sizes():
            return page.evaluate("""() => {
              const go = document.querySelector('#boardWrap .board-hit');
              const sq = document.querySelector('#boardWrap rect.board-hit');
              const g = go ? go.getBoundingClientRect() : null;
              const s = sq ? sq.getBoundingClientRect() : null;
              return {go: g && Math.round(g.width), sq: s && Math.round(s.width)};
            }""")

        page.locator('#typeFilters .filter-chip[data-type="go"]').click()
        page.wait_for_timeout(150)
        t375 = touch_sizes()
        check("375 바둑 터치 영역", (t375["go"] or 0) >= 30, t375)
        page.locator('#typeFilters .filter-chip[data-type="chess"]').click()
        page.wait_for_timeout(150)
        c375 = touch_sizes()
        check("375 체스 칸 크기", (c375["sq"] or 0) >= 34, c375)

        def settle_banner():
            for _ in range(8):
                page.evaluate("() => { if (window.fitCoupangBanner) window.fitCoupangBanner(); }")
                has = page.evaluate("() => !!document.querySelector('#coupangSlot iframe')")
                if has:
                    break
                page.wait_for_timeout(400)
            page.wait_for_timeout(200)

        settle_banner()
        banner = page.evaluate("""() => {
          const frame = document.querySelector('#coupangSlot iframe');
          const note = document.querySelector('.affiliate-note');
          return {hasFrame: !!frame, note: note ? note.textContent : '', w: frame ? frame.getAttribute('width') : null};
        }""")
        check("쿠팡 배너 iframe", banner["hasFrame"] is True, banner)
        check("수수료 문구가 배너 옆", "쿠팡 파트너스 활동의 일환으로" in (banner["note"] or ""))
        ov_ad = overflow()
        check("375 배너 뒤 가로 넘침 없음", ov_ad["sw"] <= ov_ad["cw"] + 1, ov_ad)

        page.set_viewport_size({"width": 320, "height": 700})
        page.wait_for_timeout(250)
        page.evaluate("() => { if (window.fitCoupangBanner) window.fitCoupangBanner(); }")
        page.wait_for_timeout(200)
        ov320 = overflow()
        check("320 가로 넘침 없음", ov320["sw"] <= ov320["cw"] + 1, ov320)
        page.locator('#typeFilters .filter-chip[data-type="go"]').click()
        page.wait_for_timeout(150)
        t320 = touch_sizes()
        check("320 바둑 터치 영역", (t320["go"] or 0) >= 28, t320)
        page.locator('#typeFilters .filter-chip[data-type="chess"]').click()
        page.wait_for_timeout(150)
        c320 = touch_sizes()
        check("320 체스 칸 크기", (c320["sq"] or 0) >= 30, c320)
        page.screenshot(path=f"{shot_prefix}-320.png", full_page=True)
        result["screenshots"].append(f"{shot_prefix}-320.png")

        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(200)
        ov_bottom = overflow()
        check("320 하단 가로 넘침 없음", ov_bottom["sw"] <= ov_bottom["cw"] + 1, ov_bottom)
        page.screenshot(path=f"{shot_prefix}-375-full.png", full_page=True)

        base = url if url.endswith("/") else url + "/"
        page.goto(base + "privacy.html", wait_until="load")
        page.set_viewport_size({"width": 320, "height": 700})
        page.wait_for_timeout(200)
        pov = overflow()
        check("개인정보 320 가로 넘침 없음", pov["sw"] <= pov["cw"] + 1, pov)
        privacy_html = page.content()
        check("개인정보 방침에 쿠팡 쿠키 안내", "쿠팡" in privacy_html and "쿠키" in privacy_html)
        check("개인정보에 자체 수집 없음", "개인정보" in privacy_html)

        allowed = ("coupang.com", "coupangcdn.com")
        unexpected = [u for u in result["requests"] if not any(host in u for host in allowed)]
        check("쿠팡 외 외부 요청 없음", not unexpected, unexpected[:8])

        browser.close()

    result["console_error_count"] = len(result["console_errors"])
    result["page_error_count"] = len(result["page_errors"])
    print(f"\n콘솔 에러 {len(result['console_errors'])}건 / 페이지 에러 {len(result['page_errors'])}건")
    for e in result["console_errors"][:12]:
        print("  console:", e)
    for e in result["page_errors"][:12]:
        print("  pageerror:", e)
    passed = sum(1 for c in result["checks"] if c["ok"])
    result["passed"] = passed
    result["total"] = len(result["checks"])
    print(f"체크 통과 {passed}/{len(result['checks'])}")
    if out_json:
        json.dump(result, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    clean = passed == len(result["checks"]) and not result["console_errors"] and not result["page_errors"]
    return 0 if clean else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8777/")
    ap.add_argument("--shot-prefix", default="/tmp/go-chess-mobile")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    sys.exit(run(a.url, a.shot_prefix, a.json))
