import pytest
from dataclasses import dataclass, field
from src.sudoku.board import Board, Cell, Row, Column, Unit


def _parse_expected(s: str) -> list[list[int | None]]:
    cleaned = "".join(c for c in s if not c.isspace())
    return [
        [None if c in ".0" else int(c) for c in cleaned[i * 9:(i + 1) * 9]]
        for i in range(9)
    ]


@dataclass
class PuzzleStringTestCase:
    id: str
    puzzle_string: str
    expected_grid: list[list[int | None]] = field(init=False)

    def __post_init__(self):
        self.expected_grid = _parse_expected(self.puzzle_string)


@dataclass
class InvalidPuzzleStringTestCase:
    id: str
    puzzle_string: str
    error_type: type[Exception]


valid_cases = [
    PuzzleStringTestCase(
        id="all_zeros",
        puzzle_string="0" * 81,
    ),
    PuzzleStringTestCase(
        id="all_dots",
        puzzle_string="." * 81,
    ),
    PuzzleStringTestCase(
        id="fully_solved",
        puzzle_string="534678912672195348198342567859761423426853791713924856961537284287419635345286179",
    ),
    PuzzleStringTestCase(
        id="partial_with_zeros",
        puzzle_string="530070000600195000098000060800060003400803001700020006060000280000419005000080079",
    ),
    PuzzleStringTestCase(
        id="partial_with_dots",
        puzzle_string="53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
    ),
    PuzzleStringTestCase(
        id="mixed_zeros_and_dots",
        puzzle_string="5300700006001950000980000608000600034008030017000200060600002800004190050000800.9",
    ),
    PuzzleStringTestCase(
        id="single_given_top_left",
        puzzle_string="5" + "0" * 80,
    ),
    PuzzleStringTestCase(
        id="single_given_bottom_right",
        puzzle_string="0" * 80 + "9",
    ),
    PuzzleStringTestCase(
        id="whitespace_between_rows",
        puzzle_string=(
            "530070000\n"
            "600195000\n"
            "098000060\n"
            "800060003\n"
            "400803001\n"
            "700020006\n"
            "060000280\n"
            "000419005\n"
            "000080079\n"
        ),
    ),
    PuzzleStringTestCase(
        id="whitespace_with_spaces",
        puzzle_string=(
            "530 070 000 "
            "600 195 000 "
            "098 000 060 "
            "800 060 003 "
            "400 803 001 "
            "700 020 006 "
            "060 000 280 "
            "000 419 005 "
            "000 080 079"
        ),
    ),
    PuzzleStringTestCase(
        id="first_row_given_rest_empty",
        puzzle_string="123456789" + "0" * 72,
    ),
    PuzzleStringTestCase(
        id="last_row_given_rest_empty",
        puzzle_string="0" * 72 + "123456789",
    ),
]

invalid_cases = [
    InvalidPuzzleStringTestCase(
        id="too_short",
        puzzle_string="123",
        error_type=ValueError,
    ),
    InvalidPuzzleStringTestCase(
        id="too_long",
        puzzle_string="0" * 82,
        error_type=ValueError,
    ),
    InvalidPuzzleStringTestCase(
        id="empty_string",
        puzzle_string="",
        error_type=ValueError,
    ),
    InvalidPuzzleStringTestCase(
        id="invalid_char_letter",
        puzzle_string="x" * 81,
        error_type=ValueError,
    ),
    InvalidPuzzleStringTestCase(
        id="invalid_char_mixed_in",
        puzzle_string="53007000060019500009800006080006000340080300170002000606000028000041900500008007x",
        error_type=ValueError,
    ),
]


class TestPuzzleStringParsing:
    @pytest.mark.parametrize("case", valid_cases, ids=[c.id for c in valid_cases])
    def test_valid_puzzle_parses_correctly(self, case: PuzzleStringTestCase):
        board = Board(case.puzzle_string)
        actual = [
            [cell.value for cell in row]
            for row in board.cells
        ]
        assert actual == case.expected_grid

    @pytest.mark.parametrize("case", valid_cases, ids=[c.id for c in valid_cases])
    def test_valid_puzzle_has_81_cells(self, case: PuzzleStringTestCase):
        board = Board(case.puzzle_string)
        assert sum(len(row) for row in board.cells) == 81

    @pytest.mark.parametrize("case", invalid_cases, ids=[c.id for c in invalid_cases])
    def test_invalid_puzzle_raises(self, case: InvalidPuzzleStringTestCase):
        with pytest.raises(case.error_type):
            Board(case.puzzle_string)


class TestCell:
    def test_cell_has_full_candidates_when_no_value(self):
        cell = Cell(Row.R1, Column.C1)
        assert cell.candidates == set(range(1, 10))

    def test_cell_has_no_candidates_when_given_value(self):
        cell = Cell(Row.R1, Column.C1, value=5)
        assert cell.candidates == set()

    def test_cell_remove_candidates_when_no_remaining_candidates(self):
        cell = Cell(Row.R1, Column.C1, value=5)
        removed_candidates = cell.remove_candidates([4])
        assert cell.candidates == set()
        assert removed_candidates == set()

    def test_is_solved_false_when_no_value(self):
        cell = Cell(Row.R1, Column.C1)
        assert not cell.is_solved()

    def test_is_solved_true_when_value_set(self):
        cell = Cell(Row.R1, Column.C1, value=3)
        assert cell.is_solved()

    def test_box_calculation(self):
        # R1C1 → box 1, R1C4 → box 2, R4C1 → box 4
        assert Cell(Row.R1, Column.C1).box == 1
        assert Cell(Row.R1, Column.C4).box == 2
        assert Cell(Row.R4, Column.C1).box == 4

    def test_remove_candidates(self):
        cell = Cell(Row.R1, Column.C1)
        removed = cell.remove_candidates([1, 2, 3])
        assert removed == {1, 2, 3}
        assert 1 not in cell.candidates

    def test_remove_candidate_that_does_not_exist(self):
        cell = Cell(Row.R1, Column.C1)
        cell.remove_candidates([1, 2, 3])
        removed_again = cell.remove_candidates([1, 2, 3])
        assert removed_again == set()
        assert 1 not in cell.candidates

    def test_set_value_clears_candidates(self):
        cell = Cell(Row.R1, Column.C1)
        cell.set_value(7)
        assert cell.value == 7
        assert cell.candidates == set()

    def test_only_candidate_returns_digit_when_one_left(self):
        cell = Cell(Row.R1, Column.C1)
        cell.candidates = {4}
        assert cell.only_candidate() == 4

    def test_only_candidate_returns_none_when_multiple(self):
        cell = Cell(Row.R1, Column.C1)
        assert cell.only_candidate() is None

    def test_key_returns_tuple(self):
        cell = Cell(Row.R7, Column.C3)
        expected = (Row.R7, Column.C3)
        assert cell.__key__() == expected

    def test_key_hashed_correctly(self):
        cell = Cell(Row.R7, Column.C3)
        expected = hash((Row.R7, Column.C3))
        assert cell.__hash__() == expected

    def test_hash_equal_for_same_position(self):
        cell_a = Cell(Row.R3, Column.C5)
        cell_b = Cell(Row.R3, Column.C5)
        assert hash(cell_a) == cell_b.__hash__()

    def test_hash_differs_for_different_positions(self):
        cell_a = Cell(Row.R1, Column.C1)
        cell_b = Cell(Row.R1, Column.C2)
        assert hash(cell_a) != cell_b.__hash__()

    def test_repr(self):
        cell = Cell(Row.R2, Column.C4)
        assert repr(cell) == "Cell(R2, C4, Box: 2)"


class TestUnit:
    def _make_unit(self, values: list[int | None]) -> Unit:
        """Build a row Unit from a 9-element list of int|None."""
        cells = [
            Cell(Row(i + 1), Column.C1, value=v)
            for i, v in enumerate(values)
        ]
        return Unit('row', 1, cells)

    def test_stores_type_index_and_cells(self):
        unit = self._make_unit([None] * 9)
        assert unit.type == 'row'
        assert unit.index == 1
        assert len(unit.cells) == 9

    # --- unsolved_cells ---

    def test_unsolved_cells_all_when_none_solved(self):
        unit = self._make_unit([None] * 9)
        assert len(unit.unsolved_cells) == 9

    def test_unsolved_cells_excludes_solved_cells(self):
        unit = self._make_unit([1, 2, None, None, None, None, None, None, None])
        assert len(unit.unsolved_cells) == 7

    def test_unsolved_cells_empty_when_all_solved(self):
        unit = self._make_unit([1, 2, 3, 4, 5, 6, 7, 8, 9])
        assert unit.unsolved_cells == []

    # --- missing_digits ---

    def test_missing_digits_all_when_no_values(self):
        unit = self._make_unit([None] * 9)
        assert unit.missing_digits == set(range(1, 10))

    def test_missing_digits_excludes_placed_values(self):
        unit = self._make_unit([1, 2, 3, None, None, None, None, None, None])
        assert unit.missing_digits == {4, 5, 6, 7, 8, 9}

    def test_missing_digits_empty_when_fully_solved(self):
        unit = self._make_unit([1, 2, 3, 4, 5, 6, 7, 8, 9])
        assert unit.missing_digits == set()

    def test_missing_digits_single_missing(self):
        unit = self._make_unit([1, 2, 3, 4, 5, 6, 7, 8, None])
        assert unit.missing_digits == {9}

    # --- cells_with_candidates ---

    def test_cells_with_candidates_returns_empty_when_digit_already_placed(self):
        unit = self._make_unit([5, None, None, None, None, None, None, None, None])
        assert unit.cells_with_candidates(5) == []

    def test_cells_with_candidates_returns_cells_that_have_candidate(self):
        unit = self._make_unit([None] * 9)
        # all unsolved cells start with full candidate sets
        result = unit.cells_with_candidates(3)
        assert len(result) == 9
        assert all(3 in cell.candidates for cell in result)

    def test_cells_with_candidates_excludes_cells_missing_that_candidate(self):
        unit = self._make_unit([None] * 9)
        unit.cells[0].candidates.discard(7)
        unit.cells[1].candidates.discard(7)
        result = unit.cells_with_candidates(7)
        assert len(result) == 7
        assert unit.cells[0] not in result
        assert unit.cells[1] not in result

    def test_cells_with_candidates_empty_when_no_unsolved_cells_have_candidate(self):
        unit = self._make_unit([None] * 9)
        for cell in unit.cells:
            cell.candidates.discard(4)
        assert unit.cells_with_candidates(4) == []

    # --- candidate_locations ---

    def test_candidate_locations_keys_are_missing_digits(self):
        unit = self._make_unit([1, 2, 3, None, None, None, None, None, None])
        locations = unit.candidate_locations()
        assert set(locations.keys()) == {4, 5, 6, 7, 8, 9}

    def test_candidate_locations_empty_when_fully_solved(self):
        unit = self._make_unit([1, 2, 3, 4, 5, 6, 7, 8, 9])
        assert unit.candidate_locations() == {}

    def test_candidate_locations_values_are_lists_of_cells(self):
        unit = self._make_unit([None] * 9)
        locations = unit.candidate_locations()
        for digit, cells in locations.items():
            assert isinstance(cells, list)
            assert all(digit in cell.candidates for cell in cells)


class TestBoard:
    def test_empty_board_has_81_cells(self):
        board = Board()
        assert sum(len(row) for row in board.cells) == 81

    def test_board_has_9_rows_columns_boxes(self):
        board = Board()
        assert len(board.rows) == 9
        assert len(board.columns) == 9
        assert len(board.boxes) == 9

    def test_parse_raises_on_wrong_length(self):
        with pytest.raises(ValueError):
            Board("123")

    def test_parse_raises_on_invalid_char(self):
        with pytest.raises(ValueError):
            Board("x" * 81)

    def test_given_values_parsed_correctly(self):
        puzzle = "5" + "0" * 80
        board = Board(puzzle)
        assert board.cells[0][0].value == 5
        assert board.cells[0][1].value is None

    def test_dots_parsed_as_empty(self):
        puzzle = "." * 81
        board = Board(puzzle)
        assert all(cell.value is None for row in board.cells for cell in row)

    # --- _network_cell_peers ---

    def test_network_cell_peers_sets_units_on_every_cell(self):
        board = Board()
        board._network_cell_peers()
        for row in board.cells:
            for cell in row:
                assert cell.units is not None
                assert len(cell.units) == 3

    def test_network_cell_peers_correct_unit_types(self):
        board = Board()
        board._network_cell_peers()
        cell = board.cells[0][0]
        assert cell.units is not None
        types = [u.type for u in cell.units]
        assert types == ['row', 'column', 'box']

    def test_network_cell_peers_each_cell_has_20_peers(self):
        board = Board()
        board._network_cell_peers()
        for row in board.cells:
            for cell in row:
                assert cell.peers is not None
                assert len(cell.peers) == 20

    def test_network_cell_peers_cell_not_in_own_peers(self):
        board = Board()
        board._network_cell_peers()
        for row in board.cells:
            for cell in row:
                assert cell.peers is not None
                assert cell not in cell.peers

    # --- _propogate_given_values ---

    def test_propogate_given_values_removes_candidate_from_peers(self):
        board = Board("5" + "0" * 80)
        board._network_cell_peers()
        board._propogate_given_values()
        given_cell = board.cells[0][0]
        assert given_cell.peers is not None
        for peer in given_cell.peers:
            assert 5 not in peer.candidates

    def test_propogate_given_values_does_not_affect_unrelated_cells(self):
        board = Board("5" + "0" * 80)
        board._network_cell_peers()
        board._propogate_given_values()
        # a cell in row 9, col 9 (box 9) shares no unit with R1C1
        unrelated = board.cells[8][8]
        assert 5 in unrelated.candidates

    def test_propogate_given_values_does_not_alter_given_cell_itself(self):
        board = Board("5" + "0" * 80)
        board._network_cell_peers()
        board._propogate_given_values()
        given_cell = board.cells[0][0]
        assert given_cell.value == 5
        assert given_cell.candidates == set()
