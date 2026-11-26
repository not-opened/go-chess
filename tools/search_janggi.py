#!/usr/bin/env python3
"""장기 1수 외통 문항 후보 탐색기(개발 보조 도구).

무작위로 국면을 만들고 규칙 엔진으로
  · 초기 국면이 문항으로 성립하는지(양 궁 존재·빅장 아님·초가 장군 아님·초에게 합법수 있음)
  · 한(漢)의 합법수 중 정확히 하나만 1수 외통인지
  · 외통 국면에서 초 궁의 도피로가 모두 '공격당해서' 막혔는지(빅장으로만 막힌 후보는 제외)
를 확인해 후보를 모은다. 채택한 최종 문항은 puzzle_data.py 에 손으로 옮긴다.

    python3 tools/search_janggi.py --tier 입문 --n 200000 --want 8
"""
import argparse
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janggi as J

HAN, CHO = J.HAN, J.CHO
KNAME = {"K": "궁", "R": "차", "P": "포", "M": "마", "E": "상", "G": "사", "S": "졸/병"}


def king_escape_report(board):
    """초 궁의 도피로 상태를 돌려준다."""
    ck = J.find_king(board, CHO)
    if ck is None:
        return None
    rep = []
    for dst in J.pseudo_moves(board, ck[0], ck[1]):
        t = board.get(dst)
        if t is not None and t[1] == CHO:
            rep.append((dst, "own"))
            continue
        nb, cap = J.apply_move(board, ck, dst)
        if J.kings_face(nb):
            rep.append((dst, "bigjang"))
            continue
        atk = J.attackers(nb, dst, HAN)
        if atk:
            rep.append((dst, "attacked:" + ",".join("%s%d,%d" % (board[p][0], p[0] + 1, p[1] + 1) for p in atk)))
        elif cap is not None and cap[1] == HAN:
            rep.append((dst, "capturable"))
        else:
            rep.append((dst, "FREE"))
    return rep


def quality(board, info, args):
    """채택 기준. 문제 있으면 이유 문자열."""
    src, dst = info["move"]
    if args.mover and info["mover"] not in args.mover:
        return "기물 종류"
    nb = J.apply_move(board, src, dst)[0]
    rep = king_escape_report(nb)
    if rep is None:
        return "궁 없음"
    cover = 0
    for sq, state in rep:
        if state in ("bigjang", "FREE", "capturable"):
            return "도피로 %s %s" % (sq, state)
        if state.startswith("attacked:") and ("%s%d,%d" % (info["mover"], src[0] + 1, src[1] + 1)) not in state:
            cover += 1
    if args.min_cover and cover < args.min_cover:
        return "아군 협공 부족(%d)" % cover
    if info["attackers"] < 1:
        return "장군 아님"
    if args.min_attack and info["attackers"] < args.min_attack:
        return "장군 기물 수 부족"
    if args.max_pieces and len(board) > args.max_pieces:
        return "기물 과다"
    if args.capture and not info["capture"]:
        return "잡는 수 아님"
    if args.checker:
        atk = J.attackers(nb, J.find_king(nb, CHO), HAN)
        if dst not in atk:
            return "정답 기물이 장군 기물이 아님"
    # 정답 수가 초 기물을 잡는 경우와 아닌 경우를 모두 허용하되, 지나치게 먼 유닛은 제한
    dist = max(abs(src[0] - dst[0]), abs(src[1] - dst[1]))
    if dist > 3 and info["mover"] in ("E",):
        return "상 이동 거리 과다"
    return ""


def random_position(rng, tier):
    if tier == "입문":
        han_n, cho_n = rng.choice([2, 3, 3]), rng.choice([1, 2])
        han_kinds = "RRMPS"
        cho_kinds = "GS"
    elif tier == "중급":
        han_n, cho_n = rng.choice([3, 3, 4]), rng.choice([1, 2])
        han_kinds = "RPMSGE"
        cho_kinds = "GSR"
    elif tier == "포":
        han_n, cho_n = rng.choice([3, 4]), rng.choice([1, 2])
        han_kinds = "PPRM"
        cho_kinds = "GSR"
    else:
        han_n, cho_n = rng.choice([4, 4, 5]), rng.choice([2, 3])
        han_kinds = "RMPSEGR"
        cho_kinds = "GSRP"

    pieces = []
    hk = rng.choice([(9, 3), (9, 4), (9, 5), (8, 3), (8, 5), (7, 4)])
    pieces.append((HAN, "K", hk[0], hk[1]))
    ck = rng.choice([(0, 3), (0, 4), (0, 5), (1, 3), (1, 4), (1, 5), (2, 4), (2, 3), (2, 5)])
    pieces.append((CHO, "K", ck[0], ck[1]))
    used = {hk, ck}
    for _ in range(han_n):
        kind = rng.choice(han_kinds)
        for _try in range(60):
            if kind == "G":
                r, c = rng.randrange(7, 10), rng.randrange(3, 6)
            elif rng.random() < 0.78:
                r, c = rng.randrange(0, 5), rng.randrange(0, 9)
            else:
                r, c = rng.randrange(5, 10), rng.randrange(0, 9)
            if (r, c) not in used:
                break
        else:
            continue
        used.add((r, c))
        pieces.append((HAN, kind, r, c))
    for _ in range(cho_n):
        kind = rng.choice(cho_kinds)
        for _try in range(60):
            if kind == "G":
                r, c = rng.randrange(0, 3), rng.randrange(3, 6)
            elif rng.random() < 0.85:
                r, c = rng.randrange(0, 5), rng.randrange(0, 9)
            else:
                r, c = rng.randrange(5, 10), rng.randrange(0, 9)
            if (r, c) not in used:
                break
        else:
            continue
        used.add((r, c))
        pieces.append((CHO, kind, r, c))
    return pieces


def describe(board, mate, total_moves):
    src, dst = mate
    kind, side = board[src]
    nb = J.apply_move(board, src, dst)[0]
    atk = J.attackers(nb, J.find_king(nb, CHO), HAN)
    return dict(
        move=mate, mover=kind,
        capture=board.get(dst) is not None,
        diag=any(dst == pts[0] for pts in J.diag_rays(src[0], src[1])),
        attackers=len(atk), legal_moves=total_moves,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="입문")
    ap.add_argument("--n", type=int, default=200000)
    ap.add_argument("--want", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261126)
    ap.add_argument("--mover", default="", help="정답 기물 종류 제한(R,P,M,S,E,G)")
    ap.add_argument("--min-cover", type=int, default=0, help="정답 기물이 아닌 아군이 막은 도피로 수")
    ap.add_argument("--checker", action="store_true", help="정답 기물이 직접 장군을 거는 수만")
    ap.add_argument("--min-attack", type=int, default=0, help="장군 기물 최소 수(2=양수겸장)")
    ap.add_argument("--max-pieces", type=int, default=0, help="양쪽 기물 수 상한")
    ap.add_argument("--capture", action="store_true", help="정답 수가 기물을 잡는 수만")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    found = []
    seen = set()
    scanned = 0
    for i in range(args.n):
        scanned = i + 1
        pieces = random_position(rng, args.tier)
        try:
            board = J.from_pieces(pieces)
        except ValueError:
            continue
        if J.position_problems(board):
            continue
        total = J.legal_moves(board, HAN)
        if len(total) < 8:
            continue
        mates = J.mate_moves(board, HAN)
        if len(mates) != 1:
            continue
        info = describe(board, mates[0], len(total))
        why = quality(board, info, args)
        if why:
            continue
        key = tuple(sorted(pieces))
        if key in seen:
            continue
        seen.add(key)
        found.append((board, pieces, info))
        if len(found) >= args.want:
            break
    print("scanned %d trials, %d candidates" % (scanned, len(found)))
    found.sort(key=lambda x: (len(x[1]), x[2]["legal_moves"]))
    for board, pieces, info in found:
        src, dst = info["move"]
        kind, side = board[src]
        print("=" * 62)
        print("pieces:", "; ".join("%s:%s%d,%d" % (s, k, r + 1, c + 1) for s, k, r, c in pieces))
        print("mate:", kind, "(%d,%d)->(%d,%d)" % (src[0] + 1, src[1] + 1, dst[0] + 1, dst[1] + 1),
              "capture=%s" % info["capture"], "diag=%s" % info["diag"],
              "attackers=%d" % info["attackers"], "legal=%d" % info["legal_moves"])
        print(J.ascii_board(board, mark={src}, targets={dst}))
        nb = J.apply_move(board, src, dst)[0]
        for sq, state in king_escape_report(nb):
            print("   초 궁 (%d,%d): %s" % (sq[0] + 1, sq[1] + 1, state))


if __name__ == "__main__":
    main()
