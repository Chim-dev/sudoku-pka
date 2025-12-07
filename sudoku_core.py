import math
from typing import List, Tuple, Optional

EMPTY = 0  # sel kosong

def block_size(n: int) -> int:
    return int(math.isqrt(n))  # 9 -> 3, 25 -> 5

def parse_puzzle(lines: List[str]) -> List[List[int]]:
    """
    Mendukung dua format:
    - 9x9 lama: 9 karakter per baris, misal '530070000'
    - N x N baru: N angka per baris dipisah whitespace, misal '0 0 12 6 ...'
      (whitespace bisa spasi atau tab, split() akan tangani semua).
    0 / '.' / '*' dianggap kosong.
    """
    n = len(lines)
    board: List[List[int]] = []

    for row in lines:
        row = row.strip()
        if not row:
            continue

        # Pisah berdasarkan whitespace (spasi/tab, dll)
        tokens = row.split()  # split() default pakai semua whitespace [web:164][web:166][web:168]

        if len(tokens) == n and len(tokens) > 1:
            # Format angka-per-token (25x25, 16x16, dll)
            nums: List[int] = []
            for tok in tokens:
                if tok in ("0", ".", "*"):
                    nums.append(EMPTY)
                else:
                    nums.append(int(tok))
            board.append(nums)
        elif len(row) == n:
            # Format karakter-per-sel (9x9 klasik)
            nums: List[int] = []
            for ch in row:
                if ch in (".", "0", "*"):
                    nums.append(EMPTY)
                else:
                    nums.append(int(ch))
            board.append(nums)
        else:
            raise ValueError(
                f"Row format not recognized: expected {n} tokens or {n} chars, "
                f"got {len(tokens)} tokens and {len(row)} chars. Row={repr(row)}"
            )

    return board


def is_valid(board: List[List[int]], r: int, c: int, val: int) -> bool:
    n = len(board)
    b = block_size(n)
    for j in range(n):
        if board[r][j] == val:
            return False
    for i in range(n):
        if board[i][c] == val:
            return False
    br = (r // b) * b
    bc = (c // b) * b
    for i in range(br, br + b):
        for j in range(bc, bc + b):
            if board[i][j] == val:
                return False
    return True

def find_empty(board: List[List[int]]) -> Optional[Tuple[int, int]]:
    n = len(board)
    for i in range(n):
        for j in range(n):
            if board[i][j] == EMPTY:
                return i, j
    return None

def clone_board(board: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in board]
def print_board(board: List[List[int]]) -> None:
    n = len(board)
    b = block_size(n)
    line = "+" + "+".join(["-" * (2 * b + (b - 1))] * b) + "+"

    for i, row in enumerate(board):
        if i % b == 0:
            print(line)
        row_str_parts = []
        for j, val in enumerate(row):
            ch = "." if val == EMPTY else str(val)
            row_str_parts.append(ch)
            if (j + 1) % b == 0 and j != n - 1:
                row_str_parts.append("|")
        print("| " + " ".join(row_str_parts) + " |")
    print(line)
