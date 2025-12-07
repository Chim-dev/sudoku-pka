from sudoku_core import parse_puzzle, clone_board
from solver_dfs import solve_dfs
from solver_csp import solve_csp
from solver_dlx import solve_dlx
from metrics import run_with_metrics
import csv

SOLVERS = {
    "dfs": solve_dfs,
    "csp": solve_csp,
    "dlx": solve_dlx,
}

def load_puzzles_from_file(path: str):
    with open(path) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    n = 25  # karena file ini khusus puzzle 25x25

    puzzles = []
    for i in range(0, len(lines), n):
        chunk = lines[i:i+n]
        if len(chunk) == n:
            puzzles.append(parse_puzzle(chunk))
    return puzzles


def benchmark(file_path: str, csv_out: str, timeout_sec: float = 30.0):
    puzzles = load_puzzles_from_file(file_path)
    with open(csv_out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["solver", "puzzle_id", "success",
                         "time_ms", "recursion_steps", "peak_memory_kb"])
        for pid, puzzle in enumerate(puzzles):
            for name, solver in SOLVERS.items():
                board = clone_board(puzzle)
                metrics = run_with_metrics(solver, board, timeout_sec)
                writer.writerow([
                    name,
                    pid,
                    int(metrics.success),
                    f"{metrics.time_ms:.3f}",
                    metrics.recursion_steps,
                    f"{metrics.peak_memory_kb:.1f}",
                ])

if __name__ == "__main__":
    benchmark("puzzles_25x25.txt", "results_25x25.csv", timeout_sec=120.0)
