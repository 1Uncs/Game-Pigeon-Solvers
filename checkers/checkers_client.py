# checkers_client.py
# Client interface for Game Pigeon Checkers Solver
# Kyle Gerner style implementation

import os
import sys
import time
from util.terminaloutput.colors import RED_COLOR, BLUE_COLOR, NO_COLOR, GREY_COLOR, color_text
from util.terminaloutput.erasing import erase_previous_lines
from util.terminaloutput.symbols import ERROR_SYMBOL, INFO_SYMBOL, error, info
from checkers.checkers_player import CheckersPlayer
from checkers.checkers_strategy import CheckersStrategy, opponent_of, perform_move, get_valid_moves, copy_of_board, RED, BLACK, EMPTY, RED_KING, BLACK_KING

BOARD_OUTPUT_HEIGHT = 11

# Helper to map coordinates (e.g., A1) to (row, col)
def coordinate_to_index(coord):
    if len(coord) < 2: return None
    col = ord(coord[0].lower()) - ord('a')
    try:
        row = 8 - int(coord[1:])
    except ValueError:
        return None
    if 0 <= row < 8 and 0 <= col < 8:
        return (row, col)
    return None

def index_to_coordinate(index):
    row, col = index
    return f"{chr(ord('a') + col).upper()}{8 - row}"

class HumanPlayer(CheckersPlayer):
    def __init__(self, color):
        super().__init__(color, is_ai=False)

    def get_move(self, board):
        """Takes in the user's input for a move (e.g., 'C3 B4' or 'C3 E5 G7')"""
        valid_moves = get_valid_moves(board, self.color)
        
        while True:
            move_input = input("Enter your move (e.g., 'C3 D4' or 'C3 E5 G7' for jumps):\t").strip().upper()
            erase_previous_lines(1)
            
            if move_input == 'Q':
                exit(0)
                
            parts = move_input.split()
            if len(parts) < 2:
                print(f"{ERROR_SYMBOL} Invalid format. Use 'START END'.")
                erase_previous_lines(1)
                continue
            
            path = [coordinate_to_index(p) for p in parts]
            if None in path:
                print(f"{ERROR_SYMBOL} Invalid coordinates.")
                erase_previous_lines(1)
                continue
            
            # Verify if this path is in valid_moves
            if path in valid_moves:
                return path
            else:
                # Check if it's a valid path but maybe missing a step in a multi-jump
                print(f"{ERROR_SYMBOL} That is not a valid move. Remember: jumps are mandatory!")
                erase_previous_lines(1)

def print_board(board, highlight_path=None):
    """Prints the checkers board with labels"""
    print("\n    A B C D E F G H")
    print("  +-----------------+")
    for r in range(8):
        print(f"{8-r} | ", end='')
        for c in range(8):
            piece = board[r][c]
            # Map pieces to 'Bead' symbols
            char = "O" if piece != EMPTY else "."
            if piece == RED_KING: char = "K"
            elif piece == BLACK_KING: char = "X"
            
            if piece.lower() == RED:
                display_char = color_text(char, RED_COLOR)
            elif piece.lower() == BLACK:
                display_char = color_text(char, BLUE_COLOR)
            elif piece == EMPTY:
                if (r + c) % 2 == 0:
                    display_char = GREY_COLOR + "." + NO_COLOR
                else:
                    display_char = " "
            
            # Highlight move path
            if highlight_path and (r, c) in highlight_path:
                # Use underlining or different color for highlight? Let's use simple highlight
                print(f"[{display_char}]", end='') # This might break alignment, let's keep it simple
            else:
                print(f"{display_char} ", end='')
        print(f"| {8-r}")
    print("  +-----------------+")
    print("    A B C D E F G H\n")

def run():
    print("\nWelcome to the Game Pigeon Checkers AI!")
    print("Note: This version uses Dark squares as playable, matching Game Pigeon.")
    
    # Setup initial board
    game_board = [[EMPTY for _ in range(8)] for _ in range(8)]
    for r in range(8):
        for c in range(8):
            # In Game Pigeon (based on latest screenshot), A8 (0,0) is a playable square.
            # (r + c) % 2 == 0 corresponds to the dark squares where pieces are placed.
            if (r + c) % 2 == 0: 
                if r < 3: game_board[r][c] = BLACK
                elif r > 4: game_board[r][c] = RED

    user_color_input = input("Would you like to be RED ('r') or BLACK ('b')? (Black goes first!):\t").strip().lower()
    erase_previous_lines(1)
    
    if user_color_input == 'r':
        user_color = RED
        ai_color = BLACK
    else:
        user_color = BLACK
        ai_color = RED

    players = {
        RED: HumanPlayer(RED) if user_color == RED else CheckersStrategy(RED),
        BLACK: HumanPlayer(BLACK) if user_color == BLACK else CheckersStrategy(BLACK)
    }

    turn = BLACK # Black starts in Game Pigeon
    print_board(game_board)
    
    game_over = False
    while not game_over:
        current_player = players[turn]
        if current_player.is_ai:
            input(f"AI ({turn})'s turn. Press enter to see its move...")
            erase_previous_lines(1)
            move = current_player.get_move(game_board)
        else:
            move = current_player.get_move(game_board)
        
        if not move:
            print(f"No moves available for {turn}. Game Over!")
            break
            
        perform_move(game_board, move)
        path_str = " -> ".join([index_to_coordinate(p) for p in move])
        
        erase_previous_lines(BOARD_OUTPUT_HEIGHT + 1)
        print_board(game_board)
        print(f"{turn.upper()} played: {path_str}\n")
        
        turn = opponent_of(turn)
        # Check game over (no moves for next player)
        if not get_valid_moves(game_board, turn):
            game_over = True
            winner = opponent_of(turn)
            print(f"Winner is {winner.upper()}!")

if __name__ == '__main__':
    run()
