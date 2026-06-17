from problems_module import DictConvertible
import random
import copy
class SudokuBoard(DictConvertible):
    N = 3
    row_bit_board: list[int]
    col_bit_board: list[int]
    box_bit_board: list[int]
    board: list[list[int]]

    def __init__(self, board: list[str] | list[list[int]] | None) -> None:
        if board is None:
            board = [[0 for _ in range(9)] for _ in range(9)]
        if isinstance(board, str):
            board = list(map(int, board.split()))
        if not isinstance(board, (list, tuple)):
            raise TypeError("board must be a list or a string")
        self.board = board
        self.size = int(len(board) ** 0.5)
        if self.size**2 != len(board):
            raise ValueError("Board's size must be square")
        if not all(len(row) == self.size for row in board):
            raise ValueError("board must be square")
        self.initialize_bitboards()

    def initialize_bitboards(self):
        self.row_bit_board = [0 for _ in range(self.size**2)]
        self.col_bit_board = [0 for _ in range(self.size**2)]
        self.box_bit_board = [0 for _ in range(self.size**2)]
        for row in range(self.size**2):
            for col in range(self.size**2):
                if (
                    self.row_bit_board[row] & (1 << self.board[row][col])
                    and self.board[row][col] != 0
                ):
                    raise ValueError(
                        f"sudoku rule violation detected: 2 instances of {self.board[row][col]} in row {row + 1}"
                    )
                self.row_bit_board[row] |= 1 << self.board[row][col]
        for col in range(self.size**2):
            for row in range(self.size**2):
                if (
                    self.col_bit_board[col] & (1 << self.board[row][col])
                    and self.board[row][col] != 0
                ):
                    raise ValueError(
                        f"sudoku rule violation detected: 2 instances of {self.board[row][col]} in column {col+1}"
                    )
                self.col_bit_board[col] |= 1 << self.board[row][col]
        # init box board
        for boxnum in range(self.size**2):
            boxrow, boxcol = self.get_boxrowcol(boxnum)
            for row in range(self.size):
                for col in range(self.size):
                    x = self.size * boxrow + row
                    y = self.size * boxcol + col
                    if (
                        self.box_bit_board[boxnum] & (1 << self.board[x][y])
                        and self.board[x][y] != 0
                    ):
                        raise ValueError(
                            f"Sudoku rule violation detected: 2 instances of {self.board[x][y]} in box {boxnum}"
                        )
                    self.box_bit_board[boxnum] |= 1 << self.board[x][y]

    def get_boxrowcol(self, boxnum: int) -> tuple[int, int]:
        return boxnum // self.size, boxnum % self.size

    def find_empty(self, raise_if_none_found = False) -> tuple[int, int] | None:
        for r in range(self.size ** 2):
            for c in range(self.size ** 2):
                if self.board[r][c] == 0:
                    return r, c
        if raise_if_none_found:
            raise ValueError("No empty cell found")
        return None

    def is_valid(self, r: int, c: int, val: int) -> bool:
        boxnum = (r // self.size) * self.size + (c // self.size)
        bit = 1 << val

        return (
                (self.row_bit_board[r] & bit) == 0
                and (self.col_bit_board[c] & bit) == 0
                and (self.box_bit_board[boxnum] & bit) == 0
        )

    def place(self, r: int, c: int, val: int) -> "SudokuBoard":
        new = self.copy()

        new.board[r][c] = val

        bit = 1 << val
        boxnum = (r // new.size) * new.size + (c // new.size)

        new.row_bit_board[r] |= bit
        new.col_bit_board[c] |= bit
        new.box_bit_board[boxnum] |= bit

        return new

    def remove(self, r: int, c: int, val: int) -> "SudokuBoard":
        new = self.copy()

        new.board[r][c] = 0

        bit = 1 << val
        boxnum = (r // new.size) * new.size + (c // new.size)

        new.row_bit_board[r] &= ~bit
        new.col_bit_board[c] &= ~bit
        new.box_bit_board[boxnum] &= ~bit

        return new

    def count_candidates(self, r: int, c: int) -> int:
        boxnum = (r // self.size) * self.size + (c // self.size)

        used = (
                self.row_bit_board[r]
                | self.col_bit_board[c]
                | self.box_bit_board[boxnum]
        )

        n = self.size ** 2

        # mask of valid digits: bits 1..n set
        full_mask = (1 << (n + 1)) - 2  # removes bit 0

        available = full_mask & ~used

        return available.bit_count()

    def find_best_cell_mrv(self) -> tuple[int, int] | None:
        best = None
        best_count = 10 ** 9

        for r in range(self.size ** 2):
            for c in range(self.size ** 2):
                if self.board[r][c] == 0:
                    cnt = self.count_candidates(r, c)

                    if cnt == 0:
                        return (r, c)  # dead cell → prune immediately

                    if cnt < best_count:
                        best_count = cnt
                        best = (r, c)

                        if best_count == 1:
                            return best  # can't do better than this

        return best
    def solve(self) -> "SudokuBoard | None":
        def backtrack(board: "SudokuBoard") -> "SudokuBoard | None":
            cell = board.find_best_cell_mrv()
            if cell is None:
                return board

            r, c = cell

            for val in range(1, board.size ** 2 + 1):
                if board.is_valid(r, c, val):
                    result = backtrack(board.place(r, c, val))
                    if result is not None:
                        return result

            return None

        return backtrack(self.copy())
    @classmethod
    def generate_full_board(cls, size: int) -> "SudokuBoard":
        board = cls([[0 for _ in range(size**2)] for _ in range(size**2)])

        nums = list(range(1, size**2 + 1))

        def backtrack(b: SudokuBoard) -> SudokuBoard | None:
            cell = b.find_empty()
            if cell is None:
                return b  # fully filled

            r, c = cell
            random.shuffle(nums)

            for val in nums:
                if b.is_valid(r, c, val):
                    result = backtrack(b.place(r, c, val))
                    if result is not None:
                        return result

            return None

        return backtrack(board)

    def copy(self) -> "SudokuBoard":
        return SudokuBoard(copy.deepcopy(self.board))
    def to_dict(self) -> dict:
        return {"board": self.board}
    @classmethod
    def from_dict(cls, data: dict) -> "SudokuBoard":
        return cls(data["board"])