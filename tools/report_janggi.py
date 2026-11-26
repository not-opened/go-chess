#!/usr/bin/env python3
"""채택한 장기 문항 10개의 좌표·해설 근거를 한 번에 뽑는다(개발 보조).

spec 문자열은 1행~10행·1열~9열(사람이 읽는 표기)이다.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janggi as J
from search_janggi import king_escape_report

SPECS = [
    ("janggi-01", "cho:K3,6 han:R9,7 han:R2,2 han:K9,4", "R9,7>3,7"),
    ("janggi-02", "cho:K3,4 han:M4,3 han:M2,1 han:K9,6", "M2,1>1,3"),
    ("janggi-03", "cho:K3,4 cho:R2,5 han:R10,7 han:E1,8 han:K9,6", "R10,7>10,4"),
    ("janggi-04", "cho:K3,4 cho:S2,5 han:R1,5 han:M3,7 han:K10,6", "R1,5>2,5"),
    ("janggi-05", "cho:K1,4 han:S3,5 han:R7,5 han:K9,6", "S3,5>2,5"),
    ("janggi-06", "cho:K3,6 cho:G2,6 han:M4,6 han:R5,2 han:K9,6", "R5,2>3,2"),
    ("janggi-07", "cho:K2,6 han:M4,6 han:R4,5 han:S3,4 cho:S6,9 han:K9,4", "R4,5>2,5"),
    ("janggi-08", "cho:K3,6 cho:E2,6 han:M4,7 han:R1,9 han:K10,4", "R1,9>1,4"),
    ("janggi-09", "cho:K1,6 han:P4,6 han:R7,6 han:R4,5 han:P4,4 cho:S4,2 han:K9,6", "P4,6>8,6"),
    ("janggi-10", "cho:K3,4 cho:G2,4 han:M5,4 han:M5,8 han:R10,1 han:K9,4", "M5,8>4,6"),
]


def parse(spec):
    out = []
    for tok in spec.split():
        side, rest = tok.split(":")
        out.append((side, rest[0], int(rest[1:].split(",")[0]) - 1, int(rest[1:].split(",")[1]) - 1))
    return out


def main():
    for pid, spec, mate in SPECS:
        pieces = parse(spec)
        board = J.from_pieces(pieces)
        m = mate.split(">")
        src = tuple(int(x) - 1 for x in m[0][1:].split(","))
        dst = tuple(int(x) - 1 for x in m[1].split(","))
        mates = J.mate_moves(board, J.HAN)
        print("=" * 70)
        print(pid, "problems:", J.position_problems(board) or "없음")
        print("py pieces:", [(s, k, r, c) for s, k, r, c in pieces])
        print("py answer: from", src, "to", dst)
        print("mates:", len(mates), "정답일치:", mates == [(src, dst)])
        print(J.ascii_board(board, mark={src}, targets={dst}))
        nb, cap = J.apply_move(board, src, dst)
        print("장군 기물:", J.attackers(nb, J.find_king(nb, J.CHO), J.HAN),
              " 잡은 기물:", cap)
        for sq, state in king_escape_report(nb):
            print("   도피로 %d,%d → %s" % (sq[0] + 1, sq[1] + 1, state))
        print("초 합법수(전):", len(J.legal_moves(board, J.CHO)))


if __name__ == "__main__":
    main()
