#!/usr/bin/env python3
"""장기 국면 점검 도구(설계 보조) — 문항 후보를 손으로 다듬을 때 쓴다.

    python3 tools/check_janggi_pos.py "han:K9,4 han:R1,1 han:R9,6 cho:K3,6 cho:G1,2"

좌표는 1행~10행 · 1열~9열(사람이 읽는 표기). 결과는
  · 국면 문제(양 궁·빅장·장군·외통 여부)
  · 한의 합법수 개수
  · 1수 외통이 되는 수(정답 후보) 전부
  · 각 후보 뒤 초 궁의 도피로 상태
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janggi as J
from search_janggi import king_escape_report


def parse(spec):
    pieces = []
    for tok in spec.replace(";", " ").split():
        side, rest = tok.split(":")
        kind = rest[0]
        r, c = rest[1:].split(",")
        pieces.append((side, kind, int(r) - 1, int(c) - 1))
    return pieces


def main():
    pieces = parse(" ".join(sys.argv[1:]))
    board = J.from_pieces(pieces)
    print(J.ascii_board(board))
    print("problems:", J.position_problems(board) or "없음")
    legal = J.legal_moves(board, "han")
    print("한 합법수:", len(legal))
    mates = J.mate_moves(board, "han")
    print("1수 외통 수:", len(mates))
    for src, dst in mates:
        print("  %s%d,%d -> %d,%d" % (board[src][0], src[0] + 1, src[1] + 1, dst[0] + 1, dst[1] + 1))
        nb = J.apply_move(board, src, dst)[0]
        print("   ", J.ascii_board(nb))
        for sq, state in king_escape_report(nb):
            print("    초 궁 %d,%d: %s" % (sq[0] + 1, sq[1] + 1, state))


if __name__ == "__main__":
    main()
