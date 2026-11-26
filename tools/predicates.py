"""바둑 문항 검증 프리디케이트."""
from goban import Board

def group_at(b, r, c):
    pts, libs = b.group(r, c)
    return pts, libs

def captured_count(b_after, b_before):
    return len(b_before.g) + 1 - len(b_after.g)

def find_group_containing(b, pt):
    assert pt in b.g, f"no stone at {pt}"
    return b.group(pt[0], pt[1])

def move_result(board, mv, color):
    nb, cap = board.play(mv[0], mv[1], color)
    return nb, cap

def is_capture(board, mv, color, n):
    nb, cap = move_result(board, mv, color)
    return len(cap) == n

def capture_targets(board, mv, color, targets):
    """captures exactly the given set of points"""
    nb, cap = move_result(board, mv, color)
    return cap == set(targets)

def double_atari(board, mv, color, groups):
    """groups: list of representative points [(r,c), ...] each a white group that must end with exactly 1 liberty"""
    nb, cap = move_result(board, mv, color)
    libs_out = []
    for g in groups:
        if g not in nb.g:
            return False
        pts, libs = nb.group(g[0], g[1])
        libs_out.append(len(libs))
    return all(l == 1 for l in libs_out)

def atari_dead(board, mv, color, target, max_white_moves=200):
    """after black's move, the white group at `target` is in atari and white has no move that saves it
    (for every white legal move, black can capture the group next move)."""
    nb, cap = move_result(board, mv, color)
    if len(cap) > 0:
        # capturing immediately is a different goal
        return False
    if target not in nb.g:
        return False
    opp = 'W' if color == 'B' else 'B'
    pts, libs = nb.group(target[0], target[1])
    if len(libs) != 1:
        return False
    # white tries every legal move
    for wr in range(nb.n):
        for wc in range(nb.n):
            if (wr, wc) in nb.g:
                continue
            try:
                wb, wcap = nb.play(wr, wc, opp)
            except ValueError:
                continue
            # does the white group still exist and can black capture it?
            still = None
            for p in pts:
                if p in wb.g and wb.g[p] == opp:
                    still = p
                    break
            if still is None:
                continue  # white group is gone/captured — fine
            spts, slibs = wb.group(still[0], still[1])
            captured = False
            for lr, lc in slibs:
                try:
                    bb, bcap = wb.play(lr, lc, color)
                except ValueError:
                    continue
                if spts <= bcap:
                    captured = True
                    break
            if not captured:
                return False
    return True

def ko_move(board, mv, color):
    """black's move captures exactly one white stone and white's immediate recapture would repeat
    the previous position (simple ko)."""
    nb, cap = move_result(board, mv, color)
    if len(cap) != 1:
        return False
    captured_pt = next(iter(cap))
    opp = 'W' if color == 'B' else 'B'
    try:
        rb, rcap = nb.play(captured_pt[0], captured_pt[1], opp)
    except ValueError:
        return False
    # white recaptured: position must equal the original board
    if len(rcap) != 1:
        return False
    if rb.g != board.g:
        return False
    return True

def eyes_count(board, mv, color, group_pt):
    nb, cap = move_result(board, mv, color)
    if group_pt not in nb.g:
        return -1
    return len(nb.eyes(group_pt[0], group_pt[1]))

def two_eyes(board, mv, color, group_pt):
    return eyes_count(board, mv, color, group_pt) >= 2

def legal_moves_with(board, color, pred):
    out = []
    for mv in board.legal_moves(color):
        if pred(mv):
            out.append(mv)
    return out
