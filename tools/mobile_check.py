#!/usr/bin/env python3
"""모바일 검증 — 30문항(바둑·체스·장기)·장기 조작·공유·쿠팡 배너·가로 넘침.

    python3 tools/mobile_check.py --url http://127.0.0.1:8777/
    python3 tools/mobile_check.py --url https://not-opened.github.io/go-chess/ \\
        --viewport 390x844 --shot-prefix downloads/go-chess-v3-janggi-390
"""
import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

FORBIDDEN = ("adsbygoogle", "googletagmanager", "gtag(", "웹 1호", "웹 3호", "Zero-PII", "출시 예정")

HERE = os.path.dirname(os.path.abspath(__file__))


def run(url, shot_prefix, out_json, vw, vh):
    result = {"url": url, "viewport": f"{vw}x{vh}", "checks": [], "console_errors": [],
              "page_errors": [], "requests": [], "screenshots": []}

    def check(name, ok, detail=""):
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail if detail == "" else str(detail)})
        print(("PASS " if ok else "FAIL ") + name + ((" | " + str(detail)) if detail != "" else ""))

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", args=["--no-sandbox"])
        except Exception:
            browser = pw.chromium.launch(args=["--no-sandbox"])
        ctx = browser.new_context(
            viewport={"width": vw, "height": vh},
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
        page.wait_for_timeout(500)

        html = page.content()
        for word in FORBIDDEN:
            check(f"페이지에 '{word}' 없음", word not in html)
        check("쿠팡 스크립트 1회", html.count("https://ads-partners.coupang.com/g.js") == 1)
        check("쿠팡 파트너 id", html.count('"id":1059927') == 1 and html.count('"trackingCode":"AF2725831"') == 1)
        check("수수료 문구 1회", html.count("이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.") == 1)
        check("애드센스 없음", "pagead2" not in html and "ca-pub-" not in html)

        check("제목", "바둑·체스·장기 한 수 미니" in page.title(), page.title())
        check("canonical", page.locator('link[rel="canonical"]').get_attribute("href") == "https://not-opened.github.io/go-chess/")
        check("og:image", (page.locator('meta[property="og:image"]').get_attribute("content") or "").endswith("/og.png"))
        check("og:description 30문항", "30문항" in (page.locator('meta[property="og:description"]').get_attribute("content") or ""))
        check("twitter card", page.locator('meta[name="twitter:card"]').get_attribute("content") == "summary_large_image")
        check("JSON-LD", "WebApplication" in (page.locator('script[type="application/ld+json"]').inner_text() or ""))
        check("lang=ko", page.locator("html").get_attribute("lang") == "ko")

        # ---------- 헤더: 유튜브 배너 최상단 + 배지 제거 ----------
        banner = page.locator(".yt-banner")
        check("유튜브 배너 1개", banner.count() == 1, banner.count())
        if banner.count() == 1:
            href = banner.get_attribute("href")
            check("유튜브 링크", href == "https://www.youtube.com/@notopened", href)
            check("새 탭 target=_blank", banner.get_attribute("target") == "_blank")
            rel = banner.get_attribute("rel") or ""
            check("rel=noopener noreferrer", "noopener" in rel and "noreferrer" in rel, rel)
            box = banner.bounding_box()
            check("배너 높이 44px 이상", box and box["height"] >= 44, box and round(box["height"]))
            fit = page.evaluate("""() => {
              const b = document.querySelector('.yt-banner');
              const t = b.querySelector('.yt-text');
              const br = b.getBoundingClientRect();
              const tr = t.getBoundingClientRect();
              return {
                inside: tr.top >= br.top - 1 && tr.bottom <= br.bottom + 1,
                text: t.textContent
              };
            }""")
            check("유튜브 배너 문구가 잘리지 않음", fit["inside"] and "보러가기" in fit["text"], fit)
            hbox = page.locator(".portal-header").bounding_box()
            check("배너가 헤더보다 위", box and hbox and box["y"] < hbox["y"], (box and round(box["y"]), hbox and round(hbox["y"])))
            check("배너 문구", "유튜브" in banner.inner_text(), banner.inner_text())
        check("상단 배지 제거", page.locator(".header-top-row, .badge").count() == 0)
        check("효과음 버튼 유지", page.locator("#soundToggleBtn").count() == 1)
        check("가로 넘침 없음(배너)", page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"))

        # ---------- 문항 수·필터 ----------
        check("진행 표시 30", page.locator("#totalCount").inner_text() == "30", page.locator("#totalCount").inner_text())
        tabs = page.locator(".puzzle-tab")
        check("탭 30개", tabs.count() == 30, tabs.count())
        for typ, n in (("go", 10), ("chess", 10), ("janggi", 10)):
            page.locator(f'#typeFilters .filter-chip[data-type="{typ}"]').click()
            page.wait_for_timeout(150)
            check(f"{typ} 필터 {n}문항", page.locator(".puzzle-tab").count() == n, page.locator(".puzzle-tab").count())
        page.locator('#typeFilters .filter-chip[data-type="janggi"]').click()
        page.locator('#diffFilters .filter-chip[data-diff="입문"]').click()
        page.wait_for_timeout(150)
        check("장기+입문 4문항", page.locator(".puzzle-tab").count() == 4)
        page.locator('#diffFilters .filter-chip[data-diff="고급"]').click()
        page.wait_for_timeout(150)
        check("장기+고급 3문항", page.locator(".puzzle-tab").count() == 3)
        page.locator('#diffFilters .filter-chip[data-diff="all"]').click()
        page.wait_for_timeout(150)

        # ---------- 장기 보드 ----------
        check("장기판 히트칸 90", page.locator("#boardWrap rect.jg-hit").count() == 90, page.locator("#boardWrap rect.jg-hit").count())
        hit375 = page.evaluate("""() => {
          const h = document.querySelector('#boardWrap rect.jg-hit');
          return h ? Math.round(h.getBoundingClientRect().width) : 0;
        }""")
        check("375 장기 터치 영역", hit375 >= 30, hit375)
        check("장기 범례 표시", not page.locator("#janggiLegend").is_hidden())
        check("장기 타입 표기", "장기" in page.locator("#puzzleTypePill").inner_text(), page.locator("#puzzleTypePill").inner_text())
        check("장기 정답 문구", "행" in page.evaluate("() => window.miniPuzzles.find(p => p.type==='janggi').answerText"))
        piece_count = page.evaluate("() => window.miniPuzzles.find(p => p.type==='janggi').pieces.length")
        check("장기 기물 수 일치", page.locator("#boardWrap text.jg-piece").count() == piece_count, (page.locator("#boardWrap text.jg-piece").count(), piece_count))

        # ---------- 장기: 기물 선택 → 착수(정답) ----------
        page.locator(".puzzle-tab").nth(0).click()
        page.wait_for_timeout(200)
        ans = page.evaluate("""() => {
          const p = window.miniPuzzles.find(x => x.id === 'janggi-01');
          return {from: [p.answer.from.r, p.answer.from.c], to: [p.answer.to.r, p.answer.to.c], text: p.answerText};
        }""")
        page.locator(f'[data-row="{ans["from"][0]}"][data-col="{ans["from"][1]}"]').click(force=True)
        page.wait_for_timeout(200)
        check("기물 선택 표시", page.evaluate("() => document.querySelectorAll('#boardWrap circle[stroke=\"#0ea5e9\"]').length") >= 1)
        check("갈 수 있는 칸 표시", page.evaluate("() => document.querySelectorAll('#boardWrap circle[fill=\"rgba(14, 165, 233, 0.55)\"]').length") >= 1)
        page.locator(f'[data-row="{ans["to"][0]}"][data-col="{ans["to"][1]}"]').click(force=True)
        page.wait_for_timeout(250)
        check("장기 정답 피드백", "정답" in page.locator("#feedbackStatus").inner_text(), page.locator("#feedbackStatus").inner_text())
        check("장기 해설", len(page.locator("#feedbackText").inner_text()) > 20)
        check("장기 정답 표기", ans["text"] in page.locator("#feedbackAnswer").inner_text(),
              (ans["text"], page.locator("#feedbackAnswer").inner_text()))
        check("풀이 카운트 1", page.locator("#solvedCount").inner_text() == "1", page.locator("#solvedCount").inner_text())
        page.screenshot(path=f"{shot_prefix}-solved.png")
        result["screenshots"].append(f"{shot_prefix}-solved.png")

        # ---------- 장기: 재도전·힌트·오답 ----------
        page.locator("#retryBtn").click()
        page.wait_for_timeout(200)
        check("재도전 → 피드백 초기화", page.locator("#feedbackBox.show").count() == 0)
        page.locator("#hintBtn").click()
        page.wait_for_timeout(150)
        hint = page.locator("#hintBox").inner_text()
        check("힌트 표시", len(hint) > 8, hint)
        check("힌트에 정답 좌표 없음", "9행 7열" not in hint and "3행 7열" not in hint, hint)
        page.locator("#hintBtn").click()
        page.wait_for_timeout(120)

        # 다른 장기 문항에서 '움직일 수 있는 아군 기물'을 골라 엉뚱한 칸에 두면 오답 처리
        page.locator(".puzzle-tab").nth(4).click()
        page.wait_for_timeout(200)
        wrong = page.evaluate("""() => {
          const p = window.miniPuzzles.find(x => x.id === 'janggi-05');
          const map = new Map(p.pieces.map(x => [x.r + ',' + x.c, x]));
          const pick = p.pieces.find(x => x.side === 'han' && x.kind === 'R');
          const from = [pick.r, pick.c];
          const moves = window.jgLegalMovesFrom(map, from, 'han');
          const ans = p.answer;
          const alt = moves.find(m => !(m[0] === ans.to.r && m[1] === ans.to.c));
          return {from: from, to: alt || null};
        }""")
        if wrong.get("to"):
            page.locator(f'[data-row="{wrong["from"][0]}"][data-col="{wrong["from"][1]}"]').click(force=True)
            page.wait_for_timeout(120)
            page.locator(f'[data-row="{wrong["to"][0]}"][data-col="{wrong["to"][1]}"]').click(force=True)
            page.wait_for_timeout(200)
            check("장기 오답 피드백", "아쉽" in page.locator("#feedbackStatus").inner_text(), page.locator("#feedbackStatus").inner_text())
            check("오답도 실제 이동 표시", page.evaluate("() => !!document.querySelector('#boardWrap circle[stroke=\"#ef4444\"]')"))
            page.locator("#retryBtn").click()
            page.wait_for_timeout(150)
        else:
            check("장기 오답 후보 존재", False, "합법수 없음")
        page.locator("#nextBtn").click()
        page.wait_for_timeout(200)
        check("다음 문제 이동", page.locator("#puzzleTitle").inner_text().startswith("6."))

        # ---------- JS 장기 엔진 ↔ 파이썬 엔진 대조 ----------
        expected_path = os.path.join(HERE, "janggi_legal_expected.json")
        if os.path.exists(expected_path):
            expected = json.load(open(expected_path, encoding="utf-8"))
            diffs = []
            for item in expected:
                got = page.evaluate("""(id) => {
                  const p = window.miniPuzzles.find(x => x.id === id);
                  const map = new Map(p.pieces.map(x => [x.r + ',' + x.c, {kind:x.kind, side:x.side, symbol:x.symbol}]));
                  const out = [];
                  p.pieces.filter(x => x.side === 'han').forEach(x => {
                    window.jgLegalMovesFrom(map, [x.r, x.c], 'han').forEach(d => out.push(x.r + ',' + x.c + '>' + d[0] + ',' + d[1]));
                  });
                  return out.sort();
                }""", item["id"])
                if sorted(item["moves"]) != got:
                    diffs.append({"id": item["id"], "py": len(item["moves"]), "js": len(got),
                                  "onlyPy": [m for m in item["moves"] if m not in got][:6],
                                  "onlyJs": [m for m in got if m not in item["moves"]][:6]})
            check("장기 JS·파이썬 합법수 일치(10문항)", not diffs, diffs)
        else:
            check("장기 합법수 기대값 파일", False, expected_path)

        # ---------- 바둑/체스 기존 동작 ----------
        page.locator('#typeFilters .filter-chip[data-type="go"]').click()
        page.wait_for_timeout(150)
        page.locator(".puzzle-tab").nth(0).click()
        page.wait_for_timeout(200)
        page.locator("#hintBtn").click()
        page.wait_for_timeout(120)
        check("바둑 힌트", len(page.locator("#hintBox").inner_text()) > 8)
        page.locator("#hintBtn").click()
        page.locator('[data-row="0"][data-col="0"]').click(force=True)
        page.wait_for_timeout(200)
        check("바둑 오답", "아쉽" in page.locator("#feedbackStatus").inner_text())
        page.locator("#retryBtn").click()
        page.wait_for_timeout(150)
        page.locator('[data-row="4"][data-col="4"]').click(force=True)
        page.wait_for_timeout(250)
        check("바둑 정답", "정답" in page.locator("#feedbackStatus").inner_text())
        check("바둑 해설", "양단수" in page.locator("#feedbackText").inner_text())

        page.locator('#typeFilters .filter-chip[data-type="chess"]').click()
        page.wait_for_timeout(200)
        page.locator(".puzzle-tab").nth(1).click()
        page.wait_for_timeout(250)
        page.locator('#boardWrap rect[aria-label="e8 칸"]').click(force=True)
        page.wait_for_timeout(250)
        check("체스 정답", "정답" in page.locator("#feedbackStatus").inner_text())
        check("체스 기물 이동", page.evaluate("""() => !!document.querySelector('#boardWrap [data-piece="Q"][data-side="W"][data-square="e8"]')"""))

        # ---------- 30문항 전수 정답 탭 ----------
        page.locator('#typeFilters .filter-chip[data-type="all"]').click()
        page.wait_for_timeout(200)
        puzzles = page.evaluate("""() => window.miniPuzzles.map(p => ({id:p.id, type:p.type, answer:p.answer}))""")
        bad = []
        for i, pzl in enumerate(puzzles):
            page.locator(".puzzle-tab").nth(i).click()
            page.wait_for_timeout(70)
            if pzl["type"] == "go":
                page.locator(f'[data-row="{pzl["answer"]["r"]}"][data-col="{pzl["answer"]["c"]}"]').click(force=True)
            elif pzl["type"] == "chess":
                file = chr(97 + pzl["answer"]["c"])
                rank = 8 - pzl["answer"]["r"]
                page.locator(f'#boardWrap rect[aria-label^="{file}{rank} "]').click(force=True)
            else:
                a = pzl["answer"]
                page.locator(f'[data-row="{a["from"]["r"]}"][data-col="{a["from"]["c"]}"]').click(force=True)
                page.wait_for_timeout(50)
                page.locator(f'[data-row="{a["to"]["r"]}"][data-col="{a["to"]["c"]}"]').click(force=True)
            page.wait_for_timeout(90)
            status = page.locator("#feedbackStatus").inner_text()
            if "정답" not in status:
                bad.append(pzl["id"] + ":" + status)
        check("30문항 정답 탭 모두 정답", not bad, bad)
        check("30문항 모두 푼 것으로 기록", page.locator("#solvedCount").inner_text() == "30", page.locator("#solvedCount").inner_text())

        page.locator("#shareBtn").click()
        page.wait_for_timeout(400)
        clip = page.evaluate("() => navigator.clipboard.readText()")
        check("공유 문구", "바둑·체스·장기 한 수 미니" in clip and "푼 문제 30/30" in clip, clip)
        check("공유 링크", "https://not-opened.github.io/go-chess/" in clip, clip)

        # ---------- 하단 링크 ----------
        footer = page.evaluate("""() => [...document.querySelectorAll('footer a')].map(a => a.textContent.trim() + ' ' + a.href)""")
        joined = " | ".join(footer)
        check("푸터 유튜브", any("youtube.com/@notopened" in x for x in footer), joined)
        check("푸터 사주", any("사주·꿈풀이·MBTI 궁합" in x and "fortune" in x for x in footer), joined)
        check("푸터 퀴즈", any("1일 1상식 두뇌 퀴즈" in x and "/quiz/" in x for x in footer), joined)
        check("푸터 개인정보", any("privacy.html" in x for x in footer), joined)
        cards = page.evaluate("""() => [...document.querySelectorAll('.web-card')].map(a => a.textContent.replace(/\\s+/g, ' ').trim())""")
        check("바로가기 카드 2개", len(cards) == 2, cards)
        check("카드에 내부 번호 없음", not any("호" in c for c in cards), cards)

        # ---------- 배너·넘침 ----------
        def settle_banner():
            for _ in range(8):
                page.evaluate("() => { if (window.fitCoupangBanner) window.fitCoupangBanner(); }")
                if page.evaluate("() => !!document.querySelector('#coupangSlot iframe')"):
                    break
                page.wait_for_timeout(400)
            page.wait_for_timeout(200)

        settle_banner()
        ad = page.evaluate("""() => {
          const frame = document.querySelector('#coupangSlot iframe');
          const note = document.querySelector('.affiliate-note');
          return {hasFrame: !!frame, note: note ? note.textContent : '', sectionHidden: document.getElementById('affiliateSection').hidden};
        }""")
        check("쿠팡 배너 iframe", ad["hasFrame"] is True, ad)
        check("쿠팡 영역 노출", ad["sectionHidden"] is False)
        check("수수료 문구 위치", "쿠팡 파트너스 활동의 일환으로" in (ad["note"] or ""))
        ov = page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
        check(f"{vw} 가로 넘침 없음", ov["sw"] <= ov["cw"] + 1, ov)

        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(200)
        ovb = page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
        check(f"{vw} 하단 가로 넘침 없음", ovb["sw"] <= ovb["cw"] + 1, ovb)

        page.locator('#typeFilters .filter-chip[data-type="janggi"]').click()
        page.wait_for_timeout(200)
        page.locator(".puzzle-tab").nth(0).click()
        page.wait_for_timeout(250)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.screenshot(path=f"{shot_prefix}-top.png")
        result["screenshots"].append(f"{shot_prefix}-top.png")
        page.locator("#puzzleCard").scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        page.screenshot(path=f"{shot_prefix}-board.png")
        result["screenshots"].append(f"{shot_prefix}-board.png")

        # 320px 확인
        page.set_viewport_size({"width": 320, "height": 700})
        page.wait_for_timeout(300)
        page.evaluate("() => { if (window.fitCoupangBanner) window.fitCoupangBanner(); }")
        page.wait_for_timeout(200)
        ov320 = page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
        check("320 가로 넘침 없음", ov320["sw"] <= ov320["cw"] + 1, ov320)
        yt320 = page.evaluate("""() => {
          const b = document.querySelector('.yt-banner');
          const t = b.querySelector('.yt-text');
          const br = b.getBoundingClientRect();
          const tr = t.getBoundingClientRect();
          return {h: Math.round(br.height), inside: tr.top >= br.top - 1 && tr.bottom <= br.bottom + 1, sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth};
        }""")
        check("320 유튜브 배너 문구가 잘리지 않음", yt320["inside"] and yt320["h"] >= 44 and yt320["sw"] <= yt320["cw"] + 1, yt320)
        check("320 장기판 히트칸 90", page.locator("#boardWrap rect.jg-hit").count() == 90)
        hit320 = page.evaluate("""() => {
          const h = document.querySelector('#boardWrap rect.jg-hit');
          return h ? Math.round(h.getBoundingClientRect().width) : 0;
        }""")
        check("320 장기 터치 영역", hit320 >= 28, hit320)

        base = url if url.endswith("/") else url + "/"
        page.set_viewport_size({"width": vw, "height": vh})
        page.goto(base + "privacy.html", wait_until="load")
        page.wait_for_timeout(200)
        pov = page.evaluate("() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
        check("개인정보 가로 넘침 없음", pov["sw"] <= pov["cw"] + 1, pov)
        privacy_html = page.content()
        check("개인정보 방침에 쿠팡 쿠키 안내", "쿠팡" in privacy_html and "쿠키" in privacy_html)

        allowed = ("coupang.com", "coupangcdn.com", "youtube.com", "ytimg.com", "googleusercontent.com")
        unexpected = [u for u in result["requests"] if not any(host in u for host in allowed)]
        check("외부 요청 쿠팡·유튜브뿐", not unexpected, unexpected[:8])

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
    ap.add_argument("--viewport", default="375x812")
    a = ap.parse_args()
    w, h = a.viewport.lower().split("x")
    sys.exit(run(a.url, a.shot_prefix, a.json, int(w), int(h)))
