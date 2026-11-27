#!/usr/bin/env python3
"""45문항 전체 검산 스크립트.

사용:
    python3 verify_puzzles.py            # index.html 에 박힌 JSON 을 검산
    python3 verify_puzzles.py --data     # tools/puzzle_data.py 원본을 검산

바둑: 자체 9x9 규칙 엔진으로 활로·따내기·자충수·패·집(눈) 계산
체스: python-chess 로 합법수/체크메이트/포크/스큐어 계산
"""
import json
import re
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from goban import Board
from predicates import (
    is_capture, double_atari, atari_dead, ko_move, two_eyes, eyes_count,
)
import janggi as J

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------------------------ 바둑 검산

def go_position_ok(p):
    n = p["size"]
    assert n == 9, "9x9 만 사용"
    stones = [(s["r"], s["c"], s["color"]) for s in p["stones"]]
    for r, c, col in stones:
        assert 0 <= r < n and 0 <= c < n, f"{p['id']}: 좌표 범위 밖 {r},{c}"
        assert col in ("B", "W"), f"{p['id']}: 색 오류 {col}"
    b = Board(n, stones)
    # 모든 그룹이 활로를 가져야 한다 (직전 수가 불법이 아님)
    for color, pts, libs in b.groups():
        assert libs, f"{p['id']}: 활로 0개 그룹 {sorted(pts)} — 초기 배치가 불법"
    return b


def white_max_eyes_after(nb, wg):
    best = 0
    for wr in range(nb.n):
        for wc in range(nb.n):
            if (wr, wc) in nb.g:
                continue
            try:
                wb, _ = nb.play(wr, wc, 'W')
            except ValueError:
                continue
            anchor = None
            for q in wg[0]:
                if q in wb.g and wb.g[q] == 'W':
                    anchor = q
                    break
            if anchor is None:
                continue
            best = max(best, len(wb.eyes(anchor[0], anchor[1])))
    return best


def go_unique(p, b, pred, label):
    legal = b.legal_moves('B')
    hits = [mv for mv in legal if pred(mv)]
    ans = (p["answer"]["r"], p["answer"]["c"])
    assert ans in legal, f"{p['id']}: 정답 {ans} 이 흑의 합법수가 아님(자충수/점유)"
    assert hits == [ans], f"{p['id']} {label}: 정답 유일성 실패 → {hits} (정답 {ans})"
    return hits


def verify_go(p):
    b = go_position_ok(p)
    ck = p["check"]
    kind = ck["kind"]
    ans = (p["answer"]["r"], p["answer"]["c"])
    detail = ""
    if kind == "capture":
        n = ck["count"]
        go_unique(p, b, lambda mv: is_capture(b, mv, 'B', n), f"따내기 {n}점")
        nb, cap = b.play(ans[0], ans[1], 'B')
        assert len(cap) == n, f"{p['id']}: 따낸 돌 {len(cap)}개 (기대 {n})"
        detail = f"{n}점 따냄"
    elif kind == "double_atari":
        groups = [tuple(g) for g in ck["groups"]]
        go_unique(p, b, lambda mv: double_atari(b, mv, 'B', groups), "양단수")
        nb, _ = b.play(ans[0], ans[1], 'B')
        libs = [len(nb.group(g[0], g[1])[1]) for g in groups]
        assert libs == [1] * len(groups), f"{p['id']}: 그룹 활로 {libs} (각 1 기대)"
        detail = f"{len(groups)}개 그룹 각각 활로 1"
    elif kind == "atari_dead":
        target = tuple(ck["target"])
        go_unique(p, b, lambda mv: atari_dead(b, mv, 'B', target), "단수→따냄")
        nb, _ = b.play(ans[0], ans[1], 'B')
        assert len(nb.group(target[0], target[1])[1]) == 1
        detail = "단수 + 백이 살 수 없음 확인"
        trap = ck.get("trap")
        if trap:
            tp = tuple(trap["point"])
            try:
                nb.play(tp[0], tp[1], trap["color"])
                raise AssertionError(f"{p['id']}: 함정 자리 {tp} 가 자충수가 아님")
            except ValueError as e:
                assert "suicide" in str(e), f"{p['id']}: 함정 자리 오류 {e}"
            detail += f" / 백 {tp} 는 자충수"
    elif kind == "ko":
        go_unique(p, b, lambda mv: ko_move(b, mv, 'B'), "패")
        detail = "패 발생 + 백 즉시 되따냄이 같은 국면 반복"
    elif kind == "two_eyes":
        grp = tuple(ck["group"])
        go_unique(p, b, lambda mv: two_eyes(b, mv, 'B', grp), "두 눈")
        nb, _ = b.play(ans[0], ans[1], 'B')
        e = len(nb.eyes(grp[0], grp[1]))
        assert e >= 2, f"{p['id']}: 눈 {e}개"
        detail = f"흑 진짜 집 {e}개"
    elif kind == "kill_nakade":
        grp = tuple(ck["group"])

        def kill(mv):
            nb, _ = b.play(mv[0], mv[1], 'B')
            wg = None
            for col, g, l in nb.groups():
                if col == 'W' and grp in g:
                    wg = (g, l)
            if wg is None or not wg[1]:
                return False
            return white_max_eyes_after(nb, wg) <= 1

        go_unique(p, b, kill, "나카데(백 사망)")
        detail = "백이 어떤 수를 두어도 진짜 집 2개 불가"
    else:
        raise AssertionError(f"{p['id']}: 알 수 없는 바둑 검산 종류 {kind}")

    # 해설 좌표 표기 검사
    m = re.match(r"^(\d+)행 (\d+)열$", p["answerText"])
    assert m, f"{p['id']}: answerText 형식 오류 {p['answerText']}"
    assert (int(m.group(1)) - 1, int(m.group(2)) - 1) == ans, \
        f"{p['id']}: answerText {p['answerText']} 와 좌표 {ans} 불일치"
    return detail


# ------------------------------------------------------------------ 체스 검산

def chess_board(p):
    b = chess.Board(p["fen"])
    assert b.is_valid(), f"{p['id']}: FEN 국면이 불법 {p['fen']} status={b.status()}"
    assert b.turn == chess.WHITE, f"{p['id']}: 백 차례가 아님"
    assert not b.is_check(), f"{p['id']}: 백이 이미 체크 상태"
    return b


def move_by_san(b, san):
    for m in b.legal_moves:
        if b.san(m) == san:
            return m
    raise AssertionError(f"불법 수: {san} ({b.fen()})")


def mate_moves(b):
    out = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            out.append(m)
        b.pop()
    return out


def sq(r, c):
    return chess.square(c, 7 - r)


def verify_chess(p):
    b = chess_board(p)
    mv = move_by_san(b, p["san"])
    ans = (p["answer"]["r"], p["answer"]["c"])
    assert mv.to_square == sq(*ans), f"{p['id']}: 정답 좌표 {ans} != {p['san']} 도착칸"
    # 보드에 그려진 기물이 FEN 과 일치하는지
    bmap = {s: piece for s, piece in b.piece_map().items()}
    assert len(p["pieces"]) == len(bmap), f"{p['id']}: 기물 수 불일치"
    for pc in p["pieces"]:
        piece = bmap.get(sq(pc["r"], pc["c"]))
        assert piece is not None, f"{p['id']}: {pc} 칸에 기물 없음"
        assert (piece.color == chess.WHITE) == (pc["side"] == "W"), f"{p['id']}: {pc} 진영 불일치"
    movers = [pc for pc in p["pieces"] if pc["mover"]]
    assert len(movers) == 1, f"{p['id']}: mover 기물 {len(movers)}개"
    assert sq(movers[0]["r"], movers[0]["c"]) == mv.from_square, f"{p['id']}: mover 위치가 출발칸과 다름"

    # 오답 이유 맵: 정답을 뺀 모든 합법 수 도착칸에 이유가 있어야 한다
    wrong = p.get("wrong") or {}
    assert isinstance(wrong, dict) and wrong, f"{p['id']}: 오답 이유 맵 없음"
    for m in b.legal_moves:
        if m.from_square != mv.from_square:
            continue
        rr = 7 - chess.square_rank(m.to_square)
        cc = chess.square_file(m.to_square)
        if (rr, cc) == ans:
            assert f"{rr},{cc}" not in wrong, f"{p['id']}: 정답 칸에 오답 이유가 있음"
            continue
        assert f"{rr},{cc}" in wrong, f"{p['id']}: 오답 이유 누락 {chess.square_name(m.to_square)}"

    kind = p["check"]["kind"]
    if kind == "mate":
        mates = mate_moves(b)
        assert len(mates) == 1, f"{p['id']}: 메이트 수 {len(mates)}개 → {[m.uci() for m in mates]}"
        assert mates[0] == mv, f"{p['id']}: 유일한 메이트가 정답과 다름 {mates[0].uci()}"
        b.push(mv)
        assert b.is_checkmate()
        detail = "유일한 1수 메이트"
    elif kind == "fork":
        target = chess.parse_square(p["check"]["target"])
        def forkish(m):
            if not b.is_capture(m) and b.gives_check(m) is False:
                return False
            nb = b.copy(); nb.push(m)
            if not nb.is_check():
                return False
            piece = nb.piece_at(m.to_square)
            if piece is None:
                return False
            return target in nb.attacks(m.to_square)
        cands = [m for m in b.legal_moves if forkish(m)]
        assert cands == [mv], f"{p['id']}: 포크 후보 {[m.uci() for m in cands]}"
        # 흑의 모든 응수 뒤에도 퀸을 잡을 수 있는지
        nb = b.copy(); nb.push(mv)
        assert nb.is_check()
        for reply in list(nb.legal_moves):
            nb2 = nb.copy(); nb2.push(reply)
            tpiece = nb2.piece_at(target)
            assert tpiece is not None and tpiece.color == chess.BLACK, \
                f"{p['id']}: 흑 응수 {reply.uci()} 뒤 퀸이 사라짐"
            caps = [m for m in nb2.legal_moves if m.to_square == target]
            assert caps, f"{p['id']}: 흑 응수 {reply.uci()} 뒤 퀸을 잡을 수 없음"
            attackers = nb2.attackers(chess.BLACK, target)
            defenders_value = chess.QUEEN
            captured = nb2.piece_at(target)
            assert caps, "no capture"
        detail = f"고유 체크+공격 수, 흑 응수 {len(list(nb.legal_moves))}가지 모두 목표 기물 획득"
    elif kind == "skewer":
        target = chess.parse_square(p["check"]["target"])
        def skewerish(m):
            nb = b.copy(); nb.push(m)
            if not nb.is_check():
                return False
            king_sq = nb.king(chess.BLACK)
            from_sq = m.to_square
            # 같은 랭크/파일/대각선 위에 킹과 타깃이 일직선
            def line(a, c):
                return (chess.square_rank(a) == chess.square_rank(c) or
                        chess.square_file(a) == chess.square_file(c) or
                        abs(chess.square_rank(a) - chess.square_rank(c)) ==
                        abs(chess.square_file(a) - chess.square_file(c)))
            if not (line(from_sq, king_sq) and line(king_sq, target) and line(from_sq, target)):
                return False
            return True
        cands = [m for m in b.legal_moves if skewerish(m)]
        assert cands == [mv], f"{p['id']}: 스큐어 후보 {[m.uci() for m in cands]}"
        nb = b.copy(); nb.push(mv)
        for reply in list(nb.legal_moves):
            nb2 = nb.copy(); nb2.push(reply)
            caps = [m for m in nb2.legal_moves if m.to_square == target]
            assert caps, f"{p['id']}: 흑 응수 {reply.uci()} 뒤 퀸 획득 불가"
        detail = "고유 스큐어 수, 흑 응수 모두 퀸 획득"
    else:
        raise AssertionError(f"{p['id']}: 알 수 없는 체스 검산 종류 {kind}")

    # 체스 좌표 표기 검사: "e8 (Qe8#)"
    fm = re.match(r"^([a-h][1-8]) \(", p["answerText"])
    assert fm, f"{p['id']}: answerText 형식 오류 {p['answerText']}"
    assert chess.parse_square(fm.group(1)) == mv.to_square, \
        f"{p['id']}: answerText 칸과 실제 도착칸 불일치"
    return detail


# ------------------------------------------------------------------ 장기 검산

JANGGI_NAME = {"R": "차", "P": "포", "M": "마", "E": "상", "G": "사", "S": "졸", "K": "궁"}


def verify_janggi(p):
    rows, cols = p["rows"], p["cols"]
    assert rows == 10 and cols == 9, f"{p['id']}: 판 크기 {rows}x{cols}"
    pieces = []
    for pc in p["pieces"]:
        pieces.append((pc["side"], pc["kind"], pc["r"], pc["c"]))
    board = J.from_pieces(pieces)
    probs = J.position_problems(board)
    assert not probs, f"{p['id']}: 국면 오류 {probs}"

    src = (p["answer"]["from"]["r"], p["answer"]["from"]["c"])
    dst = (p["answer"]["to"]["r"], p["answer"]["to"]["c"])

    # 화면에 그린 기물이 국면과 일치하고, 착수 기물이 하나뿐이며 출발칸에 있는지
    assert len(p["pieces"]) == len(board), f"{p['id']}: 기물 수 불일치"
    movers = [pc for pc in p["pieces"] if pc["mover"]]
    assert len(movers) == 1, f"{p['id']}: mover 기물 {len(movers)}개"
    assert (movers[0]["r"], movers[0]["c"]) == src, f"{p['id']}: mover 위치가 출발칸과 다름"
    mover_kind = board[src][0]
    assert movers[0]["kind"] == mover_kind, f"{p['id']}: mover 종류 불일치"
    assert movers[0]["symbol"] == J.SYMBOL[board[src][1]][mover_kind], f"{p['id']}: 기물 글자 불일치"
    for pc in p["pieces"]:
        assert pc["symbol"] == J.SYMBOL[pc["side"]][pc["kind"]], f"{p['id']}: 글자 오류 {pc}"

    # 정답이 합법수이고, 그 수가 유일한 1수 외통인지
    legal = J.legal_moves(board, J.HAN)
    assert (src, dst) in legal, f"{p['id']}: 정답 {src}->{dst} 이 합법수가 아님"
    mates = J.mate_moves(board, J.HAN)
    assert mates == [(src, dst)], f"{p['id']}: 1수 외통이 {len(mates)}개 → {mates}"

    nb, cap = J.apply_move(board, src, dst)
    assert J.in_check(nb, J.CHO), f"{p['id']}: 정답 뒤 초가 장군이 아님"
    assert not J.legal_moves(nb, J.CHO), f"{p['id']}: 정답 뒤 초에게 합법수가 있음"
    # 도피로가 모두 공격당해 막혔는지(빅장으로만 막힌 도피로가 없는지)
    ck = J.find_king(nb, J.CHO)
    for sq in J.pseudo_moves(nb, ck[0], ck[1]):
        t = nb.get(sq)
        if t is not None and t[1] == J.CHO:
            continue
        nk, _ = J.apply_move(nb, ck, sq)
        if J.kings_face(nk):
            raise AssertionError(f"{p['id']}: 도피로 {sq} 가 빅장으로만 막힘")
        if not J.attackers(nk, sq, J.HAN):
            raise AssertionError(f"{p['id']}: 도피로 {sq} 가 비어 있음")

    # 정답 표기 검사: "차 9행 7열 → 3행 7열"
    m = re.match(r"^(차|포|마|상|사|졸|병|궁) (\d+)행 (\d+)열 → (\d+)행 (\d+)열$", p["answerText"])
    assert m, f"{p['id']}: answerText 형식 오류 {p['answerText']}"
    assert m.group(1) == JANGGI_NAME[mover_kind], f"{p['id']}: answerText 기물 이름 불일치"
    assert (int(m.group(2)) - 1, int(m.group(3)) - 1) == src, f"{p['id']}: answerText 출발칸 불일치"
    assert (int(m.group(4)) - 1, int(m.group(5)) - 1) == dst, f"{p['id']}: answerText 도착칸 불일치"

    # 힌트에 정답 좌표가 노출되지 않아야 한다
    for rc in (src, dst):
        coord = "%d행 %d열" % (rc[0] + 1, rc[1] + 1)
        assert coord not in p["hint"], f"{p['id']}: 힌트에 정답 좌표 노출({coord})"

    cap_txt = "" if cap is None else f", {J.SYMBOL[cap[1]][cap[0]]} 잡음"
    return "유일한 1수 외통" + cap_txt + (", 궁성 대각선" if any(dst == pts[0] for pts in J.diag_rays(src[0], src[1])) else "")


# ------------------------------------------------------------------ 전체

def load_from_index(path):
    html = open(path, encoding="utf-8").read()
    m = re.search(r"const miniPuzzles = (\[.*?\]);\n", html, re.S)
    if not m:
        m = re.search(r"const miniPuzzles = (\[.*?\]);", html, re.S)
    assert m, "index.html 에서 문항 JSON 을 찾지 못함"
    return json.loads(m.group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", action="store_true")
    ap.add_argument("--json-report", default="")
    args = ap.parse_args()

    if args.data:
        from puzzle_data import to_json
        puzzles = to_json()
    else:
        puzzles = load_from_index(os.path.join(ROOT, "index.html"))

    assert len(puzzles) == 45, f"문항 수 {len(puzzles)} (45 기대)"
    ids = [p["id"] for p in puzzles]
    assert len(set(ids)) == len(ids), "중복 id"
    for typ, label in (("go", "바둑"), ("chess", "체스"), ("janggi", "장기")):
        assert sum(1 for p in puzzles if p["type"] == typ) == 15, f"{label} 15문항 아님"
    for p in puzzles:
        assert p["difficulty"] in ("입문", "중급", "고급"), f"{p['id']}: 난이도 {p['difficulty']}"
        for key in ("title", "prompt", "hint", "explanation", "source", "answerText"):
            assert p.get(key), f"{p['id']}: {key} 비어 있음"
        # 힌트에 정답 좌표가 그대로 노출되지 않아야 한다
        if p["type"] != "janggi":
            assert p["answerText"].split(" ")[0] not in p["hint"], f"{p['id']}: 힌트에 정답 노출"

    rows = []
    ok = 0
    for p in puzzles:
        try:
            if p["type"] == "go":
                detail = verify_go(p)
            elif p["type"] == "chess":
                detail = verify_chess(p)
            else:
                detail = verify_janggi(p)
            rows.append((p["id"], p["difficulty"], p["type"], "PASS", detail))
            ok += 1
        except AssertionError as e:
            rows.append((p["id"], p["difficulty"], p["type"], "FAIL", str(e)))

    from collections import Counter
    dist = Counter((p["type"], p["difficulty"]) for p in puzzles)
    print(f"{'ID':10} {'난이도':4} {'종목':5} {'결과':5} 검증 내용")
    for pid, diff, typ, res, detail in rows:
        print(f"{pid:10} {diff:4} {typ:5} {res:5} {detail}")
    print()
    print("난이도 분포:", dict(dist))
    print(f"통과 {ok}/{len(puzzles)}")
    if args.json_report:
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump([{"id": r[0], "difficulty": r[1], "type": r[2],
                        "result": r[3], "detail": r[4]} for r in rows],
                      f, ensure_ascii=False, indent=1)
    if ok != len(puzzles):
        sys.exit(1)


if __name__ == "__main__":
    main()
