import sys
import os

# Adjust path to find the checkers modules
sys.path.append(os.getcwd())

from checkers.checkers_strategy import CheckersStrategy, RED, BLACK, EMPTY, get_valid_moves, perform_move

def test_ai_move():
    # Setup a simple board with one possible move
    board = [[EMPTY for _ in range(8)] for _ in range(8)]
    board[5][2] = RED
    # Playable squares are (r+c)%2 == 1
    # (5,2) is 7 -> playable
    # Potential move to (4,1) (5) or (4,3) (7)
    
    player = CheckersStrategy(RED)
    move = player.get_move(board)
    print(f"AI Move found: {move}")
    assert move is not None
    assert len(move) == 2

def test_jumps():
    board = [[EMPTY for _ in range(8)] for _ in range(8)]
    board[5][2] = RED
    board[4][3] = BLACK
    # (5,2) -> (4,3) -> (3,4) is a jump
    
    moves = get_valid_moves(board, RED)
    print(f"Valid moves (should be jump): {moves}")
    assert len(moves) == 1
    assert len(moves[0]) == 2
    assert moves[0][1] == (3,4)

if __name__ == "__main__":
    try:
        test_ai_move()
        test_jumps()
        print("Tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
