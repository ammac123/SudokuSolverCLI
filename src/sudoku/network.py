# src/sudoku/network
from __future__ import annotations
from typing import Optional, Union
from enum import Enum

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
        self.peers: Optional[list[Cell]] = None
    
    @property
    def box(self) -> int:
        return (
            ((self.row.value - 1) // 3 * 3) +
            (((self.column.value - 1)) // 3 % 3) + 1
            )
    
    # -- Core queries --
    def is_solved(self) -> bool:
        return (self.value is not None)
    
    def candidate_count(self) -> int:
        return len(self.candidates)
    
    def only_candidate(self) -> Union[int, None]:
        if self.candidate_count() == 1:
            digit = next(iter(self.candidates))
            return digit

    def remove_candidates(self, digits: list[int]) -> set[int]:
        if self.candidates is set():
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

    # -- Dunder methods --
    def __key(self):
        return (self.row, self.column)

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self) -> str:
        return f"Cell({self.row.name}, {self.column.name}, Box: {self.box})"
    

class Unit:
    def __init__(self) -> None:
        pass



class Graph:
    def __init__(self) -> None:
        self.graph = {}
        raise NotImplementedError("Graph type class not yet implemented")
    
    def add_edge(self, u, v) -> None:
        if u not in self.graph:
            self.graph[u] = set()
        if v not in self.graph:
            self.graph[v] = set()
        self.graph[u].add(v)
        self.graph[v].add(u)
        return

    def adjacent_nodes(self, node) -> Optional[Graph]:
        if node not in self.graph:
            return None
        return self.graph[node]
    
