import pytest

from seabattle.sea_battle_strategy import (
	EMPTY,
	FLEET_8,
	FLEET_9,
	FLEET_10,
	HIT,
	MISS,
	SUNK,
	Board,
	SeaBattleStrategy,
	fleet_for_size,
	in_bounds,
)


FLEET_10_CELLS = sum(k * v for k, v in FLEET_10.items())
FLEET_9_CELLS = sum(k * v for k, v in FLEET_9.items())
FLEET_8_CELLS = sum(k * v for k, v in FLEET_8.items())


class TestFleetConfigs:
	def test_10x10_matches_game_pigeon(self):
		assert FLEET_10 == {1: 4, 2: 2, 3: 2, 4: 1, 5: 1}
		assert FLEET_10_CELLS == 23
		assert sum(FLEET_10.values()) == 10

	def test_9x9_matches_game_pigeon(self):
		assert FLEET_9 == {3: 8}
		assert FLEET_9_CELLS == 24
		assert sum(FLEET_9.values()) == 8

	def test_8x8_matches_game_pigeon(self):
		assert FLEET_8 == {2: 2, 3: 2, 4: 1, 5: 1}
		assert FLEET_8_CELLS == 19
		assert sum(FLEET_8.values()) == 6

	def test_fleet_for_size(self):
		assert fleet_for_size(10) == FLEET_10
		assert fleet_for_size(9) == FLEET_9
		assert fleet_for_size(8) == FLEET_8
		copy = fleet_for_size(10)
		copy["test_isolation"] = 99
		assert "test_isolation" not in FLEET_10

	def test_unsupported_size_raises(self):
		with pytest.raises(ValueError):
			fleet_for_size(7)
		with pytest.raises(ValueError):
			fleet_for_size(11)


class TestInBounds:
	def test_corners(self):
		assert in_bounds(10, 0, 0)
		assert in_bounds(10, 0, 9)
		assert in_bounds(10, 9, 0)
		assert in_bounds(10, 9, 9)

	def test_out_of_bounds(self):
		assert not in_bounds(10, -1, 0)
		assert not in_bounds(10, 10, 0)
		assert not in_bounds(10, 0, -1)
		assert not in_bounds(10, 0, 10)


class TestBoard:
	def test_new_board_is_empty(self):
		board = Board(10)
		for r in range(10):
			for c in range(10):
				assert board.cell(r, c) == EMPTY
		assert board.remaining_ship_count() == 10
		assert not board.is_complete()

	def test_record_miss(self):
		board = Board(10)
		board.record_shot(3, 4, "miss")
		assert board.cell(3, 4) == MISS

	def test_record_hit(self):
		board = Board(10)
		board.record_shot(3, 4, "hit")
		assert board.cell(3, 4) == HIT

	def test_double_shot_raises(self):
		board = Board(10)
		board.record_shot(3, 4, "miss")
		with pytest.raises(ValueError):
			board.record_shot(3, 4, "miss")

	def test_out_of_bounds_raises(self):
		board = Board(10)
		with pytest.raises(ValueError):
			board.record_shot(10, 0, "miss")
		with pytest.raises(ValueError):
			board.record_shot(0, 10, "miss")
		with pytest.raises(ValueError):
			board.record_shot(-1, 0, "miss")

	def test_invalid_result_raises(self):
		board = Board(10)
		with pytest.raises(ValueError):
			board.record_shot(0, 0, "bogus")

	def test_remaining_ship_sizes(self):
		board = Board(10)
		assert board.remaining_ship_sizes() == {1, 2, 3, 4, 5}

	def test_remaining_ship_cells(self):
		board = Board(10)
		assert board.remaining_ship_cells() == FLEET_10_CELLS

	def test_clone_is_independent(self):
		board = Board(10)
		clone = board.clone()
		clone.record_shot(0, 0, "miss")
		assert board.cell(0, 0) == EMPTY
		assert clone.cell(0, 0) == MISS


class TestSink:
	def test_sink_single_cell_ship_marks_neighbors_miss(self):
		board = Board(10, {1: 1, 2: 1})
		board.record_shot(5, 5, "sunk")
		assert board.cell(5, 5) == SUNK
		assert board.fleet[1] == 0
		for dr in (-1, 0, 1):
			for dc in (-1, 0, 1):
				if dr == 0 and dc == 0:
					continue
				nr, nc = 5 + dr, 5 + dc
				assert board.cell(nr, nc) == MISS, f"neighbor ({nr},{nc}) should be MISS"

	def test_sink_attached_to_existing_hit_collects_segment(self):
		board = Board(10, {3: 1})
		board.record_shot(4, 5, "hit")
		board.record_shot(5, 5, "hit")
		board.record_shot(6, 5, "sunk")
		assert board.cell(4, 5) == SUNK
		assert board.cell(5, 5) == SUNK
		assert board.cell(6, 5) == SUNK
		assert board.fleet[3] == 0
		assert board.cell(3, 4) == MISS
		assert board.cell(7, 6) == MISS

	def test_sink_invalid_size_raises(self):
		board = Board(10, {2: 1})
		with pytest.raises(ValueError):
			board.record_shot(5, 5, "sunk")

	def test_sink_completes_game(self):
		board = Board(10, {1: 1})
		board.record_shot(0, 0, "sunk")
		assert board.is_complete()

	def test_no_touch_diagonal_marks_neighbors_miss(self):
		board = Board(10, {2: 1, 1: 1})
		board.record_shot(4, 5, "hit")
		board.record_shot(4, 6, "sunk")
		assert board.cell(3, 4) == MISS
		assert board.cell(3, 7) == MISS
		assert board.cell(5, 4) == MISS
		assert board.cell(5, 7) == MISS
		assert board.cell(3, 5) == MISS
		assert board.cell(3, 6) == MISS
		assert board.cell(5, 5) == MISS
		assert board.cell(5, 6) == MISS


class TestHitSegments:
	def test_no_hits(self):
		board = Board(10)
		assert board.hit_segments() == []

	def test_single_hit(self):
		board = Board(10)
		board.record_shot(5, 5, "hit")
		segs = board.hit_segments()
		assert segs == [[(5, 5)]]

	def test_horizontal_segment(self):
		board = Board(10)
		board.record_shot(5, 4, "hit")
		board.record_shot(5, 5, "hit")
		board.record_shot(5, 6, "hit")
		segs = board.hit_segments()
		assert len(segs) == 1
		assert sorted(segs[0]) == [(5, 4), (5, 5), (5, 6)]

	def test_disjoint_segments(self):
		board = Board(10)
		board.record_shot(1, 1, "hit")
		board.record_shot(8, 8, "hit")
		segs = board.hit_segments()
		assert len(segs) == 2


class TestStrategyFreshBoard:
	def test_fresh_10x10_moves_exist(self):
		board = Board(10)
		strategy = SeaBattleStrategy(board)
		moves = strategy.optimal_moves()
		assert len(moves) > 0
		for r, c in moves:
			assert 0 <= r < 10 and 0 <= c < 10
			assert board.cell(r, c) == EMPTY

	def test_fresh_10x10_prefers_interior(self):
		board = Board(10)
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		corner_score = max(score[0][0], score[0][9], score[9][0], score[9][9])
		interior_score = max(score[4][4], score[4][5], score[5][4], score[5][5])
		assert interior_score > corner_score

	def test_fresh_8x8_uses_parity(self):
		board = Board(8)
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert all(score[r][c] == 0.0 for r in range(8) for c in range(8) if (r + c) % 2 != 0)

	def test_fresh_9x9_uses_parity(self):
		board = Board(9)
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert all(score[r][c] == 0.0 for r in range(9) for c in range(9) if (r + c) % 3 != 0)

	def test_score_grid_shape(self):
		board = Board(10)
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert len(score) == 10
		assert all(len(row) == 10 for row in score)

	def test_score_grid_zero_at_shot_cells(self):
		board = Board(10)
		board.record_shot(3, 3, "miss")
		board.record_shot(5, 5, "hit")
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert score[3][3] == 0.0
		assert score[5][5] == 0.0


class TestStrategyNoTouch:
	def test_placement_blocked_by_miss(self):
		board = Board(10)
		board.record_shot(4, 5, "miss")
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert score[4][5] == 0.0

	def test_placement_blocked_diagonal_to_hit(self):
		board = Board(10, {1: 1, 2: 1, 3: 1, 4: 1})
		board.record_shot(4, 4, "hit")
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert score[3][3] == 0.0
		assert score[3][5] == 0.0
		assert score[5][3] == 0.0
		assert score[5][5] == 0.0


class TestStrategyTargetMode:
	def test_target_mode_picks_adjacent_to_hit(self):
		board = Board(10)
		board.record_shot(5, 5, "hit")
		strategy = SeaBattleStrategy(board)
		moves = strategy.optimal_moves()
		assert len(moves) > 0
		candidates = {(4, 5), (6, 5), (5, 4), (5, 6)}
		assert all(m in candidates for m in moves)

	def test_target_mode_continues_aligned_ship(self):
		board = Board(10, {4: 1})
		board.record_shot(5, 4, "hit")
		board.record_shot(5, 5, "hit")
		board.record_shot(5, 6, "hit")
		strategy = SeaBattleStrategy(board)
		moves = strategy.optimal_moves()
		assert moves == [(5, 3)] or moves == [(5, 7)] or moves == [(5, 3), (5, 7)]
		assert all(score >= 0 for r in range(10) for c, score in [(c, strategy.score_grid()[r][c]) for c in range(10)])

	def test_target_mode_after_full_ship_already_known(self):
		board = Board(10, {4: 1, 2: 1, 1: 1})
		board.record_shot(5, 4, "hit")
		board.record_shot(5, 5, "hit")
		board.record_shot(5, 6, "hit")
		board.record_shot(5, 7, "sunk")
		strategy = SeaBattleStrategy(board)
		moves = strategy.optimal_moves()
		assert len(moves) > 0
		for r, c in moves:
			assert (r, c) != (5, 3)
			assert (r, c) != (5, 8)


class TestStrategyProgresses:
	def test_moves_change_after_shot(self):
		board = Board(10)
		strategy = SeaBattleStrategy(board)
		first = strategy.optimal_moves()
		board.record_shot(first[0][0], first[0][1], "miss")
		second = strategy.optimal_moves()
		assert first != second

	def test_hunt_to_target_transition(self):
		board = Board(10)
		strategy = SeaBattleStrategy(board)
		hunt_moves = set(strategy.optimal_moves())
		board.record_shot(4, 4, "hit")
		target_moves = set(strategy.optimal_moves())
		assert target_moves.issubset({(3, 4), (5, 4), (4, 3), (4, 5)})
		assert target_moves != hunt_moves


class TestStrategyParity:
	def test_no_parity_when_size_1_ships_alive(self):
		board = Board(10)
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert any(score[r][c] > 0 for r in range(10) for c in range(10) if (r + c) % 2 != 0)

	def test_parity_kicks_in_when_size_1_ships_sunk(self):
		board = Board(10, {1: 0, 2: 2, 3: 2, 4: 1, 5: 1})
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert all(score[r][c] == 0.0 for r in range(10) for c in range(10) if (r + c) % 2 != 0)

	def test_only_one_parity_color_nonzero(self):
		board = Board(10, {1: 0, 2: 2, 3: 2, 4: 1, 5: 1})
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		nonzero = sum(1 for r in range(10) for c in range(10) if score[r][c] > 0)
		assert nonzero == 50


class TestSizeFiveShip:
	def test_sinking_size_5_ship_decrements_fleet(self):
		board = Board(10)
		assert board.fleet[5] == 1
		for c in range(2, 6):
			board.record_shot(2, c, "hit")
		board.record_shot(2, 6, "sunk")
		assert board.fleet[5] == 0
		assert all(board.cell(2, c) == SUNK for c in range(2, 7))

	def test_size_5_placements_enumerated(self):
		board = Board(10, {5: 1})
		strategy = SeaBattleStrategy(board)
		moves = strategy.optimal_moves()
		assert len(moves) > 0

	def test_extending_4_of_5_size_ship(self):
		board = Board(10, {5: 1})
		board.record_shot(5, 3, "hit")
		board.record_shot(5, 4, "hit")
		board.record_shot(5, 5, "hit")
		board.record_shot(5, 6, "hit")
		strategy = SeaBattleStrategy(board)
		moves = set(strategy.optimal_moves())
		assert moves.issubset({(5, 2), (5, 7)})
		assert len(moves) == 2


class TestVerifiedFleets:
	def test_8x8_opening_uses_parity_2(self):
		board = Board(8)
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert all(score[r][c] == 0.0 for r in range(8) for c in range(8) if (r + c) % 2 != 0)

	def test_9x9_opening_uses_parity_3(self):
		board = Board(9)
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert all(score[r][c] == 0.0 for r in range(9) for c in range(9) if (r + c) % 3 != 0)

	def test_10x10_opening_no_parity(self):
		board = Board(10)
		strategy = SeaBattleStrategy(board)
		moves = strategy.optimal_moves()
		assert len(moves) >= 4
		assert (4, 4) in moves
		assert (5, 5) in moves

	def test_9x9_fleet_has_8_ships(self):
		board = Board(9)
		assert board.remaining_ship_count() == 8

	def test_8x8_fleet_has_6_ships(self):
		board = Board(8)
		assert board.remaining_ship_count() == 6

	def test_10x10_fleet_has_10_ships(self):
		board = Board(10)
		assert board.remaining_ship_count() == 10


class TestStrategyMultipleSegments:
	def test_two_independent_hits(self):
		board = Board(10)
		board.record_shot(2, 2, "hit")
		board.record_shot(7, 7, "hit")
		strategy = SeaBattleStrategy(board)
		moves = set(strategy.optimal_moves())
		assert moves.issubset(
			{(1, 2), (3, 2), (2, 1), (2, 3), (6, 7), (8, 7), (7, 6), (7, 8)}
		)
		assert len(moves) > 0

	def test_target_extensions_for_singleton_only(self):
		board = Board(10, {1: 0, 2: 1, 3: 1, 4: 1})
		board.record_shot(5, 5, "hit")
		strategy = SeaBattleStrategy(board)
		moves = set(strategy.optimal_moves())
		assert moves.issubset({(4, 5), (6, 5), (5, 4), (5, 6)})
		interior = {(4, 5), (5, 4)}
		edge = {(6, 5), (5, 6)}
		assert interior.issubset(moves)
		assert not edge.intersection(moves)


class TestStrategyDeterministic:
	def test_same_input_same_output(self):
		board1 = Board(10)
		board2 = Board(10)
		board1.record_shot(3, 3, "miss")
		board2.record_shot(3, 3, "miss")
		board1.record_shot(7, 2, "hit")
		board2.record_shot(7, 2, "hit")
		s1 = SeaBattleStrategy(board1)
		s2 = SeaBattleStrategy(board2)
		assert s1.optimal_moves() == s2.optimal_moves()
		assert s1.score_grid() == s2.score_grid()


class TestFullyKnownShip:
	def test_returns_empty_when_fully_known_not_sunk(self):
		board = Board(10)
		for c in range(2, 7):
			board.grid[2][c] = HIT
		board.strategy = SeaBattleStrategy(board)
		assert SeaBattleStrategy(board).optimal_moves() == []

	def test_partial_segment_not_fully_known(self):
		board = Board(10)
		for c in range(2, 5):
			board.grid[2][c] = HIT
		moves = SeaBattleStrategy(board).optimal_moves()
		assert len(moves) > 0

	def test_fully_known_method_reports_segment(self):
		board = Board(10, {4: 1, 2: 1, 1: 1})
		for c in range(2, 6):
			board.grid[2][c] = HIT
		known = board.fully_known_ships()
		assert len(known) == 1
		segment, length = known[0]
		assert length == 4
		assert (2, 2) in segment
		assert (2, 5) in segment

	def test_partial_segment_not_fully_known_method(self):
		board = Board(10, {4: 1})
		for c in range(2, 5):
			board.grid[2][c] = HIT
		assert board.fully_known_ships() == []


class TestOpennessRanking:
	def test_candidate_with_more_open_space_scores_higher(self):
		board = Board(10, {3: 1})
		board.grid[5][5] = HIT
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		north = score[4][5]
		south = score[6][5]
		west = score[5][4]
		east = score[5][6]
		assert north > south
		assert west > east
		assert north == west
		assert south == east

	def test_openness_handles_blocked_path(self):
		board = Board(10, {3: 1})
		board.grid[5][5] = HIT
		board.grid[4][5] = MISS
		board.grid[3][5] = MISS
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert score[6][5] > score[4][5]

	def test_perpendicular_candidates_still_tied_when_openness_equal(self):
		board = Board(10, {2: 1})
		board.grid[5][5] = HIT
		strategy = SeaBattleStrategy(board)
		score = strategy.score_grid()
		assert score[4][5] == score[5][4]


class TestStableOrdering:
	def test_optimal_moves_is_sorted(self):
		board = Board(10)
		board.grid[2][2] = HIT
		board.grid[2][3] = HIT
		board.grid[2][4] = HIT
		board.grid[2][5] = HIT
		moves = SeaBattleStrategy(board).optimal_moves()
		assert moves == sorted(moves)

	def test_tied_cells_returned_in_row_major_order(self):
		board = Board(10, {2: 1})
		board.grid[5][5] = HIT
		moves = SeaBattleStrategy(board).optimal_moves()
		assert moves == sorted(moves)
		assert moves == [(4, 5), (5, 4)]
