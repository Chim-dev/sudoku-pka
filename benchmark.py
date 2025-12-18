# benchmark.py
import csv
import time
import tracemalloc
import psutil

from sudoku_core import parse_puzzle, clone_board
from solver_dfs import solve_dfs
from solver_csp import solve_csp
from solver_dlx import solve_dlx
from metrics import Metrics  


SOLVERS = {
    "dfs": solve_dfs,
    "csp": solve_csp,
    "dlx": solve_dlx,
}


def load_puzzles_from_file(path: str, n: int) -> list:
    """
    Membaca puzzle dari txt.
    - Untuk 25x25: tiap baris berisi 25 angka dipisah spasi, 25 baris per puzzle.
    """
    with open(path) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    puzzles = []
    for i in range(0, len(lines), n):
        chunk = lines[i:i + n]
        if len(chunk) == n:
            puzzles.append(parse_puzzle(chunk))
    return puzzles


def run_with_metrics_rss(solver_func, board, timeout_sec: float) -> Metrics:
    """
    Mengukur:
    - waktu (ms)
    - recursion_steps (diisi solver)
    - success (solver True/False)
    - py_peak_kb (tracemalloc peak)
    - rss_kb (RSS proses via psutil; bytes -> KB)
    """
    metrics = Metrics()

    proc = psutil.Process()
    rss_before = proc.memory_info().rss  

    tracemalloc.start()
    start_time = time.perf_counter()

    success = solver_func(board, metrics, timeout_sec, start_time)

    end_time = time.perf_counter()
    _, py_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rss_after = proc.memory_info().rss
    rss_est_peak = max(rss_before, rss_after)

    metrics.time_ms = (end_time - start_time) * 1000.0
    metrics.success = success


    metrics.py_peak_kb = py_peak / 1024.0
    metrics.rss_kb = rss_est_peak / 1024.0
    return metrics


def benchmark(txt_path: str, csv_out: str, n: int, timeout_sec: float = 30.0):
    puzzles = load_puzzles_from_file(txt_path, n)

    fieldnames = [
        "solver", "puzzle_id", "success",
        "time_ms", "recursion_steps",
        "py_peak_kb", "rss_kb"
    ]

    with open(csv_out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  

        for pid, puzzle in enumerate(puzzles):
            for solver_name, solver_func in SOLVERS.items():
                board = clone_board(puzzle)
                metrics = run_with_metrics_rss(solver_func, board, timeout_sec)

                writer.writerow({
                    "solver": solver_name,
                    "puzzle_id": pid,
                    "success": int(metrics.success),
                    "time_ms": f"{metrics.time_ms:.3f}",
                    "recursion_steps": int(metrics.recursion_steps),
                    "py_peak_kb": f"{metrics.py_peak_kb:.1f}",
                    "rss_kb": f"{metrics.rss_kb:.1f}",
                })


if __name__ == "__main__":
    benchmark("puzzles_25x25.txt", "results_25x25_120.csv", n=25, timeout_sec=120.0)
    benchmark("puzzles_25x25.txt", "results_25x25_300.csv", n=25, timeout_sec=300.0)

