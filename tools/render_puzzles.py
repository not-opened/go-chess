#!/usr/bin/env python3
"""site_template.html + puzzle_data.py → index.html (문항 JSON 인라인 삽입)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from puzzle_data import to_json  # noqa: E402


def main():
    tpl = open(os.path.join(HERE, "site_template.html"), encoding="utf-8").read()
    puzzles = to_json()
    payload = json.dumps(puzzles, ensure_ascii=False, separators=(",", ":"))
    assert "__PUZZLES_JSON__" in tpl, "템플릿에 자리표시자가 없음"
    html = tpl.replace("__PUZZLES_JSON__", payload)
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out} ({len(html):,} bytes, {len(puzzles)} puzzles)")


if __name__ == "__main__":
    main()
