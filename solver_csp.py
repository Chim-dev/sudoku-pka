from __future__ import annotations

from typing import Dict, Tuple, Set, List, Optional, Callable, Deque
from collections import deque
import time

from sudoku_core import EMPTY, block_size
from metrics import Metrics

Cell = Tuple[int, int]              # (row, col)
DomainMap = Dict[Cell, Set[int]]
NeighborMap = Dict[Cell, Set[Cell]]
Arc = Tuple[Cell, Cell]             # (Xi, Xj)
PruneLog = List[Tuple[Cell, int]]   # daftar (cell, value) yang dihapus dari domain

StepCallback = Optional[Callable[[List[List[int]]], None]]


def build_neighbor_map(size: int) -> NeighborMap:
    """Membangun graph constraint Sudoku: tiap cell terhubung ke row/col/block neighbors."""
    b = block_size(size)
    neighbors: NeighborMap = {(r, c): set() for r in range(size) for c in range(size)}

    for r in range(size):
        for c in range(size):
            # row neighbors
            for cc in range(size):
                if cc != c:
                    neighbors[(r, c)].add((r, cc))

            # col neighbors
            for rr in range(size):
                if rr != r:
                    neighbors[(r, c)].add((rr, c))

            # block neighbors
            br = (r // b) * b
            bc = (c // b) * b
            for rr in range(br, br + b):
                for cc in range(bc, bc + b):
                    if (rr, cc) != (r, c):
                        neighbors[(r, c)].add((rr, cc))

    return neighbors


def init_domains(board: List[List[int]]) -> DomainMap:
    """Domain awal: cell kosong -> {1..N}, cell terisi -> {nilai itu}."""
    n = len(board)
    all_vals = set(range(1, n + 1))
    domains: DomainMap = {}

    for r in range(n):
        for c in range(n):
            domains[(r, c)] = {board[r][c]} if board[r][c] != EMPTY else set(all_vals)

    return domains


def is_assigned(board: List[List[int]], cell: Cell) -> bool:
    r, c = cell
    return board[r][c] != EMPTY


def select_unassigned_mrv_degree(domains: DomainMap,
                                 board: List[List[int]],
                                 neighbors: NeighborMap) -> Optional[Cell]:
    """
    MRV: pilih cell unassigned dengan domain terkecil.
    Tie-break: degree heuristic (lebih banyak tetangga unassigned).
    """
    best_cell: Optional[Cell] = None
    best_domain_size = 10**9
    best_degree = -1

    for cell, dom in domains.items():
        if is_assigned(board, cell):
            continue

        dsize = len(dom)
        if dsize == 0:
            return cell  # dead-end cepat

        degree = sum(1 for nb in neighbors[cell] if not is_assigned(board, nb))
        if dsize < best_domain_size or (dsize == best_domain_size and degree > best_degree):
            best_cell = cell
            best_domain_size = dsize
            best_degree = degree

    return best_cell


def order_values_lcv(cell: Cell,
                     domains: DomainMap,
                     board: List[List[int]],
                     neighbors: NeighborMap) -> List[int]:
    """
    LCV: urutkan nilai yang menghapus paling sedikit kandidat di tetangga.
    """
    scores: List[Tuple[int, int]] = []
    for value in domains[cell]:
        eliminated = 0
        for nb in neighbors[cell]:
            if is_assigned(board, nb):
                continue
            if value in domains[nb]:
                eliminated += 1
        scores.append((eliminated, value))

    scores.sort()
    return [v for _, v in scores]


def revise_neq(domains: DomainMap, xi: Cell, xj: Cell, pruned: PruneLog) -> bool:
    """
    Constraint antar neighbor Sudoku: Xi != Xj.
    Untuk constraint !=: hanya perlu prune jika domain(Xj) singleton {v},
    maka v dihapus dari domain(Xi).
    """
    if len(domains[xj]) != 1:
        return False

    forced_val = next(iter(domains[xj]))
    if forced_val in domains[xi]:
        domains[xi].remove(forced_val)
        pruned.append((xi, forced_val))
        return True

    return False


def ac3(domains: DomainMap, queue: Deque[Arc], neighbors: NeighborMap) -> Tuple[bool, PruneLog]:
    """
    AC-3: proses queue arc (Xi, Xj); jika domain Xi berubah, push (Xk, Xi) untuk semua neighbor Xk != Xj.
    """
    pruned: PruneLog = []

    while queue:
        xi, xj = queue.popleft()

        if revise_neq(domains, xi, xj, pruned):
            if len(domains[xi]) == 0:
                return False, pruned

            for xk in neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))

    return True, pruned


def assign_cell(board: List[List[int]], domains: DomainMap, cell: Cell, value: int) -> PruneLog:
    """
    Assign cell=value dan prune domain(cell) menjadi singleton {value}.
    Return log pruning untuk undo.
    """
    r, c = cell
    board[r][c] = value

    removed: PruneLog = []
    current_dom = domains[cell]
    for v in list(current_dom):
        if v != value:
            current_dom.remove(v)
            removed.append((cell, v))

    return removed


def undo(board: List[List[int]], domains: DomainMap, cell: Cell, prev_board_val: int, pruned: PruneLog) -> None:
    r, c = cell
    board[r][c] = prev_board_val
    for (pruned_cell, val) in pruned:
        domains[pruned_cell].add(val)


def backtrack_mac(board: List[List[int]],
                  domains: DomainMap,
                  neighbors: NeighborMap,
                  metrics: Metrics,
                  timeout_sec: float,
                  start_time: float,
                  step_callback: StepCallback = None) -> bool:
    if time.perf_counter() - start_time > timeout_sec:
        return False

    metrics.recursion_steps += 1  # cost per node search

    cell = select_unassigned_mrv_degree(domains, board, neighbors)
    if cell is None:
        if step_callback is not None:
            step_callback(board)
        return True

    if len(domains[cell]) == 0:
        return False

    r, c = cell
    prev_val = board[r][c]

    for value in order_values_lcv(cell, domains, board, neighbors):
        pruned_total: PruneLog = []

        # assign
        pruned_total += assign_cell(board, domains, cell, value)
        if step_callback is not None:
            step_callback(board)

        # MAC: jalankan AC-3 hanya untuk arc (neighbor -> cell)
        q = deque((nb, cell) for nb in neighbors[cell] if not is_assigned(board, nb))
        ok, pruned_ac3 = ac3(domains, q, neighbors)
        pruned_total += pruned_ac3

        if ok and backtrack_mac(board, domains, neighbors, metrics, timeout_sec, start_time, step_callback):
            return True

        # undo
        undo(board, domains, cell, prev_val, pruned_total)
        if step_callback is not None:
            step_callback(board)

    return False


def solve_csp(board: List[List[int]],
              metrics: Metrics,
              timeout_sec: float,
              start_time: float,
              step_callback: StepCallback = None) -> bool:
    n = len(board)
    neighbors = build_neighbor_map(n)
    domains = init_domains(board)

    # AC-3 global sekali di awal (pruning awal)
    all_arcs = deque((xi, xj) for xi in neighbors for xj in neighbors[xi])
    ok, _ = ac3(domains, all_arcs, neighbors)
    if not ok:
        return False

    return backtrack_mac(board, domains, neighbors, metrics, timeout_sec, start_time, step_callback)
