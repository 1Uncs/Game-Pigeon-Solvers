# Kyle Gerner
# Started 11.19.2022
# Mancala Capture, client facing
import os
import sys
import time
from datetime import datetime

# Add the root directory to sys.path to allow running this script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.terminaloutput.colors import RED_COLOR, GREEN_COLOR, NO_COLOR, color_text
from util.terminaloutput.symbols import ERROR_SYMBOL, INFO_SYMBOL, info
from util.terminaloutput.erasing import erase_previous_lines
from util.save.saving import path_to_save_file, allow_save
from util.aiduel.dueling import get_dueling_ai_class
from mancalacapture.mancala_player import MancalaPlayer
from mancalacapture.board_functions import get_index_of_opposite_hole, push_all_pebbles_to_bank, winning_player_bank_index, \
	is_board_terminal, perform_move
from mancalacapture.constants import POCKETS_PER_SIDE, BOARD_OUTPUT_HEIGHT, PLAYER1_BANK_INDEX, PLAYER2_BANK_INDEX, \
	SIDE_INDENT_STR, LEFT_SIDE_ARROW, RIGHT_SIDE_ARROW, BOARD_SIZE
from mancalacapture.mancala_cap_strategy import MancalaStrategy

USE_REVERSED_PRINT_LAYOUT = False
BOARD = []  # will be populated from user input at runtime
PLAYER1_ID = 1
PLAYER2_ID = 2
SAVE_FILENAME = path_to_save_file("mancala_cap_save.txt")
BOARD_HISTORY = []  # [highlightPocketIndex, playerId, board]


# class for the Human player
class HumanPlayer(MancalaPlayer):

	def __init__(self, bank_index=6):
		super().__init__(bank_index, is_ai=False)

	def get_move(self, board):
		"""Takes in the user's input and returns the index on the board for the selected move"""
		spot = input(f"It's your turn, which spot would you like to play? (1 - {POCKETS_PER_SIDE}):\t").strip().upper()
		erase_previous_lines(1)
		while True:
			if spot == 'Q':
				print("\nThanks for playing!\n")
				exit(0)
			elif spot == 'F':
				global USE_REVERSED_PRINT_LAYOUT
				USE_REVERSED_PRINT_LAYOUT = not USE_REVERSED_PRINT_LAYOUT
				erase_previous_lines(BOARD_OUTPUT_HEIGHT + 2)
				print_board(board)
				print("\n")
				spot = input(
					f"Board print layout changed. Which spot would you like to play? (1 - {POCKETS_PER_SIDE}):\t").strip().upper()
				erase_previous_lines(1)
			elif spot == 'S':
				save_game(board, PLAYER1_ID)
				spot = input("Enter a coordinates for a move, or press 'q' to quit:\t").strip().upper()
				erase_previous_lines(2)
			elif spot == 'H':
				spot = get_board_history_input_from_user(is_ai=False)
			elif not spot.isdigit() or int(spot) < 1 or int(spot) > 6:
				spot = input(f"{ERROR_SYMBOL} Please enter a number 1 - {POCKETS_PER_SIDE}:\t").strip().upper()
				erase_previous_lines(1)
			elif board[int(spot) - 1] == 0:
				spot = input(f"{ERROR_SYMBOL} That pocket is empty! Please try again:\t").strip().upper()
				erase_previous_lines(1)
			else:
				break

		return int(spot) - 1


def print_board(board, player_id=None, move=None):
	"""Prints the game board"""
	# orientation
	arrow_index = -1
	if USE_REVERSED_PRINT_LAYOUT:
		top_bank_index = PLAYER1_BANK_INDEX
		bottom_bank_index = PLAYER2_BANK_INDEX
		left_side_player_id = PLAYER2_ID
		top_left_pocket_index = POCKETS_PER_SIDE + 1  # which index is printed in the top left corner of the printed board
		left_side_color = RED_COLOR
		right_side_color = GREEN_COLOR
		if move is not None:
			arrow_index = move if move > POCKETS_PER_SIDE else get_index_of_opposite_hole(move)
	else:
		top_bank_index = PLAYER2_BANK_INDEX
		bottom_bank_index = PLAYER1_BANK_INDEX
		left_side_player_id = PLAYER1_ID
		top_left_pocket_index = 0
		left_side_color = GREEN_COLOR
		right_side_color = RED_COLOR
		if move is not None:
			arrow_index = move if move < POCKETS_PER_SIDE else get_index_of_opposite_hole(move)

	print()
	print(SIDE_INDENT_STR + " " * 5 + f"{right_side_color}{board[top_bank_index]}{NO_COLOR}")  # top bank
	print(SIDE_INDENT_STR + "___________")
	for index in range(top_left_pocket_index, top_left_pocket_index + POCKETS_PER_SIDE):
		left_side_str_prefix = SIDE_INDENT_STR  # may change to arrow
		right_side_str_suffix = ""  # may change to arrow
		if index == arrow_index:
			if player_id == left_side_player_id:
				left_side_str_prefix = LEFT_SIDE_ARROW
			else:
				right_side_str_suffix = RIGHT_SIDE_ARROW

		left_side_str = left_side_str_prefix + " " * 2 \
					  + f"{left_side_color}{board[index]}{NO_COLOR}" \
					  + (" " if board[index] >= 10 else "  ")
		right_side_str = (" " if board[get_index_of_opposite_hole(index)] >= 10 else "  ") \
					   + f"{right_side_color}{board[get_index_of_opposite_hole(index)]}{NO_COLOR}" \
					   + right_side_str_suffix
		print(SIDE_INDENT_STR + "     |     ")
		print(left_side_str + str(min(index, get_index_of_opposite_hole(index)) + 1) + right_side_str)
		print(SIDE_INDENT_STR + "_____|_____")
	print("\n" + SIDE_INDENT_STR + " " * 5 + f"{left_side_color}{board[bottom_bank_index]}{NO_COLOR}\n")  # bottom bank


def opponent_of(player_id):
	"""Gets the id opponent of the given id"""
	return PLAYER1_ID if player_id == PLAYER2_ID else PLAYER2_ID


def print_average_time_taken_by_players(time_taken_per_player):
	"""Prints out the average time taken per move for each player"""
	user_time_taken = round(time_taken_per_player[PLAYER1_ID][1] / max(1, time_taken_per_player[PLAYER1_ID][2]), 2)
	ai_time_taken = round(time_taken_per_player[PLAYER2_ID][1] / max(1, time_taken_per_player[PLAYER2_ID][2]), 2)
	print("Average time taken per move:")
	print(f"{color_text(str(time_taken_per_player[PLAYER1_ID][0]), GREEN_COLOR)}: {user_time_taken}s")
	print(f"{color_text(str(time_taken_per_player[PLAYER2_ID][0]), RED_COLOR)}: {ai_time_taken}s")


def print_ascii_art():
	"""Prints the Mancala Capture Ascii Art"""
	print(r"""
  __  __                       _       
 |  \/  |                     | |      
 | \  / | __ _ _ __   ___ __ _| | __ _ 
 | |\/| |/ _` | '_ \ / __/ _` | |/ _` |
 | |  | | (_| | | | | (_| (_| | | (_| |
 |_|__|_|\__,_|_| |_|\___\__,_|_|\__,_|
  / ____|          | |                 
 | |     __ _ _ __ | |_ _   _ _ __ ___ 
 | |    / _` | '_ \| __| | | | '__/ _ \ 
 | |___| (_| | |_) | |_| |_| | | |  __/
  \_____\__,_| .__/ \__|\__,_|_|  \___|
             | |                       
             |_|  
    """)


def input_for_board():
	"""Reads in the input for the board from the user"""
	player_values_input = input(f"""
From your left to your right (or top to bottom), enter the # of pebbles in
each spot on {GREEN_COLOR}your{NO_COLOR} side of the board, with a space separating each number:

    """).strip().split()
	while True:
		try:
			erase_previous_lines(1)
			player_vals = [int(item) for item in player_values_input]
			if len(player_vals) != POCKETS_PER_SIDE:
				player_values_input = input(f"{ERROR_SYMBOL} There should be {POCKETS_PER_SIDE} values entered.\t").strip().split()
				continue
			break
		except ValueError:
			player_values_input = input(
				f"{ERROR_SYMBOL} There was an issue with your input. Please try again.\t").strip().split()
	erase_previous_lines(4)

	enemy_values_input = input(f"""
From your left to your right (or top to bottom), enter the # of pebbles in
each spot on the {RED_COLOR}enemy{NO_COLOR} side of the board, with a space separating each number:

    """).strip().split()
	while True:
		erase_previous_lines(1)
		try:
			enemy_vals = [int(item) for item in enemy_values_input]
			if len(enemy_vals) != POCKETS_PER_SIDE:
				enemy_values_input = input(f"{ERROR_SYMBOL} There should be {POCKETS_PER_SIDE} values entered.\t").strip().split()
				continue
			break
		except ValueError:
			enemy_values_input = input(
				f"{ERROR_SYMBOL} There was an issue with your input. Please try again.\t").strip().split()
	erase_previous_lines(4)

	enemy_vals.reverse()
	return player_vals + [0] + enemy_vals + [0]


def save_game(board, turn):
	"""Saves the given board state to a save file"""
	if not allow_save(SAVE_FILENAME):
		return
	with open(SAVE_FILENAME, 'w') as save_file:
		save_file.write("This file contains the save state of a previously played game.\n")
		save_file.write("Modifying this file may cause issues with loading the save state.\n\n")
		time_of_save = datetime.now().strftime("%m/%d/%Y at %I:%M:%S %p")
		save_file.write(time_of_save + "\n\n")
		save_file.write("SAVE STATE:\n")
		save_file.write(f"   {board[PLAYER2_BANK_INDEX]}\n")  # opponent bank
		for row in range(len(board) // 2 - 1):  # playable caves; default 1 - 6
			save_file.write(
				str(board[row]) + (" | " if board[row] >= 10 else "  | ") + str(board[-1 * (row + 2)]) + "\n")
		save_file.write(f"   {str(board[PLAYER1_BANK_INDEX])}\n")  # player bank
		save_file.write(f"Turn: {turn}")
	info("The game has been saved!")


def validate_loaded_save_state(board, turn):
	"""Make sure the state loaded from the save file is valid. Returns a boolean"""
	if turn not in [PLAYER1_ID, PLAYER2_ID]:
		print(f"{ERROR_SYMBOL} Invalid player turn!")
		return False
	if len(board) % 2 != 0:
		print(f"{ERROR_SYMBOL} Please ensure each player has a bank and the same number of pockets!")
		return False
	num_rows = len(board) // 2 - 1
	if num_rows != POCKETS_PER_SIDE:
		print(f"{ERROR_SYMBOL} # Rows must be {POCKETS_PER_SIDE}! Was {num_rows}")
		return False
	for spot in board:
		if spot < 0:
			print(f"{ERROR_SYMBOL} Pockets cannot have a negative amount of pebbles!")
			return False
	return True


def load_saved_game():
	"""Try to load the saved game data"""
	global BOARD
	with open(SAVE_FILENAME, 'r') as save_file:
		try:
			lines_from_save_file = save_file.readlines()
			time_of_previous_save = lines_from_save_file[3].strip()
			use_existing_save = input(
				f"{INFO_SYMBOL} Would you like to load the saved game from {time_of_previous_save}? (y/n)\t").strip().lower()
			erase_previous_lines(1)
			if use_existing_save != 'y':
				info("Starting a new game...")
				return
			line_num = 0
			current_line = lines_from_save_file[line_num].strip()
			while current_line != "SAVE STATE:":
				line_num += 1
				current_line = lines_from_save_file[line_num].strip()
			line_num += 1
			current_line = lines_from_save_file[line_num].strip()

			opponent_bank = [int(current_line.strip())]
			line_num += 1
			current_line = lines_from_save_file[line_num].strip()

			user_pockets = []
			opponent_pockets = []
			while "|" in current_line:
				user_pockets.append(int(current_line.split("|")[0].strip()))
				opponent_pockets.append(int(current_line.split("|")[1].strip()))
				line_num += 1
				current_line = lines_from_save_file[line_num].strip()
			user_bank = [int(current_line.strip())]
			board = user_pockets + user_bank + opponent_pockets + opponent_bank

			while not current_line.startswith("Turn:"):
				line_num += 1
				current_line = lines_from_save_file[line_num].strip()
			turn = int(current_line.split()[1])

			if not validate_loaded_save_state(board, turn):
				raise ValueError
			BOARD = board
			delete_save_file = input(
				f"{INFO_SYMBOL} Saved game was successfully loaded! Delete the save file? (y/n)\t").strip().lower()
			erase_previous_lines(1)
			file_deleted_text = ""
			if delete_save_file == 'y':
				os.remove(SAVE_FILENAME)
				file_deleted_text = "Save file deleted."
			info(f"{file_deleted_text} Resuming saved game...")
			return turn
		except Exception:
			print(f"{ERROR_SYMBOL} There was an issue reading from the save file. Starting a new game...")
			return None


def print_move_history(num_moves_previous):
	"""Prints the move history of the current game"""
	while True:
		erase_previous_lines(2)
		print_board(BOARD_HISTORY[-(num_moves_previous + 1)][2], BOARD_HISTORY[-(num_moves_previous + 1)][1],
					BOARD_HISTORY[-(num_moves_previous + 1)][0])
		if num_moves_previous == 0:
			return
		print("(%d move%s before current board state)\n" % (num_moves_previous, "s" if num_moves_previous != 1 else ""))
		num_moves_previous -= 1
		user_input = input("Press enter for next move, or 'e' to return to game.  ").strip().lower()
		erase_previous_lines(1)
		if user_input == 'q':
			erase_previous_lines(2)
			print("\nThanks for playing!\n")
			exit(0)
		elif user_input == 'e':
			erase_previous_lines(2)
			return
		else:
			erase_previous_lines(BOARD_OUTPUT_HEIGHT)


def get_board_history_input_from_user(is_ai):
	"""
    Prompts the user for input for how far the board history function.
    Returns the user's input for the next move
    """
	next_move_prompt = "Press enter to continue." if is_ai else "Enter a valid move to play:"
	if len(BOARD_HISTORY) < 2:
		user_input = input(f"{INFO_SYMBOL} No previous moves to see. {next_move_prompt}   ").strip().upper()
		erase_previous_lines(1)
	else:
		num_moves_previous = input(f"How many moves ago do you want to see? (1 to {len(BOARD_HISTORY) - 1})  ").strip()
		erase_previous_lines(1)
		if num_moves_previous.isdigit() and 1 <= int(num_moves_previous) <= len(BOARD_HISTORY) - 1:
			erase_previous_lines(BOARD_OUTPUT_HEIGHT)
			print_move_history(int(num_moves_previous))
			erase_previous_lines(BOARD_OUTPUT_HEIGHT)
			print_board(BOARD_HISTORY[-1][2], BOARD_HISTORY[-1][1], BOARD_HISTORY[-1][0])
			user_input = input(f"{INFO_SYMBOL} You're back in play mode. {next_move_prompt}   ").strip().upper()
			erase_previous_lines(1)
			print("\n")  # make this output the same height as the other options
		else:
			user_input = input(f"{ERROR_SYMBOL} Invalid input. {next_move_prompt}   ").strip().upper()
			erase_previous_lines(1)
	return user_input


def run():
	global BOARD
	print_ascii_art()
	BOARD = input_for_board()
	strategy = MancalaStrategy(PLAYER1_BANK_INDEX)

	print("\nThe current board looks like this:\n")
	print_board(BOARD)
	print()

	first_iteration = True
	extra_lines_above_board = 4  # header(3) + blank(1) on first iteration
	while True:
		user_input = input("Press enter to receive best move, or 'q' to quit.\t").strip().lower()
		erase_previous_lines(1)
		if user_input == 'q':
			print("\nThanks for playing!\n")
			exit(0)

		best_move = strategy.get_move(BOARD)
		move_num = best_move + 1  # indices 0-5 -> spots 1-6
		final_pebble_location = perform_move(BOARD, best_move, PLAYER1_BANK_INDEX)
		extra_turn = (final_pebble_location == PLAYER1_BANK_INDEX)

		erase_previous_lines(BOARD_OUTPUT_HEIGHT + extra_lines_above_board)
		print_board(BOARD, PLAYER1_ID, best_move)
		print("Best move: spot %d.%s\n" % (move_num, " Last pebble landed in your bank — you get another turn!" if extra_turn else ""))

		if is_board_terminal(BOARD):
			push_all_pebbles_to_bank(BOARD)
			erase_previous_lines(BOARD_OUTPUT_HEIGHT + 2)
			print_board(BOARD)
			winner_bank = winning_player_bank_index(BOARD)
			if winner_bank == PLAYER1_BANK_INDEX:
				print("You win!\n")
			elif winner_bank == PLAYER2_BANK_INDEX:
				print("Opponent wins!\n")
			else:
				print("It's a tie!\n")
			break

		if not extra_turn:
			print("Input the new board after the opponent's turn.")
			BOARD = input_for_board()
			erase_previous_lines(BOARD_OUTPUT_HEIGHT + 3)
			print_board(BOARD)
			print()
			extra_lines_above_board = 1  # next erase: board(BOARD_OUTPUT_HEIGHT) + blank(1)
		else:
			extra_lines_above_board = 2  # next erase: board + "Best move...\n" (2 lines)

		first_iteration = False

if __name__ == '__main__':
	run()
