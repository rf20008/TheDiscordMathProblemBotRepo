from problems_module import DictConvertible


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
