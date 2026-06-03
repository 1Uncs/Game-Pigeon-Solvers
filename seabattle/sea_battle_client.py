from datetime import datetime
import os

from util.terminaloutput.colors import (
	GREEN_COLOR,
	YELLOW_COLOR,
	RED_COLOR,
	NO_COLOR,
	DARK_GREY_BACKGROUND as MOST_RECENT_HIGHLIGHT_COLOR,
	DARK_PURPLE_COLOR as OPTIMAL_COLOR,
	color_text,
)
from util.terminaloutput.symbols import ERROR_SYMBOL, INFO_SYMBOL, error, info
from util.terminaloutput.erasing import erase_previous_lines
from util.save.saving import path_to_save_file, allow_save

from seabattle.sea_battle_strategy import (
	Board,
	EMPTY,
	HIT,
	MISS,
	SUNK,
	SeaBattleStrategy,
)


SAVE_FILENAME = path_to_save_file("sea_battle_save.txt")
DISPLAY_EMPTY = "-"
DISPLAY_HIT = "H"
DISPLAY_MISS = "^"
DISPLAY_SUNK = "D"

SUPPORTED_SIZES = (8, 9, 10)


class SeaBattleGame:
	def __init__(self, board=None, column_labels=None):
		self.board = board if board is not None else Board(10)
		self.column_labels = column_labels if column_labels is not None else [chr(ord("A") + i) for i in range(self.board.size)]
		self.strategy = SeaBattleStrategy(self.board)

	@property
	def size(self):
		return self.board.size

	@property
	def remaining_ships(self):
		return self.board.fleet

	def record_shot(self, row, col, result):
		self.board.record_shot(row, col, result)

	def optimal_moves(self):
		return self.strategy.get_optimal_moves()

	def score_grid(self):
		return self.strategy.get_score_grid()

	def is_over(self):
		return self.board.is_complete()

	def print_board(self, most_recent_move=None, optimal_locations=None):
		if optimal_locations is None:
			optimal_locations = []
		print("\n\t    %s\n" % " ".join(self.column_labels))
		ships_remain = []
		for length in sorted(self.remaining_ships.keys(), reverse=True):
			if self.remaining_ships[length] > 0:
				ships_remain.append((length, self.remaining_ships[length]))
		for row in range(self.size):
			print("\t%d%s| " % (row + 1, "" if row > 8 else " "), end="")
			for col in range(self.size):
				spot = self._display_cell(self.board.grid[row][col])
				piece_color = MOST_RECENT_HIGHLIGHT_COLOR if [row, col] == most_recent_move else ""
				if spot == DISPLAY_HIT:
					piece_color += YELLOW_COLOR
				elif spot == DISPLAY_MISS:
					piece_color += RED_COLOR
				elif spot == DISPLAY_SUNK:
					piece_color += GREEN_COLOR
				elif [row, col] in optimal_locations:
					piece_color += OPTIMAL_COLOR
				else:
					piece_color += NO_COLOR
				print(f"{piece_color}%s{NO_COLOR} " % spot, end="")
			if row == 0:
				print("\tRemaining ships:")
			elif row == 2 and len(ships_remain) > 0:
				l, c = ships_remain[0]
				print("\t%dx  %s" % (c, "S" * l))
			elif row == 4 and len(ships_remain) > 1:
				l, c = ships_remain[1]
				print("\t%dx  %s" % (c, "S" * l))
			elif row == 6 and len(ships_remain) > 2:
				l, c = ships_remain[2]
				print("\t%dx  %s" % (c, "S" * l))
			elif row == 8 and len(ships_remain) > 3:
				l, c = ships_remain[3]
				print("\t%dx  %s" % (c, "S" * l))
			else:
				print("")
		print()

	@staticmethod
	def _display_cell(state):
		if state == HIT:
			return DISPLAY_HIT
		if state == MISS:
			return DISPLAY_MISS
		if state == SUNK:
			return DISPLAY_SUNK
		return DISPLAY_EMPTY

	def print_score_table(self, color_mode=True):
		score = self.score_grid()
		max_score = -1.0
		min_score = float("inf")
		for row in score:
			for v in row:
				if v > 0:
					if v < min_score:
						min_score = v
					if v > max_score:
						max_score = v
		if max_score < 0:
			return

		def get_color(value):
			if value == max_score:
				return OPTIMAL_COLOR
			if value == 0:
				return RED_COLOR
			rng = max(max_score - min_score, 1e-9)
			pct = 100 * ((value - min_score) / rng)
			if pct > 75:
				return GREEN_COLOR
			if pct > 40:
				return YELLOW_COLOR
			return "\u001b[38;5;208m"

		print("\n   ", end="")
		for letter in self.column_labels:
			print(f"    {letter}", end="")
		print("\n   %s" % ("-" * 55))
		for r in range(self.size):
			row = score[r]
			print("%s%d |   " % ("" if r < 9 else "", r + 1), end="")
			for value in row:
				if color_mode:
					color = get_color(value)
				else:
					color = NO_COLOR
				if value == 0:
					print(color_text("0    ", color), end="")
				else:
					s = str(int(value * 100))
					pad = 4 - len(s)
					print(color_text(s + " " * pad, color), end="")
			print("|")
		print("   %s\n" % ("-" * 55))


def save_game(game):
	if not allow_save(SAVE_FILENAME):
		return
	with open(SAVE_FILENAME, "w") as save_file:
		save_file.write("This file contains the save state of a previously played game.\n")
		save_file.write("Modifying this file may cause issues with loading the save state.\n\n")
		save_file.write(datetime.now().strftime("%m/%d/%Y at %I:%M:%S %p") + "\n\n")
		save_file.write("SAVE STATE:\n")
		for row in game.board.grid:
			save_file.write(" ".join(_state_to_char(c) for c in row) + "\n")
		save_file.write("Ships remaining:\n")
		for ship_size, num_ships in sorted(game.remaining_ships.items()):
			save_file.write(f"{ship_size}: {num_ships}\n")
		save_file.write("END")
	info("The game has been saved!")


def _state_to_char(state):
	if state == HIT:
		return DISPLAY_HIT
	if state == MISS:
		return DISPLAY_MISS
	if state == SUNK:
		return DISPLAY_SUNK
	return DISPLAY_EMPTY


def _char_to_state(ch):
	if ch == DISPLAY_HIT:
		return HIT
	if ch == DISPLAY_MISS:
		return MISS
	if ch == DISPLAY_SUNK:
		return SUNK
	return EMPTY


def load_saved_game():
	if not os.path.exists(SAVE_FILENAME):
		return None
	with open(SAVE_FILENAME, "r") as save_file:
		try:
			lines = save_file.readlines()
			time_of_previous_save = lines[3].strip()
			use_existing_save = input(
				f"{INFO_SYMBOL} Would you like to load the saved game from {time_of_previous_save}? (y/n)\t"
			).strip().lower()
			erase_previous_lines(1)
			if use_existing_save != "y":
				info("Starting a new game...")
				return None
			line_num = 0
			current = lines[line_num].strip()
			while current != "SAVE STATE:":
				line_num += 1
				current = lines[line_num].strip()
			line_num += 1
			board_rows = []
			current = lines[line_num].strip()
			while not current.startswith("Ships remaining:"):
				board_rows.append([_char_to_state(c) for c in current.split()])
				line_num += 1
				current = lines[line_num].strip()
			line_num += 1
			fleet = {}
			current = lines[line_num].strip()
			while not current.startswith("END"):
				size_str, count_str = current.split(":")[:2]
				fleet[int(size_str.strip())] = int(count_str.strip())
				line_num += 1
				current = lines[line_num].strip()
		except Exception:
			error("There was an issue reading from the save file. Starting a new game...")
			return None

	size = len(board_rows)
	if size not in SUPPORTED_SIZES:
		error(f"Saved board size {size} is not supported.")
		return None
	expected = {1: HIT, 2: SUNK, 3: MISS, 4: EMPTY}
	if any(c not in expected for row in board_rows for c in row):
		error("Saved board contains invalid characters.")
		return None
	if any(len(row) != size for row in board_rows):
		error("Saved board is not square.")
		return None
	if any(size not in range(1, 5) for size in fleet):
		error("Saved fleet contains invalid ship sizes.")
		return None
	if any(count < 0 for count in fleet.values()):
		error("Saved fleet contains negative ship counts.")
		return None
	if sum(fleet.values()) == 0:
		error("Saved fleet has no ships remaining.")
		return None

	board = Board(size, fleet)
	board.grid = board_rows
	delete = input(f"{INFO_SYMBOL} Saved game was successfully loaded! Delete the save file? (y/n)\t").strip().lower()
	erase_previous_lines(1)
	deleted = ""
	if delete == "y":
		os.remove(SAVE_FILENAME)
		deleted = "Save file deleted. "
	info(f"{deleted}Resuming saved game...")
	return SeaBattleGame(board=board)


def get_player_move(game):
	size = game.size
	labels = game.column_labels
	optimal = game.optimal_moves()
	prompt = "Which spot would you like to play? (A1 - %s%d):\t" % (labels[-1], size)
	lines_to_erase = game.size + 4 + 2

	while True:
		spot = input(prompt).strip().upper()
		erase_previous_lines(1)
		if spot == "Q":
			print("\nThanks for playing!\n")
			exit(0)
		elif spot == "D":
			erase_previous_lines(lines_to_erase)
			game.print_score_table()
			lines_to_erase = game.size + 5
			print("The space densities table is shown above. To show the game board, type 'b'")
			spot = input(prompt).strip().upper()
			erase_previous_lines(2)
			continue
		elif spot == "B":
			erase_previous_lines(lines_to_erase)
			game.print_board(optimal_locations=optimal)
			print("\nThe current game board is shown above.")
			lines_to_erase = game.size + 4 + 2
			spot = input(prompt).strip().upper()
			erase_previous_lines(1)
			continue
		elif spot == "S":
			save_game(game)
			spot = input(prompt).strip().upper()
			erase_previous_lines(2)
			continue
		parsed = _parse_spot(spot, labels, size)
		if parsed is None:
			spot = input(f"{ERROR_SYMBOL} Invalid input. Please try again.\t").strip().upper()
			erase_previous_lines(1)
			continue
		row, col = parsed
		if game.board.cell(row, col) != EMPTY:
			spot = input(f"{ERROR_SYMBOL} That spot is already taken, please choose another:\t").strip().upper()
			erase_previous_lines(1)
			parsed = None
			while parsed is None:
				parsed = _parse_spot(spot, labels, size)
				if parsed is None:
					spot = input(f"{ERROR_SYMBOL} Invalid input. Please try again.\t").strip().upper()
					erase_previous_lines(1)
			row, col = parsed
		if [row, col] not in optimal:
			confirm = input(
				f"{ERROR_SYMBOL} {spot} is not in the list of optimal moves. Are you sure you want to make that move? (y/n)\t"
			).strip().upper()
			erase_previous_lines(1)
			while confirm not in ("Y", "N"):
				confirm = input(f"{ERROR_SYMBOL} Please enter 'y' or 'n':\t").strip().upper()
				erase_previous_lines(1)
			if confirm == "N":
				spot = input("Phew! Okay, where would you like to play? (A1 - %s%d):\t" % (labels[-1], size)).strip().upper()
				erase_previous_lines(1)
				continue
		return row, col


def _parse_spot(spot, labels, size):
	if len(spot) < 2:
		return None
	col_char = spot[0]
	row_str = spot[1:]
	if col_char not in labels or not row_str.isdigit():
		return None
	row = int(row_str) - 1
	if not (0 <= row < size):
		return None
	col = labels.index(col_char)
	return row, col


def run():
	print("""
   _____              ____        _   _   _
  / ____|            |  _ \\      | | | | | |
 | (___   ___  __ _  | |_) | __ _| |_| |_| | ___
  \\___ \\ / _ \\/ _` | |  _ < / _` | __| __| |/ _ \\
  ____) |  __/ (_| | | |_) | (_| | |_| |_| |  __/
 |_____/ \\___|\\__,_| |____/ \\__,_|\\__|\\__|_|\\___|
 """)
	print("The default board size is 10x10.")
	print("To show the color-coded space density table, type 'd' at the move selection prompt.")
	print("To re-display the current game board, type 'b' at the move selection prompt.")
	print("To save the game, type 's' at the move selection prompt.")
	print("To quit, type 'q' at any prompt.\n")

	game = load_saved_game()
	if game is None:
		dim = input("What is the dimension of the board (8, 9, or 10)? (Default is 10x10)\nEnter a single number:\t").strip()
		erase_previous_lines(2)
		if dim.isdigit() and int(dim) in SUPPORTED_SIZES:
			print("The board will be %sx%s!" % (dim, dim))
		else:
			dim = 10
			error("Invalid input. The board will be 10x10!")
		game = SeaBattleGame(board=Board(int(dim)))

	best = game.optimal_moves()
	game.print_board(optimal_locations=best)
	while True:
		if not best:
			for segment, length in game.board.fully_known_ships():
				first = segment[0]
				last = segment[-1]
				print(
					f"\nThe ship at {chr(ord('A') + first[1])}{first[0] + 1}-"
					f"{chr(ord('A') + last[1])}{last[0] + 1} appears fully discovered "
					f"({length} cells). Mark it as sunk to continue."
				)
		elif len(best) > 1:
			words = ("spots", "are", "have")
			print(f"\nThe %s that %s most likely to contain a ship %s been colored {OPTIMAL_COLOR}blue{NO_COLOR}." % words)
		else:
			print(f"\nThe spot that is most likely to contain a ship has been colored {OPTIMAL_COLOR}blue{NO_COLOR}.")
		row, col = get_player_move(game)
		erase_previous_lines(game.size + 4 + 2)
		game.print_board([row, col], best)
		print("\nThe selected move has been highlighted.")
		outcome = input("Was that shot a miss (M), a partial-hit (H), or a sink (S)?\t").strip().upper()
		erase_previous_lines(1)
		while outcome not in ("Q", "H", "S", "M"):
			outcome = input(f"{ERROR_SYMBOL} Invalid input. Try again:\t").strip().upper()
			erase_previous_lines(1)
		if outcome == "M":
			game.board.grid[row][col] = MISS
		elif outcome == "H":
			game.board.grid[row][col] = HIT
		elif outcome == "S":
			try:
				game.record_shot(row, col, "sunk")
			except ValueError as exc:
				error(str(exc))
				continue
		else:
			print("\nThanks for playing!\n")
			exit(0)

		if game.is_over():
			break
		best = game.optimal_moves()
		erase_previous_lines(game.size + 4 + 2)
		game.print_board([row, col], best)

	erase_previous_lines(game.size + 4 + 2)
	game.print_board(most_recent_move=[row, col])
	print("\nGood job, you won!\n")
