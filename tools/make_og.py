#!/usr/bin/env python3
"""og.png(1200×630 공유 카드)를 만든다 — 바둑·체스·장기 세 판을 그린다.

    python3 tools/make_og.py    # → og.png
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def go_board():
    pad, cell, n = 16, 18, 9
    size = pad * 2 + cell * (n - 1)
    parts = [f'<rect width="{size}" height="{size}" fill="#dcb35c"/>', '<g stroke="#3b2f1c" stroke-width="1.6">']
    for i in range(n):
        p = pad + i * cell
        parts.append(f'<line x1="{pad}" y1="{p}" x2="{size - pad}" y2="{p}"/>')
        parts.append(f'<line x1="{p}" y1="{pad}" x2="{p}" y2="{size - pad}"/>')
    parts.append("</g>")
    stones = [("B", 2, 2), ("B", 3, 2), ("W", 3, 3), ("B", 4, 3), ("W", 4, 4)]
    for col, r, c in stones:
        fill = "#111827" if col == "B" else "#f8fafc"
        stroke = "#000" if col == "B" else "#64748b"
        parts.append(f'<circle cx="{pad + c * cell}" cy="{pad + r * cell}" r="10" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    return f'<svg class="board" width="{size}" height="{size}" viewBox="0 0 {size} {size}">' + "".join(parts) + "</svg>"


def chess_board():
    cell, n = 20, 8
    size = cell * n
    parts = []
    for r in range(n):
        for c in range(n):
            fill = "#e2e8f0" if (r + c) % 2 == 0 else "#7c8ba1"
            parts.append(f'<rect x="{c * cell}" y="{r * cell}" width="{cell}" height="{cell}" fill="{fill}"/>')
    pieces = [("♜", 0, 0, "#111827"), ("♚", 0, 3, "#111827"), ("♕", 4, 2, "#f8fafc"), ("♔", 5, 5, "#f8fafc")]
    for sym, r, c, ink in pieces:
        parts.append(f'<text x="{c * cell + cell / 2}" y="{r * cell + cell / 2 + 9}" font-size="26" text-anchor="middle" fill="{ink}">{sym}</text>')
    return f'<svg class="board" width="{size}" height="{size}" viewBox="0 0 {size} {size}">' + "".join(parts) + "</svg>"


def janggi_board():
    cols, rows = 9, 10
    pad, cell = 14, 18
    w = pad * 2 + cell * (cols - 1)
    h = pad * 2 + cell * (rows - 1)
    parts = [f'<rect width="{w}" height="{h}" fill="#e6c894"/>', '<g stroke="#5b4520" stroke-width="1.5">']
    for r in range(rows):
        parts.append(f'<line x1="{pad}" y1="{pad + r * cell}" x2="{w - pad}" y2="{pad + r * cell}"/>')
    for c in range(cols):
        parts.append(f'<line x1="{pad + c * cell}" y1="{pad}" x2="{pad + c * cell}" y2="{h - pad}"/>')
    for a, b in (((0, 3), (2, 5)), ((0, 5), (2, 3)), ((7, 3), (9, 5)), ((7, 5), (9, 3))):
        parts.append(f'<line x1="{pad + a[1] * cell}" y1="{pad + a[0] * cell}" x2="{pad + b[1] * cell}" y2="{pad + b[0] * cell}"/>')
    parts.append("</g>")
    pieces = [("車", 1, 1, "#b91c1c"), ("楚", 1, 5, "#0f766e"), ("漢", 8, 4, "#b91c1c"), ("車", 9, 6, "#b91c1c")]
    for sym, r, c, color in pieces:
        cx, cy = pad + c * cell, pad + r * cell
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="#fdf3df" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="{cx}" y="{cy + 5.5}" font-size="15" font-weight="700" text-anchor="middle" fill="{color}">{sym}</text>')
    return f'<svg class="board" width="{w}" height="{h}" viewBox="0 0 {w} {h}">' + "".join(parts) + "</svg>"


HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:1200px; height:630px; background:#0f172a; color:#f8fafc;
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;
         display:flex; align-items:center; gap:16px; padding:0 52px; overflow:hidden; position:relative; }}
  .bar {{ position:absolute; left:0; top:0; width:100%; height:8px;
         background:linear-gradient(90deg,#38bdf8,#818cf8,#f472b6); }}
  .left {{ width:530px; flex:0 0 auto; }}
  .badge {{ display:inline-block; font-size:19px; font-weight:800; color:#38bdf8;
           background:rgba(56,189,248,.14); border:2px solid rgba(56,189,248,.5);
           padding:6px 18px; border-radius:999px; margin-bottom:20px; }}
  h1 {{ font-size:64px; line-height:1.12; font-weight:900; letter-spacing:-.02em; }}
  h1 .accent {{ color:#38bdf8; display:block; }}
  .sub {{ margin-top:18px; font-size:25px; line-height:1.5; color:#94a3b8; font-weight:600; }}
  .meta {{ margin-top:24px; font-size:22px; color:#cbd5e1; font-weight:700; }}
  .meta b {{ color:#f8fafc; }}
  .boards {{ display:flex; align-items:center; gap:16px; flex:1 1 auto; justify-content:flex-end; }}
  .board {{ border-radius:16px; overflow:hidden; box-shadow:0 18px 40px rgba(0,0,0,.45); display:block; }}
  .cap {{ text-align:center; font-size:17px; font-weight:800; color:#94a3b8; margin-top:8px; }}
  .col {{ display:flex; flex-direction:column; align-items:center; }}
</style></head>
<body>
<div class="bar"></div>
<div class="left">
  <span class="badge">notopened</span>
  <h1>바둑 · 체스 · 장기<span class="accent">한 수 미니</span></h1>
  <div class="sub">사활 · 체크메이트 · 외통수를<br>단 한 수로 풀어 보세요</div>
  <div class="meta">입문 · 중급 · 고급 <b>30문항</b></div>
</div>
<div class="boards">
  <div class="col">{go}<div class="cap">바둑</div></div>
  <div class="col" style="margin-bottom:22px">{chess}<div class="cap">체스</div></div>
  <div class="col">{janggi}<div class="cap">장기</div></div>
</div>
</body></html>
"""


def main():
    from playwright.sync_api import sync_playwright

    html = HTML.format(go=go_board(), chess=chess_board(), janggi=janggi_board())
    path = os.path.join(HERE, "og_render.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome", args=["--no-sandbox"])
        except Exception:
            browser = pw.chromium.launch(args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto("file://" + path)
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(ROOT, "og.png"))
        browser.close()
    print("wrote", os.path.join(ROOT, "og.png"))


if __name__ == "__main__":
    main()
