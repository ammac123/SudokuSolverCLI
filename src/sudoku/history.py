from src.sudoku.board import Cell
from src.algorithms import AvailableTechniques
from typing import Literal
from dataclasses import dataclass

Digit = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]


@dataclass
class Step:
    technique: AvailableTechniques
    difficulty: int
    placements: list[tuple[Cell, Digit]]
    eliminations: list[tuple[Cell, Digit]]
    reason_cells: list[Cell]


class History:
    def __init__(self) -> None:
        self._undo_stack: list[Step] = []
        self._redo_stack: list[Step] = []

    def record(self, step: Step) -> None:
        self._undo_stack.append(step)
        self._redo_stack.clear()

    def undo(self) -> Step | None:
        if not self._undo_stack:
            return None
        step = self._undo_stack.pop()
        self._redo_stack.append(step)
        return step

    def redo(self) -> Step | None:
        if not self._redo_stack:
            return None
        step = self._redo_stack.pop()
        self._undo_stack.append(step)
        return step

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    @property
    def path(self) -> list[Step]:
        return list(self._undo_stack)

    def __len__(self) -> int:
        return len(self._undo_stack)