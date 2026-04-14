# src/sudoku/board
from __future__ import annotations
from typing import Optional, Union, Literal
from enum import Enum

UNITTYPE = Literal['row', 'column', 'box']

class Row(Enum):
    R1 = 1; R2 = 2; R3 = 3
    R4 = 4; R5 = 5; R6 = 6
    R7 = 7; R8 = 8; R9 = 9

class Column(Enum):
    C1 = 1; C2 = 2; C3 = 3
    C4 = 4; C5 = 5; C6 = 6
    C7 = 7; C8 = 8; C9 = 9

class Cell:
    def __init__(self, row: Row, column: Column, value: Optional[int] = None) -> None:
        self.row = row
        self.column = column
        self.value = value
        self.candidates: set[int] = set(range(1,10)) if value is None else set()
        self.is_given = value is not None
        self.units: Optional[list[Unit]] = None
        self.peers: Optional[set[Cell]] = None

    @property
    def box(self) -> int:
        return (
            ((self.row.value - 1) // 3 * 3) +
            (((self.column.value - 1)) // 3 % 3) + 1
            )

    def is_solved(self) -> bool:
        return (self.value is not None)

    def candidate_count(self) -> int:
        return len(self.candidates)

    def only_candidate(self) -> Union[int, None]:
        if self.candidate_count() == 1:
            digit = next(iter(self.candidates))
            return digit
        return

    def remove_candidates(self, digits: list[int]) -> set[int]:
        if self.candidates == set():
            return set()
        removed = set()
        for digit in digits:
            if digit in self.candidates:
                self.candidates.remove(digit)
                removed.add(digit)
        return removed

    def set_value(self, digit):
        self.value = digit
        self.candidates.clear()

    def __key__(self):
        return (self.row, self.column)

    def __hash__(self):
        return hash(self.__key__())

    def __repr__(self) -> str:
        return f"Cell({self.row.name}, {self.column.name}, Box: {self.box})"


class Unit:
    def __init__(self, unit_type: UNITTYPE, index: int, cells: list[Cell]) -> None:
        self.type = unit_type
        self.index = index
        self.cells = cells

    @property
    def unsolved_cells(self) -> list[Cell]:
        return [
            cell for cell in self.cells
            if not cell.is_solved()
            ]

    @property
    def missing_digits(self) -> set[int]:
        digits = set(range(1,10))
        for cell in self.cells:
            if cell.is_solved() and cell.value is not None:
                digits.remove(cell.value)
        return digits

    def cells_with_candidates(self, d: int) -> list[Cell]:
        if d not in self.missing_digits:
            return []
        return [
            cell for cell in self.unsolved_cells
            if d in cell.candidates
        ]

    def candidate_locations(self) -> dict[int, list[Cell]]:
        candidate_map = {}
        for digit in self.missing_digits:
            candidates = self.cells_with_candidates(digit)
            candidate_map[digit] = candidates
        return candidate_map


class Board:
    def __init__(self, puzzle: Optional[str] = None) -> None:
        self.cells: list[list[Cell]] = self._build_cells(puzzle)
        
        self.rows: list[Unit] = self._build_rows()
        self.columns: list[Unit] = self._build_columns()
        self.boxes: list[Unit] = self._build_boxes()


    @staticmethod
    def _parse(puzzle: Optional[str]) -> list[list[Optional[int]]]:
        if puzzle is None:
            return [[None] * 9 for _ in range(9)]
        cleaned_puzzle = "".join(char for char in puzzle if not char.isspace())
        if len(cleaned_puzzle) != 81:
            raise ValueError(f"Puzzle must be 81 cells, got {len(cleaned_puzzle)} instead")
        values: list[Optional[int]] = []
        for char in cleaned_puzzle:
            if char in ".0":
                values.append(None)
            elif char.isdigit():
                values.append(int(char))
            else:
                raise ValueError(F"Unexpected value in puzzle: {char!r}")
        return [values[i * 9 : (i + 1) * 9] for i in range(9)]


    def _build_cells(self, puzzle: Optional[str]) -> list[list[Cell]]:
        cell_values = self._parse(puzzle)
        rows, columns = list(Row), list(Column)
        return [
            [Cell(rows[r], columns[c], value=cell_values[r][c]) for c in range(9)]
            for r in range(9)
        ]

    def _build_rows(self) -> list[Unit]:
        return [Unit('row', i+1, list(self.cells[i])) for i in range(9)]

    def _build_columns(self) -> list[Unit]:
        return [Unit('column', i+1, [self.cells[r][i] for r in range(9)]) 
                for i in range(9)]
    
    def _build_boxes(self) -> list[Unit]:
        boxes: list[Unit] = []
        for b in range(1,10):
            members = [
                self.cells[r][c]
                for r in range(9) for c in range(9)
                if self.cells[r][c].box == b
            ]
            boxes.append(Unit('box', b, members))
        return boxes
    
    def _network_cell_peers(self) -> None:
        for r in range(9):
            for c in range(9):
                cell = self.cells[r][c]
                cell.units = [
                    self.rows[r],
                    self.columns[c],
                    self.boxes[cell.box - 1],
                ]
                peers: set[Cell] = set()
                for unit in cell.units:
                    peers.update(unit.cells)
                peers.discard(cell)
                cell.peers = peers

    def _propogate_given_values(self) -> None:
        for row in self.cells:
            for cell in row:
                if cell.is_given and cell.value is not None and cell.peers:
                    for peer in cell.peers:
                        peer.remove_candidates([cell.value])
                        