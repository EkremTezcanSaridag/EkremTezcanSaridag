#!/usr/bin/env python3
"""
Interactive GitHub Profile Chess Engine & Obsidian/Gold SVG Board Renderer.
Updates game/state.json, assets/chessboard.svg, and README.md.
"""

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

REPO = "EkremTezcanSaridag/EkremTezcanSaridag"
ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "game" / "state.json"
BOARD_SVG_PATH = ROOT / "assets" / "chessboard.svg"
README_PATH = ROOT / "README.md"

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

FILES = "abcdefgh"
RANKS = "87654321"

PIECE_ORDER = {"K": 0, "Q": 1, "R": 2, "B": 3, "N": 4, "P": 5}
PIECE_ICONS = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}


def piece_svg_markup(piece: str, x: int, y: int) -> str:
    """Return crisp Staunton-inspired vector SVG markup for a chess piece in a 60x60 square."""
    is_white = piece.isupper()
    kind = piece.upper()
    fill = "url(#wGold)" if is_white else "#0F131C"
    stroke = "#5C4008" if is_white else "#B8C2D4"
    accent = "#FFF7DC" if is_white else "#7E8BA3"
    sw = "1.25" if is_white else "1.6"

    # Inner paths designed on a 45x45 coordinate grid, centered inside 60x60
    tx = x + 7.5
    ty = y + 7.5

    if kind == "P":
        inner = (
            f'<circle cx="22.5" cy="13.5" r="5" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<path d="M18.2 19 C17.3 23.6 15 27.6 13.8 32 H31.2 C30 27.6 27.7 23.6 26.8 19 Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<rect x="11.5" y="32.5" width="22" height="4.8" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
    elif kind == "R":
        inner = (
            f'<path d="M11 9.5 H15.5 V13 H19.8 V9.5 H25.2 V13 H29.5 V9.5 H34 V17 L30.5 20 V31 '
            f'L34 34.5 V38 H11 V34.5 L14.5 31 V20 L11 17 Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<line x1="14.5" y1="20" x2="30.5" y2="20" stroke="{accent}" stroke-width="1.1" opacity="0.7"/>'
            f'<line x1="14.5" y1="31" x2="30.5" y2="31" stroke="{accent}" stroke-width="1.1" opacity="0.7"/>'
        )
    elif kind == "N":
        eye = "#1A1306" if is_white else "#C9D3E6"
        inner = (
            f'<rect x="12" y="33.5" width="21" height="4.5" rx="1.6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<path d="M15 33.5 C15.6 26.8 18.8 23.8 22 21.3 C18.8 21.3 15.8 22.3 13.2 23.4 '
            f'C11.6 24 10.2 22.7 10.7 21 C11.5 18.2 14.3 15 16.8 12.8 C17.1 10.6 18.2 8.5 20.2 7 '
            f'L21.2 10 C24.6 9.8 28.6 11.8 30.5 16 C32.1 19.7 31.9 26.2 30.8 33.5 Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<circle cx="17.2" cy="15.4" r="1.35" fill="{eye}"/>'
        )
    elif kind == "B":
        inner = (
            f'<circle cx="22.5" cy="8.2" r="2.6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<path d="M22.5 11.2 C16.5 14.2 13.8 19.5 15.5 25.5 C16.3 28.2 17.5 29.8 17.5 31.5 '
            f'H27.5 C27.5 29.8 28.7 28.2 29.5 25.5 C31.2 19.5 28.5 14.2 22.5 11.2 Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<path d="M19.5 18.5 L25.5 24.5 M25.5 18.5 L19.5 24.5" stroke="{accent}" stroke-width="1.2" stroke-linecap="round" opacity="0.8"/>'
            f'<rect x="13.5" y="31.5" width="18" height="3.2" rx="1.2" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<rect x="11" y="34.8" width="23" height="3.6" rx="1.5" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
    elif kind == "Q":
        inner = (
            f'<circle cx="8.5" cy="12" r="2.2" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            f'<circle cx="15" cy="8.5" r="2.2" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            f'<circle cx="22.5" cy="7" r="2.4" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            f'<circle cx="30" cy="8.5" r="2.2" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            f'<circle cx="36.5" cy="12" r="2.2" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            f'<path d="M9.5 14.8 L13.5 30 H31.5 L35.5 14.8 L28.8 22.8 L22.5 11.2 L16.2 22.8 Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<rect x="13" y="30.2" width="19" height="3.4" rx="1.2" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<rect x="10.5" y="34.2" width="24" height="4" rx="1.5" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
    else:  # K
        inner = (
            f'<path d="M22.5 5.2 V12.5 M18.8 8.2 H26.2" stroke="{stroke if not is_white else "#F5D98B"}" stroke-width="2.3" stroke-linecap="round"/>'
            f'<path d="M22.5 12.2 C17.5 12.2 12.8 15.8 12.8 21.8 C12.8 25.4 14.8 28 16.4 30 '
            f'H28.6 C30.2 28 32.2 25.4 32.2 21.8 C32.2 15.8 27.5 12.2 22.5 12.2 Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<path d="M22.5 13.5 V29.2" stroke="{accent}" stroke-width="1.1" opacity="0.65"/>'
            f'<rect x="13.2" y="30.2" width="18.6" height="3.5" rx="1.2" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<rect x="10.8" y="34.2" width="23.4" height="4" rx="1.5" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    return f'  <g transform="translate({tx:.1f}, {ty:.1f})" filter="url(#ps)">{inner}</g>'


def parse_fen_board(fen: str):
    """Parse FEN piece placement into an 8x8 list of strings (empty string or piece char)."""
    placement = fen.split()[0]
    rows = placement.split("/")
    grid = []
    for row in rows:
        cells = []
        for ch in row:
            if ch.isdigit():
                cells.extend([""] * int(ch))
            else:
                cells.append(ch)
        grid.append(cells)
    return grid


def square_to_xy(sq: str):
    col = FILES.index(sq[0])
    row = RANKS.index(sq[1])
    return 20 + col * 60, 62 + row * 60


def render_board_svg(
    fen: str,
    last_move: str | None = None,
    last_san: str | None = None,
    check_sq: str | None = None,
    status_text: str = "Yeni Oyun",
    turn_white: bool = True,
    game_number: int = 1,
) -> str:
    grid = parse_fen_board(fen)
    turn_label = "Sıra: Beyaz" if turn_white else "Sıra: Siyah"
    turn_dot = "#F0C85A" if turn_white else "#B8C2D4"
    last_label = f"Son: {last_san}" if last_san else f"Oyun #{game_number}"

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="564" viewBox="0 0 520 564" role="img" aria-label="İnteraktif Satranç Tahtası">',
        "  <defs>",
        '    <linearGradient id="frameBg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#0A0D13"/>',
        '      <stop offset="100%" stop-color="#121722"/>',
        "    </linearGradient>",
        '    <linearGradient id="wGold" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#FFF4CC"/>',
        '      <stop offset="42%" stop-color="#E5C158"/>',
        '      <stop offset="80%" stop-color="#C49526"/>',
        '      <stop offset="100%" stop-color="#8A6512"/>',
        "    </linearGradient>",
        '    <radialGradient id="checkGlow" cx="50%" cy="50%" r="55%">',
        '      <stop offset="0%" stop-color="#E04848" stop-opacity="0.7"/>',
        '      <stop offset="100%" stop-color="#991B1B" stop-opacity="0"/>',
        "    </radialGradient>",
        '    <filter id="ps" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feDropShadow dx="0" dy="1.8" stdDeviation="1.8" flood-color="#000000" flood-opacity="0.72"/>',
        "    </filter>",
        "    <style>",
        "      .hud { font-family: 'SFMono-Regular', Consolas, Menlo, monospace; font-size: 11.5px; font-weight: 600; fill: #E6DFD0; }",
        "      .hud-gold { font-family: 'SFMono-Regular', Consolas, Menlo, monospace; font-size: 11.5px; font-weight: 700; fill: #E8C563; }",
        "      .hud-muted { font-family: 'SFMono-Regular', Consolas, Menlo, monospace; font-size: 11px; fill: #98A3B8; }",
        "      .coord-l { font-family: 'SFMono-Regular', Consolas, Menlo, monospace; font-size: 10px; font-weight: 700; fill: #697489; }",
        "      .coord-d { font-family: 'SFMono-Regular', Consolas, Menlo, monospace; font-size: 10px; font-weight: 700; fill: #8490A6; }",
        "    </style>",
        "  </defs>",
        "",
        '  <!-- Outer Frame -->',
        '  <rect x="1" y="1" width="518" height="562" rx="14" fill="url(#frameBg)" stroke="#D4AF37" stroke-opacity="0.38" stroke-width="1.2"/>',
        "",
        '  <!-- Top HUD Bar -->',
        f'  <circle cx="28" cy="31" r="5" fill="{turn_dot}"/>',
        f'  <text x="41" y="35" class="hud">{turn_label}</text>',
        f'  <text x="260" y="35" text-anchor="middle" class="hud-gold">{status_text}</text>',
        f'  <text x="498" y="35" text-anchor="end" class="hud-muted">{last_label}</text>',
        '  <line x1="20" y1="52" x2="500" y2="52" stroke="#D4AF37" stroke-opacity="0.2" stroke-width="1"/>',
        "",
        '  <!-- 8x8 Chessboard Squares -->',
    ]

    last_from = last_move[:2] if last_move and len(last_move) >= 4 else None
    last_to = last_move[2:4] if last_move and len(last_move) >= 4 else None

    for r in range(8):
        for c in range(8):
            sq = f"{FILES[c]}{RANKS[r]}"
            x = 20 + c * 60
            y = 62 + r * 60
            is_light = (r + c) % 2 == 0
            bg = "#252E3E" if is_light else "#121620"
            parts.append(f'  <rect x="{x}" y="{y}" width="60" height="60" fill="{bg}"/>')

            if sq == last_from or sq == last_to:
                op = "0.28" if sq == last_to else "0.17"
                parts.append(f'  <rect x="{x}" y="{y}" width="60" height="60" fill="#D4AF37" fill-opacity="{op}"/>')
                if sq == last_to:
                    parts.append(f'  <rect x="{x+1}" y="{y+1}" width="58" height="58" fill="none" stroke="#E8C563" stroke-opacity="0.7" stroke-width="1.2"/>')

            if sq == check_sq:
                parts.append(f'  <rect x="{x}" y="{y}" width="60" height="60" fill="url(#checkGlow)"/>')

            # Rank label on 'a' file
            if c == 0:
                cls = "coord-l" if is_light else "coord-d"
                parts.append(f'  <text x="{x+4}" y="{y+13}" class="{cls}">{RANKS[r]}</text>')
            # File label on rank '1'
            if r == 7:
                cls = "coord-l" if is_light else "coord-d"
                parts.append(f'  <text x="{x+51}" y="{y+55}" class="{cls}">{FILES[c]}</text>')

    # Board inner border
    parts.append('  <rect x="20" y="62" width="480" height="480" fill="none" stroke="#D4AF37" stroke-opacity="0.45" stroke-width="1.2"/>')
    parts.append("")
    parts.append("  <!-- Chess Pieces -->")

    for r in range(8):
        for c in range(8):
            p = grid[r][c]
            if p:
                x = 20 + c * 60
                y = 62 + r * 60
                parts.append(piece_svg_markup(p, x, y))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def make_issue_url(title: str, body: str) -> str:
    params = urllib.parse.urlencode({"title": title, "body": body})
    return f"https://github.com/{REPO}/issues/new?{params}"


def build_moves_markdown(
    state: dict,
    grouped_moves: list[tuple[str, str, list[tuple[str, str]]]],
    game_over_msg: str | None = None,
    turn_white: bool = True,
) -> str:
    """
    Build clean, compact Markdown for the interactive chess section.
    grouped_moves: list of (piece_char, from_sq, [(label, uci), ...])
    """
    v = f"{state['game_number']}-{state['total_moves']}"
    new_game_url = make_issue_url(
        "chess|new",
        "Yeni bir satranç oyunu başlatmak için sadece **Create** butonuna tıkla! ♟️",
    )

    lines = [
        '<div align="center">',
        "",
        f'<img src="./assets/chessboard.svg?v={v}" alt="İnteraktif Satranç Tahtası" width="460" />',
        "",
    ]

    if state.get("last_san") and state.get("last_player"):
        lines.append(
            f'<sub>Son hamle: <b>{state["last_san"]}</b> (@{state["last_player"]}) · '
            f'<a href="{new_game_url}">↻ Yeni Oyun</a></sub>'
        )
    else:
        lines.append(
            f'<sub>Oyun #{state["game_number"]} · İlk hamleyi yapmak için aşağıdan bir kare seç · '
            f'<a href="{new_game_url}">↻ Sıfırla</a></sub>'
        )

    lines.append("")

    if game_over_msg:
        lines.append(f"**{game_over_msg}**")
        lines.append("")
        lines.append(f"👉 [**Yeni Oyun Başlat**]({new_game_url})")
    else:
        side = "Beyaz" if turn_white else "Siyah"
        lines.append(f"<sub><b>Sıra {side}'da</b> — Hamleye tıkla, açılan Issue'da <b>Create</b> butonuna bas:</sub>")
        lines.append("")

        # Compact, clean rows: 4 origin squares per line
        chunks = [grouped_moves[i : i + 4] for i in range(0, len(grouped_moves), 4)]
        for chunk in chunks:
            row_items = []
            for piece_ch, from_sq, targets in chunk:
                icon = PIECE_ICONS.get(piece_ch, "")
                links = []
                for label, uci in targets:
                    url = make_issue_url(
                        f"chess|move|{uci}",
                        f"Hamlem: **{from_sq} → {label}** (`{uci}`)\n\nBu Issue'yu gönderdikten birkaç saniye sonra profildeki tahta otomatik güncellenir! ♟️",
                    )
                    links.append(f"[{label}]({url})")
                row_items.append(f"{icon} `{from_sq}`: " + " ".join(links))
            lines.append(" &nbsp;·&nbsp; ".join(row_items) + "<br/>")

    # Collapsible move history
    moves = state.get("moves", [])
    if moves:
        lines.append("")
        lines.append("<details>")
        lines.append(f"<summary>📜 Hamle Geçmişi ({len(moves)} hamle)</summary>")
        lines.append("")
        pairs = []
        for i in range(0, len(moves), 2):
            m_num = i // 2 + 1
            w = moves[i]
            w_str = f"{w['san']} (@{w['player']})"
            if i + 1 < len(moves):
                b = moves[i + 1]
                b_str = f"{b['san']} (@{b['player']})"
                pairs.append(f"`{m_num}.` {w_str} · {b_str}")
            else:
                pairs.append(f"`{m_num}.` {w_str}")
        lines.append("  \n".join(pairs[-10:]))
        lines.append("")
        lines.append("</details>")

    lines.append("")
    lines.append("</div>")
    return "\n".join(lines)


def update_readme(chess_block: str):
    content = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(r"<!-- CHESS_START -->.*?<!-- CHESS_END -->", re.DOTALL)
    replacement = f"<!-- CHESS_START -->\n{chess_block}\n<!-- CHESS_END -->"
    if not pattern.search(content):
        raise RuntimeError("README.md is missing CHESS_START / CHESS_END markers.")
    updated = pattern.sub(replacement, content, count=1)
    README_PATH.write_text(updated, encoding="utf-8")


def starting_grouped_moves():
    """Exact 20 legal moves from starting position (used for --init without python-chess)."""
    res = [
        ("N", "b1", [("a3", "b1a3"), ("c3", "b1c3")]),
        ("N", "g1", [("f3", "g1f3"), ("h3", "g1h3")]),
    ]
    for f in FILES:
        res.append(("P", f"{f}2", [(f"{f}3", f"{f}2{f}3"), (f"{f}4", f"{f}2{f}4")]))
    return res


def grouped_moves_from_board(board):
    import chess

    by_from: dict[str, tuple[str, list[tuple[str, str]]]] = {}
    for move in board.legal_moves:
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)
        piece = board.piece_at(move.from_square)
        p_char = piece.symbol() if piece else "P"

        # Auto-promote to queen to keep clickable move list clean
        if move.promotion and move.promotion != chess.QUEEN:
            continue

        label = f"{to_sq}=Q" if move.promotion == chess.QUEEN else to_sq
        uci = move.uci()
        if from_sq not in by_from:
            by_from[from_sq] = (p_char, [])
        by_from[from_sq][1].append((label, uci))

    ordered = []
    for from_sq, (p_char, targets) in by_from.items():
        targets.sort(key=lambda t: t[0])
        ordered.append((p_char, from_sq, targets))

    ordered.sort(key=lambda item: (PIECE_ORDER.get(item[0].upper(), 9), item[1]))
    return ordered


def sync_from_chess_board(board, state: dict):
    import chess

    check_sq = None
    if board.is_check():
        king_sq = board.king(board.turn)
        if king_sq is not None:
            check_sq = chess.square_name(king_sq)

    game_over_msg = None
    if board.is_checkmate():
        winner = "Beyaz" if board.turn == chess.BLACK else "Siyah"
        status_text = "ŞAH MAT!"
        game_over_msg = f"🏆 Şah Mat! Kazanan: {winner}"
    elif board.is_stalemate():
        status_text = "PAT (Berabere)"
        game_over_msg = "🤝 Pat! Oyun berabere bitti."
    elif board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        status_text = "Berabere"
        game_over_msg = "🤝 Oyun berabere bitti."
    elif board.is_check():
        status_text = f"ŞAH! · Hamle #{state['total_moves']}"
    elif state["total_moves"] == 0:
        status_text = "Yeni Oyun"
    else:
        status_text = f"Hamle #{state['total_moves']}"

    svg = render_board_svg(
        fen=board.fen(),
        last_move=state.get("last_move"),
        last_san=state.get("last_san"),
        check_sq=check_sq,
        status_text=status_text,
        turn_white=(board.turn == chess.WHITE),
        game_number=state["game_number"],
    )
    BOARD_SVG_PATH.write_text(svg, encoding="utf-8")

    grouped = [] if game_over_msg else grouped_moves_from_board(board)
    md = build_moves_markdown(
        state=state,
        grouped_moves=grouped,
        game_over_msg=game_over_msg,
        turn_white=(board.turn == chess.WHITE),
    )
    update_readme(md)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return game_over_msg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--move", type=str)
    parser.add_argument("--new", action="store_true")
    parser.add_argument("--issue-title", type=str)
    parser.add_argument("--output-file", type=str)
    parser.add_argument("--player", type=str, default="oyuncu")
    args = parser.parse_args()

    def finish(payload: dict):
        text = json.dumps(payload, ensure_ascii=False)
        if args.output_file:
            Path(args.output_file).write_text(text + "\n", encoding="utf-8")
        print(text)

    if args.issue_title is not None:
        parts = args.issue_title.strip().split("|")
        if len(parts) >= 2 and parts[1] == "new":
            args.new = True
        elif len(parts) >= 3 and parts[1] == "move":
            args.move = parts[2]
        else:
            finish({"ok": False, "message": "Bilinmeyen satranç komutu."})
            return

    if args.init:
        state = {
            "fen": START_FEN,
            "last_move": None,
            "last_san": None,
            "last_player": None,
            "moves": [],
            "game_number": 1,
            "total_moves": 0,
        }
        svg = render_board_svg(
            fen=START_FEN,
            status_text="Yeni Oyun",
            turn_white=True,
            game_number=1,
        )
        BOARD_SVG_PATH.write_text(svg, encoding="utf-8")
        md = build_moves_markdown(state, starting_grouped_moves(), turn_white=True)
        update_readme(md)
        STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        finish({"ok": True, "message": "Başlangıç tahtası oluşturuldu."})
        return

    import chess

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))

    if args.new:
        state = {
            "fen": START_FEN,
            "last_move": None,
            "last_san": None,
            "last_player": None,
            "moves": [],
            "game_number": state.get("game_number", 1) + 1,
            "total_moves": 0,
        }
        board = chess.Board()
        sync_from_chess_board(board, state)
        finish({
            "ok": True,
            "message": f"♟️ Yeni oyun (#{state['game_number']}) başlatıldı! Teşekkürler @{args.player}.",
        })
        return

    if args.move:
        board = chess.Board(state["fen"])
        if board.is_game_over():
            finish({
                "ok": False,
                "message": "Bu oyun zaten bitti. Profildeki **Yeni Oyun** bağlantısıyla yeni bir maç başlatabilirsin!",
            })
            return

        raw_uci = args.move.strip().lower()
        try:
            move = chess.Move.from_uci(raw_uci)
        except ValueError:
            finish({
                "ok": False,
                "message": f"Geçersiz hamle formatı: `{raw_uci}`.",
            })
            return

        # Auto-promote pawn to queen if promotion char omitted
        if move not in board.legal_moves and len(raw_uci) == 4:
            q_move = chess.Move.from_uci(raw_uci + "q")
            if q_move in board.legal_moves:
                move = q_move

        if move not in board.legal_moves:
            finish({
                "ok": False,
                "message": f"`{raw_uci}` şu anki pozisyonda geçerli bir hamle değil (başka biri az önce hamle yapmış olabilir).",
            })
            return

        san = board.san(move)
        board.push(move)

        state["fen"] = board.fen()
        state["last_move"] = move.uci()
        state["last_san"] = san
        state["last_player"] = args.player
        state["total_moves"] = state.get("total_moves", 0) + 1
        state.setdefault("moves", []).append({"san": san, "uci": move.uci(), "player": args.player})

        game_over_msg = sync_from_chess_board(board, state)
        msg = f"✅ Hamle oynandı: **{san}** (`{move.uci()}`) — Teşekkürler @{args.player}!"
        if game_over_msg:
            msg += f"\n\n{game_over_msg}"
        finish({"ok": True, "message": msg})


if __name__ == "__main__":
    main()
