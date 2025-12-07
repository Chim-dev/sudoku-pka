# visual_demo.py
import time
from sudoku_core import parse_puzzle, print_board, clone_board
from solver_dfs import solve_dfs
from solver_csp import solve_csp
from solver_dlx import solve_dlx
from metrics import Metrics

def load_first_puzzle(path: str):
    with open(path) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    n = len(lines[0])
    chunk = lines[:n]
    return parse_puzzle(chunk)

def step_printer(name: str, delay: float = 0.05):
    def callback(board):
        print("\033[H\033[J", end="")  # clear screen (works di banyak terminal)
        print(f"Solver: {name}")
        print_board(board)
        time.sleep(delay)
    return callback

if __name__ == "__main__":
    puzzle = load_first_puzzle("puzzles_25x25.txt")  # isinya boleh 9x9 dulu

    print("=== DFS Visual ===")
    b1 = clone_board(puzzle)
    m1 = Metrics()
    solve_dfs(b1, m1, timeout_sec=10.0, start_time=time.perf_counter(),
              step_callback=step_printer("DFS", delay=0.05))
    input("DFS selesai. Tekan Enter untuk lanjut ke CSP...")

    print("=== CSP Visual ===")
    b2 = clone_board(puzzle)
    m2 = Metrics()
    solve_csp(b2, m2, timeout_sec=10.0, start_time=time.perf_counter(),
              step_callback=step_printer("CSP", delay=0.05))
    input("CSP selesai. Tekan Enter untuk lanjut ke DLX...")

    print("=== DLX Visual ===")
    b3 = clone_board(puzzle)
    m3 = Metrics()
    solve_dlx(b3, m3, timeout_sec=10.0, start_time=time.perf_counter(),
              step_callback=step_printer("DLX", delay=0.02))
    input("DLX selesai. Tekan Enter untuk keluar...")
