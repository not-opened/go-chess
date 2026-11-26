"""9x9 바둑 규칙 엔진: 활로/따내기/자충수/패 검증용."""
from collections import deque

N = 9

def neighbors(r, c, n=N):
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        rr, cc = r+dr, c+dc
        if 0 <= rr < n and 0 <= cc < n:
            yield rr, cc

class Board:
    def __init__(self, n=N, stones=()):
        self.n = n
        self.g = {}
        for s in stones:
            key = (s[0], s[1])
            if key in self.g:
                raise ValueError(f"duplicate stone at {key}")
            self.g[key] = s[2]
    def copy(self):
        b = Board(self.n)
        b.g = dict(self.g)
        return b
    def get(self, r, c):
        return self.g.get((r, c))
    def group(self, r, c):
        """returns (set of points, set of liberties) for the group at (r,c)"""
        color = self.g[(r, c)]
        seen = {(r, c)}
        libs = set()
        dq = deque([(r, c)])
        while dq:
            cr, cc = dq.popleft()
            for rr, kk in neighbors(cr, cc, self.n):
                v = self.g.get((rr, kk))
                if v is None:
                    libs.add((rr, kk))
                elif v == color and (rr, kk) not in seen:
                    seen.add((rr, kk))
                    dq.append((rr, kk))
        return seen, libs
    def groups(self):
        seen = set()
        out = []
        for (r, c), color in self.g.items():
            if (r, c) in seen:
                continue
            pts, libs = self.group(r, c)
            seen |= pts
            out.append((color, pts, libs))
        return out
    def play(self, r, c, color):
        """plays a move; returns (new_board, captured_points) or raises Illegal"""
        if (r, c) in self.g:
            raise ValueError("occupied")
        b = self.copy()
        b.g[(r, c)] = color
        opp = 'W' if color == 'B' else 'B'
        captured = set()
        for rr, kk in neighbors(r, c, self.n):
            if b.g.get((rr, kk)) == opp:
                pts, libs = b.group(rr, kk)
                if not libs:
                    for p in pts:
                        del b.g[p]
                    captured |= pts
        _, own_libs = b.group(r, c)
        if not own_libs:
            raise ValueError("suicide")
        return b, captured
    def legal_moves(self, color):
        out = []
        for r in range(self.n):
            for c in range(self.n):
                if (r, c) in self.g:
                    continue
                try:
                    self.play(r, c, color)
                except ValueError:
                    continue
                out.append((r, c))
        return out
    def eyes(self, r, c):
        """true eyes of the group at (r,c): empty points all of whose neighbours are the group or the edge"""
        pts, _ = self.group(r, c)
        own = pts
        eyes = set()
        for (pr, pc) in pts:
            for rr, kk in neighbors(pr, pc, self.n):
                if (rr, kk) in self.g:
                    continue
                ok = True
                for r2, k2 in neighbors(rr, kk, self.n):
                    if (r2, k2) not in own:
                        ok = False
                        break
                if ok:
                    eyes.add((rr, kk))
        return eyes
    def __str__(self):
        rows = []
        for r in range(self.n):
            row = ''
            for c in range(self.n):
                v = self.g.get((r, c))
                row += '.' if v is None else v
            rows.append(f"{r} {row}")
        return '\n'.join(rows)

def stones_from(*spec):
    out = []
    for color, pts in spec:
        for p in pts:
            out.append((p[0], p[1], color))
    return out
