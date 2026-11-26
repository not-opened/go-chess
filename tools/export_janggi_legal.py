#!/usr/bin/env python3
"""장기 문항별 '한의 합법수' 전체를 뽑아 JSON 으로 저장한다.

브라우저(자바스크립트) 장기 엔진이 파이썬 엔진과 같은 수를 내는지 대조하는 데 쓴다.
    python3 tools/export_janggi_legal.py   # → tools/janggi_legal_expected.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import janggi as J
from puzzle_data import to_json


def main():
    out = []
    for p in to_json():
        if p["type"] != "janggi":
            continue
        board = J.from_pieces([(pc["side"], pc["kind"], pc["r"], pc["c"]) for pc in p["pieces"]])
        moves = sorted("%d,%d>%d,%d" % (a[0], a[1], b[0], b[1]) for a, b in J.legal_moves(board, "han"))
        out.append({"id": p["id"], "moves": moves})
    path = os.path.join(HERE, "janggi_legal_expected.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    print("wrote", path, len(out), "puzzles", sum(len(x["moves"]) for x in out), "moves")


if __name__ == "__main__":
    main()
