"""notopened 바둑·체스 한 수 미니 — 20문항 원본 데이터.

이 파일이 문항의 유일한 원본이다. render_puzzles.py 가 JSON 으로 바꿔 index.html 에 넣고,
verify_puzzles.py 가 index.html 의 JSON 을 다시 읽어 규칙 검산을 한다.
"""
import chess

GO_SOURCE_RULES = "한국기원 바둑 규칙"
GO_SOURCE_BEGIN = "한국기원 바둑 입문 가이드"
CHESS_SOURCE = "FIDE Laws of Chess"

# ---------------------------------------------------------------- 바둑 10문항

GO = [
    dict(
        id="go-01", difficulty="입문",
        title="1. 양단수 — 두 점을 동시에 단수로",
        prompt="흑 차례입니다. 백 두 점의 활로를 한 수로 각각 하나씩만 남기는 급소를 탭하세요.",
        hint="백 두 점이 서로 닿지 않습니다. 두 점에 동시에 닿는 자리가 하나 있습니다.",
        answer=(4, 4), answer_text="5행 5열",
        stones=[("B", 2, 3), ("B", 2, 4), ("B", 3, 3), ("B", 4, 2), ("W", 3, 4), ("W", 4, 3)],
        check=dict(kind="double_atari", groups=[(3, 4), (4, 3)]),
        explanation="정답은 5행 5열(양단수)입니다. 이 한 수로 4행 5열 백돌과 5행 4열 백돌의 활로가 각각 하나씩만 남습니다. 백이 한쪽을 이어도 다른 쪽은 그대로 잡힙니다.",
        source=GO_SOURCE_BEGIN,
    ),
    dict(
        id="go-02", difficulty="입문",
        title="2. 한 점 따내기",
        prompt="흑 차례입니다. 활로가 하나만 남은 백돌을 바로 들어내는 자리를 탭하세요.",
        hint="백돌의 위·아래·왼쪽은 이미 흑돌입니다. 남은 한 방향만 막으면 됩니다.",
        answer=(2, 3), answer_text="3행 4열",
        stones=[("B", 1, 2), ("B", 2, 1), ("B", 3, 2), ("W", 2, 2)],
        check=dict(kind="capture", count=1),
        explanation="정답은 3행 4열, 백돌 오른쪽의 마지막 활로입니다. 네 방향 활로가 모두 막혀 3행 3열의 백돌은 판에서 들어납니다.",
        source=GO_SOURCE_RULES,
    ),
    dict(
        id="go-03", difficulty="입문",
        title="3. 변(1선)에 몰린 백돌 따내기",
        prompt="흑 차례입니다. 바둑판 맨 윗변에 붙은 백돌을 잡는 마지막 한 수를 두세요.",
        hint="변에 붙은 돌은 원래부터 활로가 세 개뿐입니다. 그중 남은 하나는 백돌의 오른쪽입니다.",
        answer=(0, 5), answer_text="1행 6열",
        stones=[("B", 0, 3), ("B", 1, 4), ("W", 0, 4)],
        check=dict(kind="capture", count=1),
        explanation="정답은 1행 6열입니다. 변(1선)에 붙은 백돌은 활로가 세 개뿐이라, 왼쪽·아래를 막은 상태에서 오른쪽 하나를 메우면 바로 따낼 수 있습니다.",
        source=GO_SOURCE_BEGIN,
    ),
    dict(
        id="go-04", difficulty="입문",
        title="4. 붙어 있는 두 점 한 번에 따내기",
        prompt="흑 차례입니다. 나란히 붙은 백 두 점을 한 수로 함께 들어내세요.",
        hint="두 점은 붙어 있어 활로를 함께 씁니다. 그중 마지막 하나가 남아 있습니다.",
        answer=(3, 2), answer_text="4행 3열",
        stones=[("B", 1, 2), ("B", 1, 3), ("B", 2, 1), ("B", 2, 4), ("B", 3, 3), ("W", 2, 2), ("W", 2, 3)],
        check=dict(kind="capture", count=2),
        explanation="정답은 4행 3열입니다. 3행 3열·3행 4열 백 두 점이 함께 쓰던 마지막 활로를 막아, 두 점을 한 번에 들어냅니다.",
        source=GO_SOURCE_RULES,
    ),
    dict(
        id="go-05", difficulty="중급",
        title="5. 귀에 몰린 백 세 점 따내기",
        prompt="흑 차례입니다. 귀퉁이에 몰린 백 세 점을 한 수로 따내세요.",
        hint="귀는 두 변이 이미 막혀 있어 활로가 가장 빨리 줄어듭니다. 남은 한 자리는 귀의 모서리입니다.",
        answer=(0, 0), answer_text="1행 1열",
        stones=[("B", 0, 2), ("B", 1, 2), ("B", 2, 1), ("B", 2, 0), ("W", 0, 1), ("W", 1, 1), ("W", 1, 0)],
        check=dict(kind="capture", count=3),
        explanation="정답은 1행 1열입니다. 1행 2열·2행 2열·2행 1열 백 세 점이 함께 쓰던 마지막 활로(귀의 모서리)를 메워 세 점을 한꺼번에 들어냅니다.",
        source=GO_SOURCE_RULES,
    ),
    dict(
        id="go-06", difficulty="중급",
        title="6. 단수로 몰아 잡기 (자충수 함정)",
        prompt="흑 차례입니다. 윗변의 백 두 점을 단수로 몰아 다음 수에 잡는 자리를 두세요.",
        hint="단수만 걸면 백이 그 자리를 스스로 메워 살아날 수 있습니다. 백이 메울 수 없는 자리로 몰아야 합니다.",
        answer=(0, 3), answer_text="1행 4열",
        stones=[("B", 0, 0), ("B", 1, 0), ("B", 1, 2), ("B", 2, 1), ("W", 0, 1), ("W", 0, 2)],
        check=dict(kind="atari_dead", target=(0, 1), trap=dict(point=(1, 1), color="W")),
        explanation="정답은 1행 4열입니다. 백 두 점은 활로가 2행 2열 하나만 남지만, 그 자리는 흑돌에 둘러싸여 백이 스스로 메우면 자충수가 됩니다. 백이 어디에 두어도 다음 수에 두 점을 들어냅니다.",
        source="한국기원 바둑 규칙 · 자충수",
    ),
    dict(
        id="go-07", difficulty="중급",
        title="7. 두 그룹 동시 양단수",
        prompt="흑 차례입니다. 위쪽 백 두 점과 아래쪽 백 두 점을 한 수로 동시에 단수에 몰아넣으세요.",
        hint="두 백 그룹이 함께 쓰는 활로가 하나 있습니다. 그 자리를 차지하면 양쪽이 동시에 단수입니다.",
        answer=(2, 4), answer_text="3행 5열",
        stones=[
            ("B", 1, 2), ("B", 3, 2), ("B", 2, 1), ("B", 1, 3), ("B", 0, 4), ("B", 2, 5), ("B", 1, 6),
            ("W", 2, 2), ("W", 2, 3), ("W", 1, 4), ("W", 1, 5),
        ],
        check=dict(kind="double_atari", groups=[(2, 2), (1, 4)]),
        explanation="정답은 3행 5열입니다. 이 한 수로 3행 3열·3행 4열 백 두 점과 2행 5열·2행 6열 백 두 점이 모두 단수가 됩니다. 한쪽을 이어도 다른 쪽은 잡힙니다.",
        source=GO_SOURCE_BEGIN,
    ),
    dict(
        id="go-08", difficulty="중급",
        title="8. 사활 — 3집 궁도에서 두 눈 만들기",
        prompt="흑 차례입니다. 아래변 흑 대마가 완전히 살 수 있도록 두 눈을 만드는 급소를 두세요.",
        hint="집이 될 수 있는 빈 자리는 세 개입니다. 가운데를 차지해야 좌우로 집이 갈라집니다.",
        answer=(8, 1), answer_text="9행 2열",
        stones=[
            ("B", 7, 0), ("B", 7, 1), ("B", 7, 2), ("B", 7, 3), ("B", 8, 3),
            ("W", 6, 0), ("W", 6, 1), ("W", 6, 2), ("W", 6, 3), ("W", 7, 4), ("W", 8, 4),
        ],
        check=dict(kind="two_eyes", group=(7, 0)),
        explanation="정답은 9행 2열, 3집 궁도의 한가운데입니다. 남는 9행 1열과 9행 3열이 각각 진짜 집이 되어 두 눈이 완성됩니다. 양 끝에 두면 집이 하나로 남아 죽습니다.",
        source="한국기원 바둑 입문 가이드 · 사활",
    ),
    dict(
        id="go-09", difficulty="고급",
        title="9. 패 만들기",
        prompt="흑 차례입니다. 백 한 점을 따내면서 패 모양을 만드는 수를 두세요.",
        hint="백 한 점이 단수입니다. 그 점을 따내면 흑돌도 활로 하나만 남는 자리가 됩니다.",
        answer=(2, 3), answer_text="3행 4열",
        stones=[("B", 1, 2), ("B", 3, 2), ("B", 2, 1), ("W", 2, 2), ("W", 1, 3), ("W", 3, 3), ("W", 2, 4)],
        check=dict(kind="ko"),
        explanation="정답은 3행 4열입니다. 3행 3열 백 한 점을 따내는 동시에, 새로 둔 흑돌의 활로가 3행 3열 하나만 남습니다. 백이 곧바로 되따내면 판이 똑같아지므로 패 규칙상 둘 수 없고, 백은 다른 곳에 패를 써야 합니다.",
        source="한국기원 바둑 규칙 · 패",
    ),
    dict(
        id="go-10", difficulty="고급",
        title="10. 사활 — 나카데로 백 죽이기",
        prompt="흑 차례입니다. 오른쪽 위 귀의 백 대마를 죽이는 급소를 두세요.",
        hint="백의 집 자리는 세 개입니다. 그 한가운데에 흑이 들어가면 백의 두 집이 가짜 집이 됩니다.",
        answer=(0, 7), answer_text="1행 8열",
        stones=[
            ("W", 1, 8), ("W", 1, 7), ("W", 1, 6), ("W", 1, 5), ("W", 0, 5),
            ("B", 0, 4), ("B", 1, 4), ("B", 2, 5), ("B", 2, 6), ("B", 2, 7), ("B", 2, 8),
        ],
        check=dict(kind="kill_nakade", group=(1, 7)),
        explanation="정답은 1행 8열, 백의 3집 궁도 한가운데입니다. 이 자리에 흑돌이 들어가면 1행 7열과 1행 9열이 서로 이어지지 못해 진짜 두 눈이 되지 못합니다. 백이 어떻게 두어도 두 눈을 만들 수 없어 대마가 죽습니다.",
        source="한국기원 바둑 입문 가이드 · 나카데",
    ),
]

# ---------------------------------------------------------------- 체스 10문항

CHESS = [
    dict(
        id="chess-01", difficulty="입문",
        title="1. 백랭크 1수 체크메이트 (백선)",
        prompt="백 차례입니다. 백 룩(♖, a1)을 움직여 단 한 수로 체크메이트를 만드세요.",
        hint="흑 킹 앞줄이 자기 폰 세 개로 막혀 있습니다. 룩이 그 줄을 통째로 차지하면?",
        fen="6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
        san="Ra8#", answer=(0, 0), answer_text="a8 (Ra8#)",
        check=dict(kind="mate"),
        explanation="정답은 a8, Ra8#입니다. 룩이 8랭크를 장악하면 흑 킹(g8)은 f7·g7·h7 폰에 가로막혀 있고 f8·h8도 모두 룩의 사정권이라 빠져나갈 칸이 없습니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-02", difficulty="입문",
        title="2. 퀸 + 킹 1수 체크메이트 (백선)",
        prompt="백 차례입니다. 백 퀸(♕, e3)과 백 킹(♔, g6)의 협공으로 단 한 수 체크메이트를 만드세요.",
        hint="백 킹이 흑 킹의 옆칸들을 이미 막고 있습니다. 퀸이 마지막 줄로 내려가면?",
        fen="7k/8/6K1/8/8/4Q3/8/8 w - - 0 1",
        san="Qe8#", answer=(0, 4), answer_text="e8 (Qe8#)",
        check=dict(kind="mate"),
        explanation="정답은 e8, Qe8#입니다. 백 킹(g6)이 h7·g7을 지키고 있어 흑 킹(h8)은 옆으로도 아래로도 갈 수 없고, g8도 퀸의 사정권입니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-03", difficulty="입문",
        title="3. 질식(스모더드) 메이트 (백선)",
        prompt="백 차례입니다. 백 나이트(♘, e5)로 흑 킹(♚, h8)을 단 한 수에 메이트로 몰아넣으세요.",
        hint="흑 킹은 자기 룩과 폰 두 개에 둘러싸여 있습니다. 나이트가 들어갈 수 있는 칸은?",
        fen="6rk/6pp/8/4N3/8/8/8/4K3 w - - 0 1",
        san="Nf7#", answer=(1, 5), answer_text="f7 (Nf7#)",
        check=dict(kind="mate"),
        explanation="정답은 f7, Nf7#입니다. 흑 킹(h8)은 g8 룩과 g7·h7 폰에 갇혀 있고, f7의 나이트를 잡을 기물도 없어 질식 메이트가 완성됩니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-04", difficulty="입문",
        title="4. 나이트 로열 포크 (백선)",
        prompt="백 차례입니다. 백 나이트(♘, d5)로 흑 킹(♚, e8)에 체크를 걸면서 흑 퀸(♛, a8)까지 동시에 공격하세요.",
        hint="나이트가 흑 킹과 흑 퀸을 한꺼번에 노릴 수 있는 칸은 하나뿐입니다.",
        fen="q3k3/8/8/3N4/8/8/8/4K3 w - - 0 1",
        san="Nc7+", answer=(1, 2), answer_text="c7 (Nc7+)",
        check=dict(kind="fork", target="a8"),
        explanation="정답은 c7, Nc7+입니다. 나이트가 흑 킹에 체크를 걸면서 a8의 퀸을 함께 물고 있습니다. 나이트 체크는 막을 수 없어 흑은 킹을 피할 수밖에 없고, 다음 수에 퀸을 잡습니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-05", difficulty="중급",
        title="5. 룩 스큐어로 퀸 잡기 (백선)",
        prompt="백 차례입니다. 백 룩(♖, h1)으로 흑 킹(♚, g8)을 체크해 물러나게 하고, 그 뒤에 있는 흑 퀸(♛, a8)을 노리세요.",
        hint="흑 킹과 흑 퀸이 같은 8랭크에 나란히 있습니다. 룩이 들어갈 자리를 비숍이 지켜 주는지도 확인하세요.",
        fen="q5k1/8/8/8/3B4/8/8/4K2R w - - 0 1",
        san="Rh8+", answer=(0, 7), answer_text="h8 (Rh8+)",
        check=dict(kind="skewer", target="a8"),
        explanation="정답은 h8, Rh8+입니다. 룩은 비숍(d4)이 지켜 주므로 흑 킹(g8)이 잡을 수 없습니다. g7도 그 비숍이 막고, 8랭크(f8·h8)는 룩의 사정권이라 흑은 f7로만 피할 수 있습니다. 킹이 비키면 룩이 a8의 퀸을 잡습니다(스큐어).",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-06", difficulty="중급",
        title="6. 나이트 엄호 룩 메이트 (백선)",
        prompt="백 차례입니다. 백 룩(♖, c7)과 나이트(♘, f8)로 흑 킹(♚, h6)을 단 한 수에 메이트로 몰아넣으세요.",
        hint="흑 킹 바로 옆칸으로 룩을 붙일 수 있습니다. 그 칸을 나이트가 지켜 주는지 확인하세요.",
        fen="1K3N2/2R5/7k/6p1/8/8/6p1/8 w - - 0 1",
        san="Rh7#", answer=(1, 7), answer_text="h7 (Rh7#)",
        check=dict(kind="mate"),
        explanation="정답은 h7, Rh7#입니다. f8의 나이트가 h7을 지키고 있어 흑 킹이 룩을 잡을 수 없습니다. g6은 나이트, g7은 룩이 막고, h5는 룩이 내려다보는 파일이며 g5는 흑 폰이라 갈 곳이 없습니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-07", difficulty="중급",
        title="7. 퀸 + 킹 밀착 메이트 (백선)",
        prompt="백 차례입니다. 백 퀸(♕, g5)을 흑 킹(♚, e6) 바로 옆에 붙여, 백 킹(♔, f4)의 엄호를 받는 메이트를 만드세요.",
        hint="킹 옆에 붙는 퀸은 그 자체로 강합니다. 백 킹이 그 칸을 지켜 주는지 보세요.",
        fen="8/1R6/4k3/6Q1/3p1K2/8/8/8 w - - 0 1",
        san="Qe5#", answer=(3, 4), answer_text="e5 (Qe5#)",
        check=dict(kind="mate"),
        explanation="정답은 e5, Qe5#입니다. 백 킹(f4)이 e5의 퀸을 지켜 흑 킹이 퀸을 잡을 수 없습니다. d5·d6·f5·f6은 퀸이, d7·e7·f7은 룩(b7)이 막아 나갈 칸이 없습니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-08", difficulty="고급",
        title="8. 발견 체크 메이트 (백선)",
        prompt="백 차례입니다. 백 나이트(♘, e5)가 비켜 주면 룩(♖, e1)의 체크가 열립니다. 흑 킹의 탈출로까지 막는 단 한 수를 찾으세요.",
        hint="나이트가 어디로 가야 흑 킹의 d8 탈출로까지 막을 수 있을까요?",
        fen="4k3/3p1p2/8/2B1N3/8/8/8/4R1K1 w - - 0 1",
        san="Nc6#", answer=(2, 2), answer_text="c6 (Nc6#)",
        check=dict(kind="mate"),
        explanation="정답은 c6, Nc6#입니다. 나이트가 e5를 비우자 e파일의 룩이 흑 킹(e8)을 체크합니다. e7은 그 룩의 사정권이고, c6의 나이트가 d8을, 비숍(c5)이 f8을 막습니다. d7·f7은 흑 폰이 막아 탈출로가 없습니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-09", difficulty="고급",
        title="9. 8랭크 장악 — 잡으면서 메이트 (백선)",
        prompt="백 차례입니다. 흑 룩(♜, f8)이 8랭크를 막고 있습니다. 단 한 수로 메이트를 만드세요.",
        hint="흑 룩을 그냥 잡는 수가 왜 메이트가 되는지, 흑 킹의 옆칸을 확인해 보세요.",
        fen="N4r1k/8/6K1/8/8/8/8/5Q2 w - - 0 1",
        san="Qxf8#", answer=(0, 5), answer_text="f8 (Qxf8#)",
        check=dict(kind="mate"),
        explanation="정답은 f8, Qxf8#입니다. 퀸이 흑 룩을 잡아내며 8랭크를 장악하고, 백 킹(g6)이 h7·g7을 막고 있어 흑 킹(h8)은 g8으로도 나갈 수 없습니다.",
        source=CHESS_SOURCE,
    ),
    dict(
        id="chess-10", difficulty="고급",
        title="10. 룩 + 킹 + 나이트 협공 메이트 (백선)",
        prompt="백 차례입니다. 백 룩(♖, d2)으로 흑 킹(♚, a4)을 단 한 수에 메이트로 몰아넣으세요.",
        hint="흑 킹이 나갈 수 있는 칸을 백 킹과 나이트, 그리고 룩 자신이 모두 막는 자리를 찾으세요.",
        fen="8/8/8/N7/k1K5/3p4/3Rp3/8 w - - 0 1",
        san="Ra2#", answer=(6, 0), answer_text="a2 (Ra2#)",
        check=dict(kind="mate"),
        explanation="정답은 a2, Ra2#입니다. 룩이 a파일로 체크하면 흑 킹(a4)은 a3으로 갈 수 없고, a5의 나이트를 잡아도 룩이 그 칸을 지킵니다. b3·b4·b5는 백 킹(c4)이 막으며, 흑 폰으로는 a3을 막을 수 없습니다.",
        source=CHESS_SOURCE,
    ),
]

ALL = GO + CHESS

PIECE_SYMBOL = {
    (chess.PAWN, chess.WHITE): "♙", (chess.KNIGHT, chess.WHITE): "♘",
    (chess.BISHOP, chess.WHITE): "♗", (chess.ROOK, chess.WHITE): "♖",
    (chess.QUEEN, chess.WHITE): "♕", (chess.KING, chess.WHITE): "♔",
    (chess.PAWN, chess.BLACK): "♟", (chess.KNIGHT, chess.BLACK): "♞",
    (chess.BISHOP, chess.BLACK): "♝", (chess.ROOK, chess.BLACK): "♜",
    (chess.QUEEN, chess.BLACK): "♛", (chess.KING, chess.BLACK): "♚",
}


def chess_pieces(fen, san):
    """FEN → 앱 보드 좌표(r=8-rank, c=file). 착수 기물에는 mover 표시."""
    board = chess.Board(fen)
    move = None
    for m in board.legal_moves:
        if board.san(m) == san:
            move = m
            break
    if move is None:
        raise ValueError(f"san not legal: {san} in {fen}")
    out = []
    for sq, piece in board.piece_map().items():
        r = 7 - chess.square_rank(sq)
        c = chess.square_file(sq)
        out.append(dict(
            r=r, c=c,
            symbol=PIECE_SYMBOL[(piece.piece_type, piece.color)],
            side="W" if piece.color == chess.WHITE else "B",
            mover=(sq == move.from_square),
        ))
    out.sort(key=lambda p: (p["r"], p["c"]))
    mover_piece = board.piece_at(move.from_square)
    return out, PIECE_SYMBOL[(mover_piece.piece_type, mover_piece.color)], move


def to_json():
    puzzles = []
    for p in ALL:
        item = dict(
            id=p["id"], type="go" if p["id"].startswith("go") else "chess",
            difficulty=p["difficulty"], title=p["title"], prompt=p["prompt"],
            hint=p["hint"], explanation=p["explanation"], source=p["source"],
            answerText=p["answer_text"], check=p["check"],
        )
        if item["type"] == "go":
            item["typeLabel"] = "⚫ 바둑 9×9"
            item["size"] = 9
            item["stones"] = [dict(r=r, c=c, color=col) for col, r, c in p["stones"]]
            item["answer"] = dict(r=p["answer"][0], c=p["answer"][1])
        else:
            pieces, mover_symbol, move = chess_pieces(p["fen"], p["san"])
            item["typeLabel"] = "♟️ 체스 8×8"
            item["size"] = 8
            item["fen"] = p["fen"]
            item["san"] = p["san"]
            item["pieces"] = pieces
            item["moverSymbol"] = mover_symbol
            item["moverFrom"] = dict(r=7 - chess.square_rank(move.from_square), c=chess.square_file(move.from_square))
            item["answer"] = dict(r=p["answer"][0], c=p["answer"][1])
        puzzles.append(item)
    return puzzles


if __name__ == "__main__":
    import json
    print(json.dumps(to_json(), ensure_ascii=False, indent=1)[:2000])
