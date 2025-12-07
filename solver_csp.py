# solver_csp.py
from typing import Dict, Tuple, Set, List, Optional, Callable
from sudoku_core import EMPTY, block_size
from metrics import Metrics
import time

Coord = Tuple[int, int]
StepCallback = Optional[Callable[[List[List[int]]], None]]

def init_domains(board: List[List[int]]) -> Dict[Coord, Set[int]]:
    """
    Inisialisasi domain untuk tiap sel:
    - Jika kosong: {1..N}
    - Jika sudah terisi: {nilai itu}
    Lalu lakukan constraint propagation sederhana (hapus nilai yang sudah fix dari tetangga).
    """
    n = len(board)
    b = block_size(n)
    all_vals = set(range(1, n + 1))
    domains: Dict[Coord, Set[int]] = {}

    for r in range(n):
        for c in range(n):
            if board[r][c] == EMPTY:
                domains[(r, c)] = set(all_vals)
            else:
                domains[(r, c)] = {board[r][c]}

    def neighbors(r: int, c: int):
        # baris
        for j in range(n):
            if j != c:
                yield (r, j)
        # kolom
        for i in range(n):
            if i != r:
                yield (i, c)
        # blok
        br = (r // b) * b
        bc = (c // b) * b
        for i in range(br, br + b):
            for j in range(bc, bc + b):
                if i != r or j != c:
                    yield (i, j)

    # propagasi awal
    changed = True
    while changed:
        changed = False
        for (r, c), dom in domains.items():
            if len(dom) == 1:
                val = next(iter(dom))
                for (nr, nc) in neighbors(r, c):
                    if val in domains[(nr, nc)] and len(domains[(nr, nc)]) > 1:
                        domains[(nr, nc)].remove(val)
                        changed = True
    return domains

def select_unassigned_variable(domains: Dict[Coord, Set[int]],
                               board: List[List[int]]) -> Optional[Coord]:
    """
    Heuristik MRV: pilih sel kosong dengan domain terkecil (>0).
    Kalau ada domain size 0 -> dead-end.
    """
    mrv_cell = None
    mrv_size = 10**9
    for (r, c), dom in domains.items():
        if board[r][c] == EMPTY:
            size = len(dom)
            if size == 0:
                return (r, c)  # dead-end
            if size < mrv_size:
                mrv_size = size
                mrv_cell = (r, c)
    return mrv_cell

def get_neighbors(n: int, b: int, r: int, c: int) -> List[Coord]:
    res = []
    # baris
    for j in range(n):
        if j != c:
            res.append((r, j))
    # kolom
    for i in range(n):
        if i != r:
            res.append((i, c))
    # blok
    br = (r // b) * b
    bc = (c // b) * b
    for i in range(br, br + b):
        for j in range(bc, bc + b):
            if i != r or j != c:
                res.append((i, j))
    return res

def backtrack_csp(board: List[List[int]],
                  domains: Dict[Coord, Set[int]],
                  metrics: Metrics,
                  timeout_sec: float,
                  start_time: float,
                  step_callback: StepCallback = None) -> bool:
    """
    Backtracking dengan:
    - MRV untuk pemilihan variabel
    - forward checking untuk pruning domain tetangga
    - optional step_callback untuk visualisasi

    recursion_steps dihitung per node search:
    setiap kali fungsi ini dipanggil (dan belum timeout) -> +1.
    """
    if time.perf_counter() - start_time > timeout_sec:
        return False

    # Satu node baru di pohon pencarian
    metrics.recursion_steps += 1

    var = select_unassigned_variable(domains, board)
    if var is None:
        # semua terisi
        if step_callback is not None:
            step_callback(board)
        return True

    r, c = var
    if board[r][c] != EMPTY:
        return backtrack_csp(board, domains, metrics, timeout_sec, start_time, step_callback)

    n = len(board)
    b = block_size(n)

    for val in sorted(domains[(r, c)]):
        old_board_val = board[r][c]
        board[r][c] = val
        if step_callback is not None:
            step_callback(board)

        removed: Dict[Coord, Set[int]] = {}
        ok = True
        # forward checking: hapus 'val' dari domain tetangga
        for (nr, nc) in get_neighbors(n, b, r, c):
            d = domains[(nr, nc)]
            if val in d:
                if len(d) == 1:
                    ok = False
                    break
                removed.setdefault((nr, nc), set()).add(val)
        if ok:
            for (nr, nc), vals in removed.items():
                domains[(nr, nc)] -= vals
            if backtrack_csp(board, domains, metrics, timeout_sec, start_time, step_callback):
                return True
            # undo domain
            for (nr, nc), vals in removed.items():
                domains[(nr, nc)] |= vals

        # undo assignment di board
        board[r][c] = old_board_val
        if step_callback is not None:
            step_callback(board)

    return False

def solve_csp(board: List[List[int]],
              metrics: Metrics,
              timeout_sec: float,
              start_time: float,
              step_callback: StepCallback = None) -> bool:
    domains = init_domains(board)
    return backtrack_csp(board, domains, metrics, timeout_sec, start_time, step_callback)
