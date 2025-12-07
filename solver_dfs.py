# solver_dfs.py
from typing import List, Callable, Optional
from sudoku_core import EMPTY, find_empty, is_valid
from metrics import Metrics
import time

StepCallback = Optional[Callable[[List[List[int]]], None]]

def solve_dfs(board: List[List[int]],
              metrics: Metrics,
              timeout_sec: float,
              start_time: float,
              step_callback: StepCallback = None) -> bool:
    """
    Solver backtracking dasar (DFS).
    Sekarang recursion_steps dihitung per node search:
    setiap kali fungsi ini dipanggil (dan belum timeout) -> +1.
    """
    # cek timeout
    if time.perf_counter() - start_time > timeout_sec:
        return False

    # satu node baru di pohon pencarian
    metrics.recursion_steps += 1

    pos = find_empty(board)
    if pos is None:
        # solved
        if step_callback is not None:
            step_callback(board)
        return True

    r, c = pos
    n = len(board)

    for val in range(1, n + 1):
        if is_valid(board, r, c, val):
            board[r][c] = val
            if step_callback is not None:
                step_callback(board)

            if solve_dfs(board, metrics, timeout_sec, start_time, step_callback):
                return True

            # undo
            board[r][c] = EMPTY
            if step_callback is not None:
                step_callback(board)

    return False
