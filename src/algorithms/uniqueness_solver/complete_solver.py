from __future__ import annotations
from enum import Enum
import argparse
import textwrap
import time


class SolutionStatus(Enum):
    NO_SOLUTION = 0
    UNIQUE_SOLUTION = 1
    MULTIPLE_SOLUTIONS = 2

def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1e3
        return res, elapsed_ms
    return wrapper

class Node:
    __slots__ = ('left', 'right', 'up', 'down', 'column', 'row_id')
    
    def __init__(self, column: 'ColumnHeader', row_id=None) -> None:
        self.left: Node = self
        self.right: Node = self
        self.up: Node = self
        self.down: Node = self
        self.column: ColumnHeader = column #type: ignore
        self.row_id = row_id


class ColumnHeader(Node):
    __slots__ = ('size', 'name')

    def __init__(self, name) -> None:
        self.left: Node = self
        self.right: Node = self
        self.up: Node = self
        self.down: Node = self
        self.column = self #type: ignore
        self.row_id = None
        self.size = 0
        self.name = name
        self.column = self
    
    def __repr__(self) -> str:
        return f"Col({self.name}, size: {self.size})"

def _parse(puzzle: str) -> list[list[int]]:
    if puzzle is None:
        return [[None] * 9 for _ in range(9)]
    cleaned_puzzle = "".join(char for char in puzzle if not char.isspace())
    if len(cleaned_puzzle) != 81:
        raise ValueError(f"Puzzle must be 81 cells, got {len(cleaned_puzzle)} instead")
    values: list[int] = []
    for char in cleaned_puzzle:
        if char in ".0":
            values.append(None) #type: ignore
        elif char.isdigit():
            values.append(int(char))
        else:
            raise ValueError(F"Unexpected value in puzzle: {char!r}")
    return [values[i * 9 : (i + 1) * 9] for i in range(9)]


def _column_name(i):
    if i < 81:
        r, c = divmod(i, 9)
        return f"cell({r},{c})"
    elif i < 162:
        i -= 81
        r, d = divmod(i, 9)
        return f"row{r}-digit{d+1}"
    elif i < 243:
        i -= 162
        c, d = divmod(i, 9)
        return f"col{c}-digit{d+1}"
    else:
        i -= 243
        b, d = divmod(i, 9)
        return f"box{b}-digit{d+1}"

def _construct_columns():
    root = ColumnHeader("root")
    columns: list[ColumnHeader] = [None] * 324 #type: ignore
    for i in range(324):
        col = ColumnHeader(name=_column_name(i))
        columns[i] = col

        col.right = root
        col.left = root.left
        root.left.right = col
        root.left = col
    return root, columns

def build_matrix(puzzle: list[list[int]], columns: list[ColumnHeader]):
    for row in range(9):
        box_row = (row // 3) * 3
        row_base = row * 9
        row_constraint_base = 81 + row_base
        for col in range(9):
            cell_val = puzzle[row][col]
            digits = (cell_val,) if cell_val is not None else [i for i in range(1,10)]

            box = box_row + (col // 3)
            cell_col = columns[row_base + col]
            col_constraint_base = 162 + col * 9
            box_constraint_base = 243 + box * 9

            for d in digits:
                d0 = d - 1
                row_id = (row, col, d)

                c0 = cell_col
                c1 = columns[row_constraint_base + d0]
                c2 = columns[col_constraint_base + d0]
                c3 = columns[box_constraint_base + d0]
                
                row_nodes: list[Node] = []
                for ch in (c0, c1, c2, c3):
                    node = Node(row_id=row_id, column=ch)
                    up = ch.up
                    node.down = ch
                    node.up = up
                    up.down = node
                    ch.up = node
                    ch.size += 1

                    row_nodes.append(node)

                n0, n1, n2, n3 = row_nodes
                n0.right = n1; n1.left = n0
                n1.right = n2; n2.left = n1
                n2.right = n3; n3.left = n2
                n3.right = n0; n0.left = n3

    return columns

def cover(col: ColumnHeader):
    # Remove column from header list
    col.right.left = col.left
    col.left.right = col.right

    # For each row that satisfies this constraint...
    row_node = col.down
    while row_node is not col:
        # ...remove all other nodes in that row from their columns
        right_node = row_node.right
        while right_node is not row_node:
            right_node.down.up = right_node.up
            right_node.up.down = right_node.down
            right_node.column.size -= 1
            right_node = right_node.right
        row_node = row_node.down


def uncover(col: ColumnHeader):
    # Exact reverse of cover — bottom to top, right to left
    row_node = col.up
    while row_node is not col:
        left_node = row_node.left
        while left_node is not row_node:
            left_node.column.size += 1
            left_node.down.up = left_node
            left_node.up.down = left_node
            left_node = left_node.left
        row_node = row_node.up

    # Restore column into header list
    col.right.left = col
    col.left.right = col

def choose_column(root: ColumnHeader) -> ColumnHeader:
    best: ColumnHeader | None = None
    col = root.right
    while col is not root:
        if best is None or col.size < best.size: #type: ignore
            best = col #type: ignore
            if best.size <= 1:
                return best #type: ignore
        col = col.right
    return best #type: ignore


def search(root: ColumnHeader, solution: list, results: list, limit=2):
    if root.right is root:
        results.append(list(solution))
        return
    
    col = choose_column(root)

    if col.size == 0:
        return
    
    cover(col)

    row_node = col.down
    while row_node is not col:
        if len(results) >= limit:
            break
        solution.append(row_node.row_id)

        right_node = row_node.right
        while right_node is not row_node:
            cover(right_node.column)
            right_node = right_node.right
        
        search(root, solution, results, limit)
        
        solution.pop()

        left_node = row_node.left
        while left_node is not row_node:
            uncover(left_node.column)
            left_node = left_node.left

        row_node = row_node.down

    uncover(col)

def decode(solution):
    grid = [[0]*9 for _ in range(9)]
    for (r, c, d) in solution:
        grid[r][c] = d
    return grid

def check_unique(puzzle):
    """Returns True if puzzle has exactly one solution."""
    root, columns = _construct_columns()
    build_matrix(puzzle, columns)

    results = []
    search(root, [], results, limit=2)
    return len(results) == 1

def solve(puzzle, limit=2):
    givens = [row[:] for row in puzzle]
    root, columns = _construct_columns()
    build_matrix(puzzle, columns)

    results = []
    solution = None
    status = SolutionStatus(0)
    search(root, [], results, limit)

    if len(results) == 1:
        status = SolutionStatus(1)
        solution = decode(results[0])
    if len(results) >= 2:
        status = SolutionStatus(2)
        solution = decode(results[0])
    
    return solution, givens, status
    

GIVEN  = "\033[1;33m"
SOLVED = "\033[0;37m"
DIM    = "\033[2;37m"
RESET  = "\033[0m"

def display_grid(grid, givens, status, elapsed_ms=None):
    if status == SolutionStatus.NO_SOLUTION:
        grid = givens
    givens = list(map(lambda sub: list(map(lambda cell: cell or 0, sub)), givens))
    
    top    = f"{DIM}┌───────┬───────┬───────┐{RESET}"
    middle = f"{DIM}├───────┼───────┼───────┤{RESET}"
    bottom = f"{DIM}└───────┴───────┴───────┘{RESET}"

    lines = ["",   
            *([ f"{GIVEN}Puzzle does not have a unique solution!{RESET}", ""]
            if status == SolutionStatus.MULTIPLE_SOLUTIONS
            else []
            ),
            top]

    for r in range(9):
        row = f"{DIM}│ {RESET}"
        for c in range(9):
            colour = GIVEN if (givens[r][c] != 0) else SOLVED
            row += f"{colour}{grid[r][c] or ' '}{RESET}"
            row += f"{DIM} │ {RESET}" if (c + 1) % 3 == 0 else " "
        lines.append(row)
        if r in (2, 5):
            lines.append(middle)

    lines.append(bottom)

    total_givens = sum(givens[r][c] != 0 for r in range(9) for c in range(9))
    total_solved = 81 - total_givens if (status != SolutionStatus.NO_SOLUTION) else "No solution"
    lines += [
        "",
        f"{DIM}Givens :{RESET} {GIVEN}{total_givens}{RESET}",
        f"{DIM}Solved :{RESET} {SOLVED}{total_solved}{RESET}",
        *([ f"{DIM}Time   :{RESET} {elapsed_ms:.3f} ms"] 
          if elapsed_ms is not None and status != SolutionStatus.NO_SOLUTION
          else []
          ),
        "",
    ]

    print(textwrap.indent("\n".join(lines), "\t"))


def main():
    parser = argparse.ArgumentParser(description="Sudoku Solver")
    parser.add_argument("puzzle_string", type=str, help="Puzzle string (in '123...64 etc.' or '12300064' style format)")
    parser.add_argument("-u", "--unique-solution", action="store_true", help="Will check if solution, if found, is unique.")
    args = parser.parse_args()
    try:
        puzzle = _parse(args.puzzle_string)
        limit = 2 if args.unique_solution else 1
    except ValueError as e:
        print(f"\n{e}")
        print(f"Exiting...\n")
        exit(1)

    (solution, givens, status), elapsed_time = timeit(solve)(puzzle, limit) #type: ignore
    display_grid(solution, givens, status, elapsed_time)

if __name__=="__main__":
    main()