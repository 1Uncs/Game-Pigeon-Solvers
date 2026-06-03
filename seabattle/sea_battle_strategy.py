EMPTY = '.'
MISS = 'M'
HIT = 'X'
SUNK = 'S'

FLEET_10 = {1: 4, 2: 2, 3: 2, 4: 1, 5: 1}
FLEET_9 = {3: 8}
FLEET_8 = {2: 2, 3: 2, 4: 1, 5: 1}

PLACEMENT_WEIGHT = 0.7
INFO_GAIN_WEIGHT = 0.3
PARITY_BOOST = 1.15

DIRECTIONS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRECTIONS_8 = (
	(-1, -1), (-1, 0), (-1, 1),
	(0, -1),           (0, 1),
	(1, -1),  (1, 0),  (1, 1),
)


def fleet_for_size(size):
	if size == 10:
		return dict(FLEET_10)
	if size == 9:
		return dict(FLEET_9)
	if size == 8:
		return dict(FLEET_8)
	raise ValueError(f"Unsupported board size: {size}")


def in_bounds(size, r, c):
	return 0 <= r < size and 0 <= c < size


def _ship_cells(start_r, start_c, length, vertical):
	if vertical:
		return frozenset((start_r + i, start_c) for i in range(length))
	return frozenset((start_r, start_c + i) for i in range(length))


def _adjacent_cells_of_ship(start_r, start_c, length, vertical, size):
	cells = _ship_cells(start_r, start_c, length, vertical)
	adj = set()
	for r, c in cells:
		for dr, dc in DIRECTIONS_8:
			nr, nc = r + dr, c + dc
			if in_bounds(size, nr, nc) and (nr, nc) not in cells:
				adj.add((nr, nc))
	return frozenset(adj)


def _all_placements_for_length(size, length):
	placements = []
	for r in range(size):
		for c in range(size - length + 1):
			placements.append((_ship_cells(r, c, length, False), _adjacent_cells_of_ship(r, c, length, False, size)))
	for c in range(size):
		for r in range(size - length + 1):
			placements.append((_ship_cells(r, c, length, True), _adjacent_cells_of_ship(r, c, length, True, size)))
	return placements


_PLACEMENT_CACHE = {}


def _cached_placements(size, length):
	key = (size, length)
	cached = _PLACEMENT_CACHE.get(key)
	if cached is None:
		cached = _all_placements_for_length(size, length)
		_PLACEMENT_CACHE[key] = cached
	return cached


class Board:
	def __init__(self, size, fleet=None):
		if fleet is None:
			fleet = fleet_for_size(size)
		self.size = size
		self.fleet = dict(fleet)
		self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]

	def clone(self):
		new = Board.__new__(Board)
		new.size = self.size
		new.fleet = dict(self.fleet)
		new.grid = [row[:] for row in self.grid]
		return new

	def cell(self, r, c):
		return self.grid[r][c]

	def record_shot(self, row, col, result):
		result = result.lower()
		if not in_bounds(self.size, row, col):
			raise ValueError(f"Position ({row}, {col}) out of bounds")
		current = self.grid[row][col]
		if current != EMPTY:
			raise ValueError(f"Cell ({row}, {col}) already shot: {current}")
		if result == "miss":
			self.grid[row][col] = MISS
			return
		if result == "hit":
			self.grid[row][col] = HIT
			return
		if result == "sunk":
			self._sink_ship(row, col)
			return
		raise ValueError(f"Unknown shot result: {result!r}")

	def _sink_ship(self, row, col):
		self.grid[row][col] = HIT
		segment = self._collect_segment(row, col, {HIT})
		if not segment:
			self.grid[row][col] = SUNK
			return
		ship_len = len(segment)
		if ship_len not in self.fleet or self.fleet[ship_len] <= 0:
			raise ValueError(f"Sunk ship length {ship_len} is not in fleet {self.fleet}")
		for r, c in segment:
			self.grid[r][c] = SUNK
		self.fleet[ship_len] -= 1
		for r, c in segment:
			for dr, dc in DIRECTIONS_8:
				nr, nc = r + dr, c + dc
				if in_bounds(self.size, nr, nc) and self.grid[nr][nc] == EMPTY:
					self.grid[nr][nc] = MISS

	def _collect_segment(self, row, col, allowed):
		if self.grid[row][col] not in allowed and not (allowed == {HIT} and self.grid[row][col] == SUNK):
			return []
		stack = [(row, col)]
		visited = set()
		segment = []
		while stack:
			r, c = stack.pop()
			if (r, c) in visited:
				continue
			if self.grid[r][c] not in allowed:
				continue
			visited.add((r, c))
			segment.append((r, c))
			for dr, dc in DIRECTIONS_4:
				nr, nc = r + dr, c + dc
				if in_bounds(self.size, nr, nc) and (nr, nc) not in visited:
					stack.append((nr, nc))
		return segment

	def hit_segments(self):
		visited = set()
		segments = []
		for r in range(self.size):
			for c in range(self.size):
				if self.grid[r][c] == HIT and (r, c) not in visited:
					seg = self._collect_segment(r, c, {HIT})
					visited.update(seg)
					segments.append(sorted(seg))
		return segments

	def fully_known_ships(self):
		result = []
		for segment in self.hit_segments():
			length = len(segment)
			if length in self.fleet and self.fleet[length] > 0:
				result.append((segment, length))
		return result

	def remaining_ship_cells(self):
		return sum(size * count for size, count in self.fleet.items())

	def remaining_ship_count(self):
		return sum(self.fleet.values())

	def is_complete(self):
		return self.remaining_ship_count() == 0

	def remaining_ship_sizes(self):
		return {size for size, count in self.fleet.items() if count > 0}

	def parity_value(self):
		alive = self.remaining_ship_sizes()
		if not alive:
			return 0
		return min(alive)


class SeaBattleStrategy:
	def __init__(self, board):
		self.board = board

	def _valid_placements_for_length(self, length):
		size = self.board.size
		grid = self.board.grid
		results = []
		for cells, adj in _cached_placements(size, length):
			if any(grid[r][c] in (MISS, SUNK) for r, c in cells):
				continue
			if any(grid[r][c] in (HIT, SUNK) for r, c in adj):
				continue
			results.append(cells)
		return results

	def _all_valid_placements(self):
		all_placements = {}
		for length, count in self.board.fleet.items():
			if count <= 0:
				continue
			all_placements[length] = self._valid_placements_for_length(length)
		return all_placements

	def _placement_score_grid(self, all_placements):
		size = self.board.size
		score = [[0.0] * size for _ in range(size)]
		for length, placements in all_placements.items():
			count = self.board.fleet.get(length, 0)
			if count <= 0 or not placements:
				continue
			weight = count / len(placements)
			for cells in placements:
				for r, c in cells:
					score[r][c] += weight
		return score

	def _info_gain_grid(self, placement_score):
		size = self.board.size
		grid = self.board.grid
		gain = [[0.0] * size for _ in range(size)]
		for r in range(size):
			for c in range(size):
				if grid[r][c] != EMPTY:
					continue
				neighbor_total = 0.0
				for dr, dc in DIRECTIONS_8:
					nr, nc = r + dr, c + dc
					if in_bounds(size, nr, nc):
						neighbor_total += placement_score[nr][nc]
				gain[r][c] = neighbor_total
		return gain

	def _hunt_score_grid(self):
		all_placements = self._all_valid_placements()
		if not all_placements:
			return [[0.0] * self.board.size for _ in range(self.board.size)]
		placement = self._placement_score_grid(all_placements)
		info = self._info_gain_grid(placement)
		combined = [
			[
				PLACEMENT_WEIGHT * placement[r][c] + INFO_GAIN_WEIGHT * info[r][c]
				for c in range(self.board.size)
			]
			for r in range(self.board.size)
		]
		if self.board.remaining_ship_sizes():
			combined = self._apply_parity(combined)
		return combined

	def _apply_parity(self, score):
		size = self.board.size
		stride = self.board.parity_value()
		if stride <= 1:
			return score
		parities = [0] * stride
		for r in range(size):
			for c in range(size):
				parities[(r + c) % stride] += 1
		best_parity = max(range(stride), key=lambda p: parities[p])
		boosted = [row[:] for row in score]
		for r in range(size):
			for c in range(size):
				if self.board.grid[r][c] != EMPTY:
					boosted[r][c] = 0.0
					continue
				if (r + c) % stride == best_parity:
					boosted[r][c] *= PARITY_BOOST
				else:
					boosted[r][c] = 0.0
		return boosted

	def _target_score_grid(self):
		size = self.board.size
		score = [[0.0] * size for _ in range(size)]
		segments = self.board.hit_segments()
		if not segments:
			return score
		alive_sizes = self.board.remaining_ship_sizes()
		if not alive_sizes:
			return score
		max_boost = 0.0
		all_placements = self._all_valid_placements()
		for length, placements in all_placements.items():
			max_boost += self.board.fleet.get(length, 0) / max(len(placements), 1)
		for segment in segments:
			self._score_segment(segment, score, alive_sizes, max_boost)
		return score

	def _score_segment(self, segment, score, alive_sizes, max_boost):
		candidates = []
		if len(segment) == 1:
			row, col = segment[0]
			candidates = [
				((row - 1, col), (-1, 0)),
				((row + 1, col), (1, 0)),
				((row, col - 1), (0, -1)),
				((row, col + 1), (0, 1)),
			]
		else:
			if all(r == segment[0][0] for r, _ in segment):
				cols = sorted(c for _, c in segment)
				candidates = [
					(((segment[0][0], cols[0] - 1)), (0, -1)),
					(((segment[0][0], cols[-1] + 1)), (0, 1)),
				]
			else:
				rows = sorted(r for r, _ in segment)
				candidates = [
					(((rows[0] - 1, segment[0][1])), (-1, 0)),
					(((rows[-1] + 1, segment[0][1])), (1, 0)),
				]
		for (er, ec), (dr, dc) in candidates:
			if not in_bounds(self.board.size, er, ec):
				continue
			if self.board.grid[er][ec] != EMPTY:
				continue
			base = self._extension_score(segment, (er, ec), alive_sizes, max_boost)
			openness = self._openness(er, ec, dr, dc)
			cell_score = base * (1.0 + 0.05 * openness)
			if cell_score > score[er][ec]:
				score[er][ec] = cell_score

	def _openness(self, row, col, dr, dc):
		count = 0
		r, c = row + dr, col + dc
		while in_bounds(self.board.size, r, c) and self.board.grid[r][c] == EMPTY:
			count += 1
			r, c = r + dr, c + dc
		return count

	def _extension_score(self, segment, candidate, alive_sizes, max_boost):
		seg_len = len(segment)
		best = 0.0
		for ship_len in alive_sizes:
			if ship_len < seg_len + 1:
				continue
			if seg_len + 1 == ship_len:
				best += max_boost
			elif self._can_extend_to_ship(segment, candidate, ship_len):
				best += max_boost * 0.5
		return best

	def _can_extend_to_ship(self, segment, candidate, target_len):
		needed = target_len - len(segment) - 1
		if needed < 0:
			return False
		all_cells = set(segment)
		all_cells.add(candidate)
		if all(r == segment[0][0] for r, _ in all_cells):
			cols = sorted(c for _, c in all_cells)
			space = cols[0] + (self.board.size - 1 - cols[-1])
		else:
			rows = sorted(r for r, _ in all_cells)
			space = rows[0] + (self.board.size - 1 - rows[-1])
		return space >= needed

	def _normalize(self, score):
		flat_max = max((max(row) for row in score), default=0.0)
		if flat_max <= 0:
			return score
		return [[v / flat_max for v in row] for row in score]

	def get_score_grid(self):
		segments = self.board.hit_segments()
		if segments:
			return self._normalize(self._target_score_grid())
		return self._normalize(self._hunt_score_grid())

	score_grid = get_score_grid

	def get_optimal_moves(self):
		size = self.board.size
		grid = self.board.grid
		score = self.get_score_grid()
		best = -1.0
		best_cells = []
		for r in range(size):
			for c in range(size):
				if grid[r][c] != EMPTY:
					continue
				v = round(score[r][c], 6)
				if v > best:
					best = v
					best_cells = [(r, c)]
				elif v == best and v > 0:
					best_cells.append((r, c))
		if best <= 0:
			return []
		return sorted(best_cells)

	optimal_moves = get_optimal_moves
