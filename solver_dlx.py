# solver_dlx.py
from typing import List, Dict, Set, Callable, Optional
from metrics import Metrics
import time
from sudoku_core import EMPTY, block_size, clone_board

StepCallback = Optional[Callable[[List[List[int]]], None]]

def sudoku_to_exact_cover(board: List[List[int]]):
    """
    Encode Sudoku (N x N) menjadi masalah Exact Cover.
    Setiap kandidat (r, c, v) -> satu baris dalam matrix,
    dengan 4 jenis constraint:
      1) Setiap sel (r,c) terisi tepat satu kali.
      2) Setiap nilai v muncul sekali di baris r.
      3) Setiap nilai v muncul sekali di kolom c.
      4) Setiap nilai v muncul sekali di blok.
    """
    n = len(board)
    b = block_size(n)

    def cell_constraint(r, c):
        return r * n + c

    def row_constraint(r, val):
        return n * n + r * n + (val - 1)

    def col_constraint(c, val):
        return 2 * n * n + c * n + (val - 1)

    def block_constraint(br, bc, val):
        return 3 * n * n + (br * b + bc) * n + (val - 1)

    # row_id -> set kolom
    matrix: Dict[int, Set[int]] = {}
    # row_id -> (r, c, val)
    row_lookup: Dict[int, tuple] = {}
    # kolom -> set row_id yang mengandung kolom tsb (index untuk percepat)
    col_to_rows: Dict[int, Set[int]] = {}

    row_id = 0
    for r in range(n):
        for c in range(n):
            if board[r][c] != EMPTY:
                vals = [board[r][c]]
            else:
                vals = list(range(1, n + 1))
            for val in vals:
                br = r // b
                bc = c // b
                cols = {
                    cell_constraint(r, c),
                    row_constraint(r, val),
                    col_constraint(c, val),
                    block_constraint(br, bc, val),
                }
                matrix[row_id] = cols
                row_lookup[row_id] = (r, c, val)
                for col in cols:
                    col_to_rows.setdefault(col, set()).add(row_id)
                row_id += 1

    all_cols = set()
    for cols in matrix.values():
        all_cols |= cols
    return matrix, row_lookup, all_cols, col_to_rows

def algorithm_x(matrix: Dict[int, Set[int]],
                columns: Set[int],
                col_to_rows: Dict[int, Set[int]],
                solution: List[int],
                metrics: Metrics,
                timeout_sec: float,
                start_time: float,
                row_lookup: Dict[int, tuple],
                vis_board: List[List[int]],
                step_callback: StepCallback = None) -> bool:
    """
    Implementasi Algorithm X (Exact Cover) gaya backtracking.
    matrix: row_id -> set kolom aktif
    columns: set kolom yang belum ter-cover
    col_to_rows: kolom -> set row_id aktif yang berisi kolom tsb
    vis_board: board untuk visualisasi (tidak dipakai hitung hasil benchmark)
    """
    # cek timeout
    if time.perf_counter() - start_time > timeout_sec:
        return False

    # semua constraint ter-cover -> solusi lengkap
    if not columns:
        if step_callback is not None:
            step_callback(vis_board)
        return True

    # heuristik: pilih kolom dengan jumlah baris aktif paling sedikit
    # (mirip DLX: \"choose column with minimal size\") [web:51][web:60][web:62]
    col = min(columns, key=lambda c: len(col_to_rows.get(c, ( ))))

    candidate_rows = list(col_to_rows.get(col, ( )))
    if not candidate_rows:
        return False

    for r in candidate_rows:
        # r bisa saja sudah terhapus di level lebih dalam, cek dulu
        if r not in matrix:
            continue

        metrics.recursion_steps += 1
        solution.append(r)

        # apply ke vis_board (untuk visualisasi)
        vr, vc, vv = row_lookup[r]
        old_val = vis_board[vr][vc]
        vis_board[vr][vc] = vv
        if step_callback is not None:
            step_callback(vis_board)

        removed_rows: Dict[int, Set[int]] = {}
        removed_cols: Set[int] = set()
        cols_to_cover = set(matrix[r])

        # cover semua kolom di row ini
        for c in cols_to_cover:
            if c in columns:
                columns.remove(c)
                removed_cols.add(c)
            # semua row lain yang mengandung kolom ini harus dihapus
            for rr in list(col_to_rows.get(c, ())):
                if rr == r:
                    continue
                if rr in matrix:
                    removed_rows[rr] = matrix[rr]
                    # hapus rr dari semua col_to_rows
                    for cc in matrix[rr]:
                        if cc in col_to_rows:
                            col_to_rows[cc].discard(rr)
                    del matrix[rr]

        # rekursif
        if algorithm_x(matrix, columns, col_to_rows, solution, metrics,
                       timeout_sec, start_time, row_lookup, vis_board, step_callback):
            return True

        # undo (uncover) semua perubahan
        for rr, cols in removed_rows.items():
            matrix[rr] = cols
            for cc in cols:
                col_to_rows.setdefault(cc, set()).add(rr)
        for c in removed_cols:
            columns.add(c)

        solution.pop()
        vis_board[vr][vc] = old_val
        if step_callback is not None:
            step_callback(vis_board)

    return False

def solve_dlx(board: List[List[int]],
              metrics: Metrics,
              timeout_sec: float,
              start_time: float,
              step_callback: StepCallback = None) -> bool:
    """
    Solver Sudoku dengan Exact Cover (Algorithm X).
    Dipakai oleh:
      - benchmark.py (tanpa step_callback)
      - visual_gui.py (dengan step_callback)
    """
    matrix, row_lookup, columns, col_to_rows = sudoku_to_exact_cover(board)
    solution_rows: List[int] = []

    # copy supaya struktur asli tidak rusak
    mat_copy = {r: set(cols) for r, cols in matrix.items()}
    cols_copy = set(columns)
    col_to_rows_copy = {c: set(rs) for c, rs in col_to_rows.items()}

    # board untuk visualisasi
    vis_board = clone_board(board)

    ok = algorithm_x(mat_copy, cols_copy, col_to_rows_copy, solution_rows, metrics,
                     timeout_sec, start_time, row_lookup, vis_board, step_callback)
    if not ok:
        return False

    # terapkan solusi ke board asli
    for r_id in solution_rows:
        r, c, v = row_lookup[r_id]
        board[r][c] = v
    return True
