# checkers_strategy.py
# AI strategy and board manipulation for Game Pigeon Checkers
# Follows the patterns of existing solvers in this repo

import math
import random
from checkers.checkers_player import CheckersPlayer

# Constants
EMPTY = '.'
RED = 'r'      # Bottom side (usually human)
BLACK = 'b'    # Top side (usually AI)
RED_KING = 'R'
BLACK_KING = 'B'

NUM_ROWS = 8
NUM_COLS = 8
WIN_SCORE = 1000000
MAX_DEPTH = 6

class CheckersStrategy(CheckersPlayer):
    def __init__(self, color):
        super().__init__(color)
        self.AI_COLOR = color
        self.HUMAN_COLOR = opponent_of(color)

    def get_move(self, board):
        """Calculates the best move for the AI for the given board"""
        best_move = None
        # Iterative deepening for better pruning and time management
        # We start from 1 to MAX_DEPTH to ensure we have a valid move if time/memory is an issue
        try:
            for i in range(1, MAX_DEPTH + 1):
                move, score = self.minimax(board, 0, True, -math.inf, math.inf, i)
                if move:
                    best_move = move
                if score >= WIN_SCORE or score <= -WIN_SCORE:
                    break
        except MemoryError:
            # Fallback if memory spikes occur (though less likely with optimized pruning)
            pass
            
        return best_move

    def minimax(self, board, depth, is_max, alpha, beta, local_max_depth):
        valid_moves = get_valid_moves(board, self.AI_COLOR if is_max else self.HUMAN_COLOR)
        
        if not valid_moves:
            # If no moves, current player loses (or it's a draw, but usually loss in checkers)
            return None, -WIN_SCORE if is_max else WIN_SCORE
            
        if depth == local_max_depth:
            return None, score_board(board, self.AI_COLOR)

        random.shuffle(valid_moves)
        best_move = valid_moves[0]

        if is_max:
            score = -math.inf
            for move in valid_moves:
                new_board = perform_move(copy_of_board(board), move)
                _, updated_score = self.minimax(new_board, depth + 1, False, alpha, beta, local_max_depth)
                if updated_score > score:
                    score = updated_score
                    best_move = move
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
            return best_move, score
        else:
            score = math.inf
            for move in valid_moves:
                new_board = perform_move(copy_of_board(board), move)
                _, updated_score = self.minimax(new_board, depth + 1, True, alpha, beta, local_max_depth)
                if updated_score < score:
                    score = updated_score
                    best_move = move
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return best_move, score

def get_valid_moves(board, color):
    """Returns a list of valid moves. Jumps are mandatory if available."""
    jumps = []
    moves = []
    
    for r in range(NUM_ROWS):
        for c in range(NUM_COLS):
            piece = board[r][c]
            if piece.lower() == color.lower():
                piece_jumps = get_jumps(board, r, c)
                if piece_jumps:
                    jumps.extend(piece_jumps)
                
                # We only need to check simple moves if no jumps have been found globally
                if not jumps:
                    moves.extend(get_simple_moves(board, r, c))
                    
    return jumps if jumps else moves

def get_simple_moves(board, r, c):
    moves = []
    piece = board[r][c]
    directions = []
    
    if piece == RED: directions = [(-1, -1), (-1, 1)]
    elif piece == BLACK: directions = [(1, -1), (1, 1)]
    elif piece.upper() == piece: directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < NUM_ROWS and 0 <= nc < NUM_COLS and board[nr][nc] == EMPTY:
            moves.append([(r, c), (nr, nc)])
    return moves

def get_jumps(board, r, c, current_path=None):
    """Recursively finds all possible jump sequences (multi-jumps)"""
    if current_path is None:
        current_path = [(r, c)]
    
    jumps = []
    piece = board[r][c]
    directions = []
    
    if piece == RED: directions = [(-1, -1), (-1, 1)]
    elif piece == BLACK: directions = [(1, -1), (1, 1)]
    else: directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    found_jump = False
    for dr, dc in directions:
        mid_r, mid_c = r + dr, c + dc
        end_r, end_c = r + 2*dr, c + 2*dc
        
        if 0 <= end_r < NUM_ROWS and 0 <= end_c < NUM_COLS:
            mid_piece = board[mid_r][mid_c]
            if mid_piece != EMPTY and mid_piece.lower() != piece.lower() and board[end_r][end_c] == EMPTY:
                # Potential jump
                found_jump = True
                temp_board = copy_of_board(board)
                # Remove jumped piece
                temp_board[mid_r][mid_c] = EMPTY
                temp_board[end_r][end_c] = piece
                temp_board[r][c] = EMPTY
                
                # Check for multi-jumps
                extended_jumps = get_jumps(temp_board, end_r, end_c, current_path + [(end_r, end_c)])
                jumps.extend(extended_jumps)
                
    if not found_jump and len(current_path) > 1:
        return [current_path]
    return jumps

def perform_move(board, move_path):
    """Executes a move path on the board, handling jumps and kinging"""
    start_r, start_c = move_path[0]
    piece = board[start_r][start_c]
    
    curr_r, curr_c = start_r, start_c
    for i in range(1, len(move_path)):
        next_r, next_c = move_path[i]
        # Check if it was a jump
        if abs(next_r - curr_r) == 2:
            mid_r = (curr_r + next_r) // 2
            mid_c = (curr_c + next_c) // 2
            board[mid_r][mid_c] = EMPTY
            
        board[next_r][next_c] = piece
        board[curr_r][curr_c] = EMPTY
        curr_r, curr_c = next_r, next_c
        
    # Kinging
    if piece == RED and curr_r == 0: board[curr_r][curr_c] = RED_KING
    elif piece == BLACK and curr_r == NUM_ROWS - 1: board[curr_r][curr_c] = BLACK_KING
    
    return board

def score_board(board, color):
    score = 0
    for r in range(NUM_ROWS):
        for c in range(NUM_COLS):
            piece = board[r][c]
            if piece == EMPTY: continue
            
            val = 0
            # Piece values: King = 1.5x regular
            if piece.lower() == RED: val = 10 if piece == RED else 15
            else: val = -10 if piece == BLACK else -15
            
            # Positional bonuses
            if piece.lower() == RED:
                # Advancing is good
                val += (7 - r) * 0.1
                # Side protection
                if c == 0 or c == 7: val += 1
            elif piece.lower() == BLACK:
                # Advancing is good
                val -= r * 0.1
                # Side protection
                if c == 0 or c == 7: val -= 1
            
            score += val
            
    return score if color == RED else -score

def opponent_of(color):
    return BLACK if color == RED else RED

def copy_of_board(board):
    return [row[:] for row in board]
