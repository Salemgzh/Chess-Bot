"""
chess_bot.py — ~1000 ELO Chess Bot
====================================
A playable chess game against an AI bot calibrated to ~1000 ELO.

HOW TO RUN:
    pip install pygame
    python chess_bot.py

Controls:
    - Click a piece to select it (highlighted in yellow)
    - Click a destination square to move
    - Press R to restart
    - Press Q to quit
"""

import pygame
import sys
import random
import time
from copy import deepcopy

# ── Constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 640, 680
SQ = 80          # square size
BOARD_TOP = 40   # offset for top bar

# Colours
LIGHT   = (240, 217, 181)
DARK    = (181, 136,  99)
SEL     = (255, 255,   0, 160)
LAST_MV = ( 20, 85,   30, 128)
CHECK   = (220,  50,  50)
BG      = ( 30,  30,  30)
TEXT_C  = (230, 230, 230)

# Piece codes:  uppercase = White, lowercase = Black
# P/p=pawn  N/n=knight  B/b=bishop  R/r=rook  Q/q=queen  K/k=king

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
                'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}

# Piece-square tables (from White's perspective, will be flipped for Black)
PST = {
    'P': [  0,  0,  0,  0,  0,  0,  0,  0,
           50, 50, 50, 50, 50, 50, 50, 50,
           10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0],
    'N': [-50,-40,-30,-30,-30,-30,-40,-50,
          -40,-20,  0,  0,  0,  0,-20,-40,
          -30,  0, 10, 15, 15, 10,  0,-30,
          -30,  5, 15, 20, 20, 15,  5,-30,
          -30,  0, 15, 20, 20, 15,  0,-30,
          -30,  5, 10, 15, 15, 10,  5,-30,
          -40,-20,  0,  5,  5,  0,-20,-40,
          -50,-40,-30,-30,-30,-30,-40,-50],
    'B': [-20,-10,-10,-10,-10,-10,-10,-20,
          -10,  0,  0,  0,  0,  0,  0,-10,
          -10,  0,  5, 10, 10,  5,  0,-10,
          -10,  5,  5, 10, 10,  5,  5,-10,
          -10,  0, 10, 10, 10, 10,  0,-10,
          -10, 10, 10, 10, 10, 10, 10,-10,
          -10,  5,  0,  0,  0,  0,  5,-10,
          -20,-10,-10,-10,-10,-10,-10,-20],
    'R': [  0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, 10, 10, 10, 10,  5,
           -5,  0,  0,  0,  0,  0,  0, -5,
           -5,  0,  0,  0,  0,  0,  0, -5,
           -5,  0,  0,  0,  0,  0,  0, -5,
           -5,  0,  0,  0,  0,  0,  0, -5,
           -5,  0,  0,  0,  0,  0,  0, -5,
            0,  0,  0,  5,  5,  0,  0,  0],
    'Q': [-20,-10,-10, -5, -5,-10,-10,-20,
          -10,  0,  0,  0,  0,  0,  0,-10,
          -10,  0,  5,  5,  5,  5,  0,-10,
           -5,  0,  5,  5,  5,  5,  0, -5,
            0,  0,  5,  5,  5,  5,  0, -5,
          -10,  5,  5,  5,  5,  5,  0,-10,
          -10,  0,  5,  0,  0,  0,  0,-10,
          -20,-10,-10, -5, -5,-10,-10,-20],
    'K': [-30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30,
          -20,-30,-30,-40,-40,-30,-30,-20,
          -10,-20,-20,-20,-20,-20,-20,-10,
           20, 20,  0,  0,  0,  0, 20, 20,
           20, 30, 10,  0,  0, 10, 30, 20],
}


# ── Board Representation ─────────────────────────────────────────────────────

INIT_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

def fen_to_board(fen=INIT_FEN):
    parts = fen.split()
    rows = parts[0].split('/')
    board = []
    for row in rows:
        for ch in row:
            if ch.isdigit():
                board.extend(['.'] * int(ch))
            else:
                board.append(ch)
    turn = parts[1]
    castling = parts[2]
    ep = parts[3]
    return board, turn, castling, ep

def is_white(p): return p.isupper() and p != '.'
def is_black(p): return p.islower()
def is_enemy(p, turn): return (is_black(p) if turn == 'w' else is_white(p))
def is_friend(p, turn): return (is_white(p) if turn == 'w' else is_black(p))
def rc(sq): return sq // 8, sq % 8

def generate_moves(board, turn, castling, ep_sq):
    """Generate all pseudo-legal moves as (from, to, promo) tuples."""
    moves = []
    ep_idx = None
    if ep_sq != '-':
        col = ord(ep_sq[0]) - ord('a')
        row = 8 - int(ep_sq[1])
        ep_idx = row * 8 + col

    for sq, piece in enumerate(board):
        if piece == '.': continue
        if turn == 'w' and not is_white(piece): continue
        if turn == 'b' and not is_black(piece): continue
        r, c = rc(sq)
        pt = piece.upper()

        if pt == 'P':
            direction = -1 if turn == 'w' else 1
            start_row = 6 if turn == 'w' else 1
            promo_row = 0 if turn == 'w' else 7
            promos = ['Q', 'R', 'B', 'N'] if (r + direction) == promo_row else [None]
            # Forward
            fwd = sq + direction * 8
            if 0 <= fwd < 64 and board[fwd] == '.':
                for p in promos:
                    moves.append((sq, fwd, p if turn == 'w' else (p.lower() if p else None)))
                if r == start_row:
                    fwd2 = sq + direction * 16
                    if board[fwd2] == '.':
                        moves.append((sq, fwd2, None))
            # Captures
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nc < 8:
                    dst = sq + direction * 8 + dc
                    if 0 <= dst < 64 and is_enemy(board[dst], turn):
                        for p in promos:
                            moves.append((sq, dst, p if turn == 'w' else (p.lower() if p else None)))
                    if dst == ep_idx:
                        moves.append((sq, dst, None))

        elif pt == 'N':
            for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nr, nc2 = r+dr, c+dc
                if 0 <= nr < 8 and 0 <= nc2 < 8:
                    dst = nr*8+nc2
                    if not is_friend(board[dst], turn):
                        moves.append((sq, dst, None))

        elif pt in ('B', 'R', 'Q'):
            dirs = []
            if pt in ('B', 'Q'): dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
            if pt in ('R', 'Q'): dirs += [(-1,0),(1,0),(0,-1),(0,1)]
            for dr, dc in dirs:
                nr, nc2 = r+dr, c+dc
                while 0 <= nr < 8 and 0 <= nc2 < 8:
                    dst = nr*8+nc2
                    if is_friend(board[dst], turn): break
                    moves.append((sq, dst, None))
                    if is_enemy(board[dst], turn): break
                    nr += dr; nc2 += dc

        elif pt == 'K':
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                nr, nc2 = r+dr, c+dc
                if 0 <= nr < 8 and 0 <= nc2 < 8:
                    dst = nr*8+nc2
                    if not is_friend(board[dst], turn):
                        moves.append((sq, dst, None))
            # Castling
            if turn == 'w' and r == 7 and c == 4:
                if 'K' in castling and board[63]=='R' and board[61]=='.' and board[62]=='.':
                    moves.append((sq, 62, None))
                if 'Q' in castling and board[56]=='R' and board[57]=='.' and board[58]=='.' and board[59]=='.':
                    moves.append((sq, 58, None))
            if turn == 'b' and r == 0 and c == 4:
                if 'k' in castling and board[7]=='r' and board[5]=='.' and board[6]=='.':
                    moves.append((sq, 6, None))
                if 'q' in castling and board[0]=='r' and board[1]=='.' and board[2]=='.' and board[3]=='.':
                    moves.append((sq, 2, None))
    return moves

def apply_move(board, turn, castling, ep_sq, move):
    frm, to, promo = move
    b = board[:]
    piece = b[frm]
    pt = piece.upper()
    new_castling = castling
    new_ep = '-'

    # En passant capture
    ep_idx = None
    if ep_sq != '-':
        col = ord(ep_sq[0]) - ord('a')
        row = 8 - int(ep_sq[1])
        ep_idx = row * 8 + col
    if pt == 'P' and to == ep_idx:
        cap_sq = to + (8 if turn == 'w' else -8)
        b[cap_sq] = '.'

    # Castling move rook
    if pt == 'K':
        fr, fc = rc(frm); tr, tc = rc(to)
        if abs(tc - fc) == 2:
            if tc == 6:  # kingside
                b[fr*8+5] = b[fr*8+7]; b[fr*8+7] = '.'
            else:        # queenside
                b[fr*8+3] = b[fr*8+0]; b[fr*8+0] = '.'
        new_castling = new_castling.replace('K' if turn=='w' else 'k', '')
        new_castling = new_castling.replace('Q' if turn=='w' else 'q', '')
    if pt == 'R':
        if frm == 63: new_castling = new_castling.replace('K','')
        if frm == 56: new_castling = new_castling.replace('Q','')
        if frm == 7:  new_castling = new_castling.replace('k','')
        if frm == 0:  new_castling = new_castling.replace('q','')
    if not new_castling: new_castling = '-'

    # Pawn double push → set ep
    if pt == 'P' and abs(to - frm) == 16:
        ep_r = (frm + to) // 2
        er, ec = rc(ep_r)
        new_ep = chr(ord('a') + ec) + str(8 - er)

    b[to] = piece
    b[frm] = '.'
    if promo:
        b[to] = promo

    next_turn = 'b' if turn == 'w' else 'w'
    return b, next_turn, new_castling, new_ep

def king_sq(board, turn):
    target = 'K' if turn == 'w' else 'k'
    for i, p in enumerate(board):
        if p == target: return i
    return -1

def in_check(board, turn, castling, ep_sq):
    opp = 'b' if turn == 'w' else 'w'
    ksq = king_sq(board, turn)
    for move in generate_moves(board, opp, castling, ep_sq):
        if move[1] == ksq: return True
    return False

def legal_moves(board, turn, castling, ep_sq):
    result = []
    for mv in generate_moves(board, turn, castling, ep_sq):
        b2, t2, c2, e2 = apply_move(board, turn, castling, ep_sq, mv)
        if not in_check(b2, turn, c2, e2):
            result.append(mv)
    return result


# ── Evaluation ───────────────────────────────────────────────────────────────

def evaluate(board):
    score = 0
    for sq, piece in enumerate(board):
        if piece == '.': continue
        pt = piece.upper()
        val = PIECE_VALUES[pt]
        r, c = rc(sq)
        pst_idx = r * 8 + c if piece.isupper() else (7 - r) * 8 + c
        pst_val = PST.get(pt, [0]*64)[pst_idx]
        if piece.isupper():
            score += val + pst_val
        else:
            score -= val + pst_val
    return score


# ── Bot (1000-ELO calibrated) ─────────────────────────────────────────────────
# ~1000 ELO characteristics:
#  - Shallow search (depth 2)
#  - Random blunders (~15% of moves picks a random legal move)
#  - No quiescence search
#  - Simple alpha-beta

BLUNDER_RATE = 0.15   # 15% random move
BOT_DEPTH    = 2

def minimax(board, turn, castling, ep_sq, depth, alpha, beta, maximising):
    moves = legal_moves(board, turn, castling, ep_sq)
    if not moves:
        if in_check(board, turn, castling, ep_sq):
            return -99999 if maximising else 99999
        return 0  # stalemate
    if depth == 0:
        return evaluate(board)

    if maximising:
        best = -float('inf')
        for mv in moves:
            b2, t2, c2, e2 = apply_move(board, turn, castling, ep_sq, mv)
            val = minimax(b2, t2, c2, e2, depth-1, alpha, beta, False)
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha: break
        return best
    else:
        best = float('inf')
        for mv in moves:
            b2, t2, c2, e2 = apply_move(board, turn, castling, ep_sq, mv)
            val = minimax(b2, t2, c2, e2, depth-1, alpha, beta, True)
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha: break
        return best

def bot_move(board, castling, ep_sq):
    """Bot plays as Black."""
    moves = legal_moves(board, 'b', castling, ep_sq)
    if not moves: return None

    # Blunder: just play a random move
    if random.random() < BLUNDER_RATE:
        return random.choice(moves)

    best_val = float('inf')
    best_moves = []
    for mv in moves:
        b2, t2, c2, e2 = apply_move(board, 'b', castling, ep_sq, mv)
        val = minimax(b2, t2, c2, e2, BOT_DEPTH - 1, -float('inf'), float('inf'), True)
        if val < best_val:
            best_val = val
            best_moves = [mv]
        elif val == best_val:
            best_moves.append(mv)

    # Add slight randomness among equally good moves
    return random.choice(best_moves)


# ── Pygame Rendering ──────────────────────────────────────────────────────────

PIECE_UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
}

def sq_to_pixel(sq):
    r, c = rc(sq)
    return c * SQ, BOARD_TOP + r * SQ

def pixel_to_sq(x, y):
    c = x // SQ
    r = (y - BOARD_TOP) // SQ
    if 0 <= r < 8 and 0 <= c < 8:
        return r * 8 + c
    return -1

def draw_board(surface, board, selected, legal_dsts, last_move, turn, castling, ep_sq, status):
    surface.fill(BG)

    # Top bar
    bar_text = f"  {'White' if turn == 'w' else 'Black'} to move"
    if status == 'checkmate':
        winner = 'Black' if turn == 'w' else 'White'
        bar_text = f"  ✓ Checkmate — {winner} wins!"
    elif status == 'stalemate':
        bar_text = "  Draw by stalemate"
    elif status == 'check':
        bar_text = f"  {'White' if turn=='w' else 'Black'} is in check!"
    elif status == 'thinking':
        bar_text = "  Bot is thinking…"

    font_sm = pygame.font.SysFont('Segoe UI', 18)
    lbl = font_sm.render(bar_text, True, TEXT_C)
    surface.blit(lbl, (0, 8))

    # Draw squares
    for sq in range(64):
        r, c = rc(sq)
        x, y = c * SQ, BOARD_TOP + r * SQ
        colour = LIGHT if (r + c) % 2 == 0 else DARK
        pygame.draw.rect(surface, colour, (x, y, SQ, SQ))

        # Last move highlight
        if last_move and sq in (last_move[0], last_move[1]):
            hl = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            hl.fill((20, 85, 30, 100))
            surface.blit(hl, (x, y))

        # Selected highlight
        if sq == selected:
            hl = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            hl.fill((255, 255, 0, 140))
            surface.blit(hl, (x, y))

        # Legal move dots
        if sq in legal_dsts:
            if board[sq] != '.':
                pygame.draw.rect(surface, (180, 0, 0), (x, y, SQ, SQ), 4)
            else:
                cx, cy = x + SQ//2, y + SQ//2
                pygame.draw.circle(surface, (50, 50, 50, 160), (cx, cy), 12)

    # King in check
    if status in ('check', 'checkmate'):
        ksq = king_sq(board, turn)
        kr, kc = rc(ksq)
        kx, ky = kc * SQ, BOARD_TOP + kr * SQ
        pygame.draw.rect(surface, CHECK, (kx, ky, SQ, SQ), 4)

    # Draw pieces
    font_piece = pygame.font.SysFont('Segoe UI Emoji', 52)
    for sq, piece in enumerate(board):
        if piece == '.': continue
        r, c = rc(sq)
        x, y = c * SQ, BOARD_TOP + r * SQ
        glyph = PIECE_UNICODE.get(piece, '?')
        color = (255, 255, 255) if piece.isupper() else (20, 20, 20)
        rendered = font_piece.render(glyph, True, color)
        # Shadow for white pieces
        if piece.isupper():
            shadow = font_piece.render(glyph, True, (80, 80, 80))
            surface.blit(shadow, (x + SQ//2 - rendered.get_width()//2 + 1,
                                  y + SQ//2 - rendered.get_height()//2 + 1))
        surface.blit(rendered, (x + SQ//2 - rendered.get_width()//2,
                                y + SQ//2 - rendered.get_height()//2))

    # Rank & file labels
    font_lbl = pygame.font.SysFont('Consolas', 12)
    for i in range(8):
        fl = font_lbl.render(chr(ord('a') + i), True, (150, 150, 150))
        surface.blit(fl, (i * SQ + SQ - 12, BOARD_TOP + 8 * SQ + 2))
        rk = font_lbl.render(str(8 - i), True, (150, 150, 150))
        surface.blit(rk, (2, BOARD_TOP + i * SQ + 2))

    # Bottom bar
    hint = font_sm.render("R = restart   Q = quit", True, (100, 100, 100))
    surface.blit(hint, (WIDTH - hint.get_width() - 6, BOARD_TOP + 8 * SQ + 4))

    pygame.display.flip()


# ── Main Loop ─────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess Bot — ~1000 ELO")
    clock = pygame.time.Clock()

    def new_game():
        b, t, cas, ep = fen_to_board()
        return b, t, cas, ep, None, None, [], 'normal'

    board, turn, castling, ep_sq, selected, last_move, legal_dsts, status = new_game()

    while True:
        # Determine status
        moves = legal_moves(board, turn, castling, ep_sq)
        if not moves:
            status = 'checkmate' if in_check(board, turn, castling, ep_sq) else 'stalemate'
        elif in_check(board, turn, castling, ep_sq):
            status = 'check'
        else:
            status = 'normal'

        draw_board(screen, board, selected, set(legal_dsts), last_move, turn, castling, ep_sq, status)

        # Bot's turn
        if turn == 'b' and status == 'normal':
            draw_board(screen, board, selected, set(), last_move, turn, castling, ep_sq, 'thinking')
            pygame.event.pump()
            time.sleep(0.3)  # brief pause so it feels natural
            mv = bot_move(board, castling, ep_sq)
            if mv:
                board, turn, castling, ep_sq = apply_move(board, turn, castling, ep_sq, mv)
                last_move = mv
            selected = None
            legal_dsts = []
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_r:
                    board, turn, castling, ep_sq, selected, last_move, legal_dsts, status = new_game()

            if event.type == pygame.MOUSEBUTTONDOWN and status not in ('checkmate', 'stalemate'):
                x, y = event.pos
                clicked = pixel_to_sq(x, y)
                if clicked == -1:
                    continue

                if selected is None:
                    # Select a piece
                    if turn == 'w' and is_white(board[clicked]):
                        selected = clicked
                        legal_dsts = [mv[1] for mv in moves if mv[0] == clicked]
                else:
                    # Try to move
                    matching = [mv for mv in moves if mv[0] == selected and mv[1] == clicked]
                    if matching:
                        mv = matching[0]
                        # Auto-promote to queen
                        board, turn, castling, ep_sq = apply_move(board, turn, castling, ep_sq, mv)
                        last_move = mv
                        selected = None
                        legal_dsts = []
                    elif turn == 'w' and is_white(board[clicked]):
                        selected = clicked
                        legal_dsts = [mv[1] for mv in moves if mv[0] == clicked]
                    else:
                        selected = None
                        legal_dsts = []

        clock.tick(60)

if __name__ == '__main__':
    main()
