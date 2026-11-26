"""한국 장기(Janggi) 규칙 엔진 — 9열 × 10행.

좌표계: r=0 이 맨 윗줄(초 진영), r=9 가 맨 아랫줄(한 진영), c=0 이 맨 왼쪽.
기물 종류
    K 漢/楚 (궁)   R 車 (차)   P 包 (포)   M 馬 (마)
    E 象 (상)     G 士 (사)   S 兵/卒 (졸·병)
진영
    han  한(漢)·아래·빨강 — 전진 = r-1
    cho  초(楚)·위·청록  — 전진 = r+1

규칙(대한장기협회·한국 장기 정식 규칙 요약)
  · 차/포: 직선(가로·세로) 임의 거리. 궁성 대각선(모서리–중앙–반대 모서리)도 같은 방식으로 이동.
  · 포: 포가 아닌 기물을 정확히 하나 넘고, 그 뒤의 빈 칸은 얼마든지 간다. 넘는 기물도 잡는 기물도 포일 수 없다.
  · 마: 직선 한 칸 + 대각 한 칸. 직선 첫 칸(멱)이 비어 있어야 한다.
  · 상: 직선 한 칸 + 대각 두 칸. 직선 첫 칸과 대각 첫 칸(멱 두 곳)이 비어 있어야 한다.
  · 사/궁: 궁성 안에서 직선 한 칸 또는 궁성 대각선 한 칸. 궁성 밖으로 나갈 수 없다.
  · 졸/병: 전진 한 칸, 좌우 한 칸. 적 궁성 안에서는 대각선 전진 한 칸도 가능하다.
  · 자살수(자기 궁이 장군에 걸리는 수)와 빅장(두 궁이 같은 세로줄에서 마주 보는 수)은 둘 수 없다.
"""

ROWS, COLS = 10, 9

HAN, CHO = "han", "cho"

PALACE = {
    CHO: (0, 2, 3, 5),
    HAN: (7, 9, 3, 5),
}

# 궁성 대각선 4개(위 2 · 아래 2). 각 선은 세 점으로 이루어진다.
DIAG_SEGS = [
    [(0, 3), (1, 4), (2, 5)],
    [(0, 5), (1, 4), (2, 3)],
    [(7, 3), (8, 4), (9, 5)],
    [(7, 5), (8, 4), (9, 3)],
]

ORTH = [(-1, 0), (1, 0), (0, -1), (0, 1)]

HORSE_DELTAS = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
ELEPHANT_DELTAS = [(3, 2), (3, -2), (-3, 2), (-3, -2), (2, 3), (2, -3), (-2, 3), (-2, -3)]

SYMBOL = {
    HAN: {"K": "漢", "R": "車", "P": "包", "M": "馬", "E": "象", "G": "士", "S": "兵"},
    CHO: {"K": "楚", "R": "車", "P": "包", "M": "馬", "E": "象", "G": "士", "S": "卒"},
}
KIND_NAME = {"K": "궁", "R": "차", "P": "포", "M": "마", "E": "상", "G": "사", "S": ""}


def other(side):
    return CHO if side == HAN else HAN


def inside(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def palace_side(r, c):
    for side, (r0, r1, c0, c1) in PALACE.items():
        if r0 <= r <= r1 and c0 <= c <= c1:
            return side
    return None


def in_palace(side, r, c):
    r0, r1, c0, c1 = PALACE[side]
    return r0 <= r <= r1 and c0 <= c <= c1


def diag_rays(r, c):
    """이 점이 궁성 대각선 위에 있을 때, 그 선을 따라 나아갈 수 있는 방향별 점 목록."""
    out = []
    for seg in DIAG_SEGS:
        if (r, c) in seg:
            i = seg.index((r, c))
            for step in (-1, 1):
                pts = []
                j = i + step
                while 0 <= j < len(seg):
                    pts.append(seg[j])
                    j += step
                if pts:
                    out.append(pts)
    return out


def orth_line(r, c, dr, dc):
    """직선 방향으로 나아가며 만나는 점 목록(판 끝까지)."""
    pts = []
    tr, tc = r + dr, c + dc
    while inside(tr, tc):
        pts.append((tr, tc))
        tr += dr
        tc += dc
    return pts


def _sign(x):
    return (x > 0) - (x < 0)


def pseudo_moves(board, r, c):
    """board: {(r,c): (kind, side)} → 이 기물이 갈 수 있는 칸(자기 궁 안전은 따지지 않음)."""
    piece = board.get((r, c))
    if not piece:
        return []
    kind, side = piece
    out = []

    def add(tr, tc):
        if not inside(tr, tc):
            return
        t = board.get((tr, tc))
        if t is not None and t[1] == side:
            return
        out.append((tr, tc))

    if kind in ("K", "G"):
        for dr, dc in ORTH:
            tr, tc = r + dr, c + dc
            if in_palace(side, tr, tc):
                add(tr, tc)
        for pts in diag_rays(r, c):
            tr, tc = pts[0]
            if in_palace(side, tr, tc):
                add(tr, tc)

    elif kind == "M":
        for dr, dc in HORSE_DELTAS:
            sr = r + _sign(dr) if abs(dr) == 2 else r
            sc = c + _sign(dc) if abs(dc) == 2 else c
            if not inside(sr, sc):
                continue
            if (sr, sc) in board:
                continue
            add(r + dr, c + dc)

    elif kind == "E":
        for dr, dc in ELEPHANT_DELTAS:
            if abs(dr) == 3:
                p1 = (r + _sign(dr), c)
                p2 = (r + 2 * _sign(dr), c + _sign(dc))
            else:
                p1 = (r, c + _sign(dc))
                p2 = (r + _sign(dr), c + 2 * _sign(dc))
            if not inside(*p1) or not inside(*p2):
                continue
            if p1 in board or p2 in board:
                continue
            add(r + dr, c + dc)

    elif kind == "R":
        for dr, dc in ORTH:
            for (tr, tc) in orth_line(r, c, dr, dc):
                t = board.get((tr, tc))
                if t is None:
                    out.append((tr, tc))
                else:
                    if t[1] != side:
                        out.append((tr, tc))
                    break
        for pts in diag_rays(r, c):
            for (tr, tc) in pts:
                t = board.get((tr, tc))
                if t is None:
                    out.append((tr, tc))
                else:
                    if t[1] != side:
                        out.append((tr, tc))
                    break

    elif kind == "P":
        # 포는 사이에 포가 아닌 기물이 정확히 하나 있어야 하고, 그 뒤의 빈 칸은
        # 얼마든지 갈 수 있다. 그 다음 기물을 잡을 때는 그 기물이 포이면 안 된다.
        lines = [orth_line(r, c, dr, dc) for dr, dc in ORTH] + diag_rays(r, c)
        for line in lines:
            screen_i = None
            for i, pt in enumerate(line):
                if pt in board:
                    screen_i = i
                    break
            if screen_i is None:
                continue
            if board[line[screen_i]][0] == "P":
                continue
            for j in range(screen_i + 1, len(line)):
                tr, tc = line[j]
                t = board.get((tr, tc))
                if t is None:
                    out.append((tr, tc))
                    continue
                if t[1] != side and t[0] != "P":
                    out.append((tr, tc))
                break

    elif kind == "S":
        fwd = -1 if side == HAN else 1
        for dr, dc in [(fwd, 0), (0, -1), (0, 1)]:
            add(r + dr, c + dc)
        here = palace_side(r, c)
        if here is not None:
            for pts in diag_rays(r, c):
                tr, tc = pts[0]
                if palace_side(tr, tc) != here:
                    continue
                if tr - r != fwd:
                    continue
                add(tr, tc)

    else:
        raise ValueError("unknown kind " + str(kind))
    return out


def find_king(board, side):
    for (r, c), (k, s) in board.items():
        if s == side and k == "K":
            return (r, c)
    return None


def attacked(board, sq, by_side):
    """sq 가 by_side 기물의 공격을 받는가(장군 판정)."""
    if sq is None:
        return False
    for pos, (k, s) in board.items():
        if s != by_side:
            continue
        if sq in pseudo_moves(board, pos[0], pos[1]):
            return True
    return False


def attackers(board, sq, by_side):
    out = []
    if sq is None:
        return out
    for pos, (k, s) in board.items():
        if s != by_side:
            continue
        if sq in pseudo_moves(board, pos[0], pos[1]):
            out.append(pos)
    return out


def kings_face(board):
    hk = find_king(board, HAN)
    ck = find_king(board, CHO)
    if not hk or not ck or hk[1] != ck[1]:
        return False
    c = hk[1]
    lo, hi = sorted([hk[0], ck[0]])
    for r in range(lo + 1, hi):
        if (r, c) in board:
            return False
    return True


def in_check(board, side):
    return attacked(board, find_king(board, side), other(side))


def apply_move(board, src, dst):
    nb = dict(board)
    piece = nb.pop(src)
    nb[dst] = piece
    return nb, board.get(dst)


def legal_moves(board, side):
    out = []
    for pos, (kind, s) in list(board.items()):
        if s != side:
            continue
        for dst in pseudo_moves(board, pos[0], pos[1]):
            nb, _ = apply_move(board, pos, dst)
            if kings_face(nb):
                continue
            kp = find_king(nb, side)
            if kp is None:
                continue
            if attacked(nb, kp, other(side)):
                continue
            out.append((pos, dst))
    return out


def is_mate(board, side):
    """side 차례일 때 외통(장군 + 합법수 없음)인가."""
    if not in_check(board, side):
        return False
    return not legal_moves(board, side)


def mate_moves(board, side):
    out = []
    for (src, dst) in legal_moves(board, side):
        nb, _ = apply_move(board, src, dst)
        if is_mate(nb, other(side)):
            out.append((src, dst))
    return out


def from_pieces(pieces):
    """[(side, kind, r, c), ...] → board dict"""
    board = {}
    for side, kind, r, c in pieces:
        if not inside(r, c):
            raise ValueError("좌표 범위 밖 %s %s %s" % (side, kind, (r, c)))
        if (r, c) in board:
            raise ValueError("같은 칸에 기물 두 개 %s" % ((r, c),))
        board[(r, c)] = (kind, side)
    return board


def position_problems(board):
    """문항으로 쓸 수 없는 국면이면 이유 목록을 돌려준다."""
    problems = []
    for side in (HAN, CHO):
        if find_king(board, side) is None:
            problems.append("%s 궁 없음" % side)
    if problems:
        return problems
    if kings_face(board):
        problems.append("빅장(두 궁이 마주 봄)")
    for (r, c), (k, s) in board.items():
        if k in ("K", "G") and not in_palace(s, r, c):
            problems.append("%s %s 가 궁성 밖(%d,%d)" % (s, k, r + 1, c + 1))
    if in_check(board, HAN):
        problems.append("한이 이미 장군")
    if in_check(board, CHO):
        problems.append("초가 이미 장군")
    if not legal_moves(board, CHO):
        problems.append("초의 합법수 없음(이미 외통)")
    limits = {"K": 1, "G": 2, "R": 2, "P": 2, "M": 2, "E": 2, "S": 5}
    counts = {}
    for (k, s) in board.values():
        counts[(s, k)] = counts.get((s, k), 0) + 1
    for side in (HAN, CHO):
        for kind, limit in limits.items():
            n = counts.get((side, kind), 0)
            if n > limit:
                problems.append("%s %s %d개 (최대 %d)" % (side, kind, n, limit))
    return problems


def ascii_board(board, mark=None, targets=None):
    """사람이 읽는 보드 그림. mark/targets 는 (r,c) 집합."""
    mark = mark or set()
    targets = set(targets or [])
    label = {HAN: "h", CHO: "c"}
    lines = ["     1  2  3  4  5  6  7  8  9"]
    for r in range(ROWS):
        cells = []
        for c in range(COLS):
            p = board.get((r, c))
            if p is None:
                ch = "**" if (r, c) in mark else ("++" if (r, c) in targets else " .")
            else:
                ch = label[p[1]] + p[0]
                if (r, c) in mark:
                    ch = "[" + ch[1] + "]"
                elif (r, c) in targets:
                    ch = "<" + ch[1] + ">"
            cells.append(ch)
        lines.append("%2d  %s" % (r + 1, " ".join(cells)))
    return "\n".join(lines)
