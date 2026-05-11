from typing import List, Tuple

class CheckersPlayer:
    def __init__(self, color: str, is_ai: bool = True):
        """Sets the color for this player, and indicates whether it is an AI"""
        self.color = color
        self.is_ai = is_ai

    def get_move(self, board: List[List[str]]) -> List[Tuple[int, int]]:
        """Returns the chosen move for a given board, as a list of coordinates (the path)"""
        print("\n<!> Function 'get_move' has not been implemented.\n"+
              "The program has been terminated.\n" +
              "Please make sure that you have implemented 'get_move' from the Player super class.\n")
        exit(0)
        return []
