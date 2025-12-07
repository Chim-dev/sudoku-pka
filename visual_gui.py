# visual_gui.py
import time
import argparse
import tkinter as tk

from sudoku_core import parse_puzzle, clone_board
from solver_dfs import solve_dfs
from solver_csp import solve_csp
from solver_dlx import solve_dlx
from metrics import Metrics

def load_first_puzzle(path: str):
    # ambil puzzle pertama dari file (9x9 atau 25x25)
    with open(path) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    n = len(lines[0])
    chunk = lines[:n]
    return parse_puzzle(chunk)

def collect_snapshots(solver_func, puzzle_path: str,
                      timeout_sec: float = 10.0,
                      downsample: int = 50):
    """
    Jalankan solver dengan step_callback yang menyimpan snapshot board.
    downsample: simpan hanya setiap N langkah biar tidak kebanyakan frame.
    """
    board = load_first_puzzle(puzzle_path)
    board = clone_board(board)

    metrics = Metrics()
    snapshots = []

    step_counter = {"k": 0}

    def callback(b):
        step_counter["k"] += 1
        if step_counter["k"] % downsample == 0:
            snapshots.append([row[:] for row in b])

    start_time = time.perf_counter()
    solved = solver_func(board, metrics, timeout_sec, start_time, step_callback=callback)
    end_time = time.perf_counter()

    # isi time_ms di metrics untuk dilaporkan
    metrics.time_ms = (end_time - start_time) * 1000.0

    # pastikan solusi akhir juga tersimpan
    snapshots.append([row[:] for row in board])

    return snapshots, metrics, solved

class SudokuGUI:
    def __init__(self, snapshots, cell_size=40, delay_ms=50, title="Sudoku Visual"):
        self.snapshots = snapshots
        self.index = 0
        self.cell_size = cell_size
        self.delay_ms = delay_ms

        self.n = len(snapshots[0])
        self.root = tk.Tk()
        self.root.title(title)

        canvas_size = self.cell_size * self.n
        self.canvas = tk.Canvas(self.root,
                                width=canvas_size,
                                height=canvas_size,
                                bg="white")
        self.canvas.pack()

        self.draw_board(self.snapshots[0])
        # mulai animasi
        self.root.after(self.delay_ms, self.play)

    def draw_board(self, board):
        self.canvas.delete("all")
        n = self.n
        cs = self.cell_size

        # gambar grid
        for i in range(n + 1):
            width = 1
            if i % int(n**0.5) == 0:
                width = 3  # garis blok lebih tebal
            # garis horizontal
            self.canvas.create_line(0, i * cs, n * cs, i * cs, width=width)
            # garis vertikal
            self.canvas.create_line(i * cs, 0, i * cs, n * cs, width=width)

        # isi angka
        for r in range(n):
            for c in range(n):
                val = board[r][c]
                if val != 0:
                    x = c * cs + cs / 2
                    y = r * cs + cs / 2
                    self.canvas.create_text(x, y, text=str(val), font=("Arial", int(cs/2)))

    def play(self):
        if self.index >= len(self.snapshots):
            return
        self.draw_board(self.snapshots[self.index])
        self.index += 1
        self.root.after(self.delay_ms, self.play)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "solver",
        choices=["dfs", "csp", "dlx"],
        help="Pilih algoritma yang akan divisualisasikan"
    )
    parser.add_argument(
        "--puzzle",
        default="puzzles_25x25.txt",
        help="Path file puzzle (default: puzzles_25x25.txt)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout (detik) untuk solving"
    )
    parser.add_argument(
        "--downsample",
        type=int,
        default=50,
        help="Simpan hanya setiap N langkah (default 50) agar animasi tidak terlalu berat"
    )
    args = parser.parse_args()

    solver_map = {
        "dfs": solve_dfs,
        "csp": solve_csp,
        "dlx": solve_dlx,
    }
    solver_func = solver_map[args.solver]

    print(f"Mengumpulkan snapshot untuk solver: {args.solver} ...")
    snapshots, metrics, solved = collect_snapshots(
        solver_func,
        args.puzzle,
        timeout_sec=args.timeout,
        downsample=args.downsample,
    )
    print(f"Solved: {solved}, langkah: {metrics.recursion_steps}, waktu: {metrics.time_ms:.2f} ms")

    if not snapshots:
        print("Tidak ada snapshot yang terkumpul.")
        return

    # Untuk 9x9, cell_size=40 OK; untuk 25x25 bisa dikurangi, misal 20
    cell_size = 40 if len(snapshots[0]) <= 9 else 20
    gui = SudokuGUI(
        snapshots,
        cell_size=cell_size,
        delay_ms=50,
        title=f"Sudoku - {args.solver.upper()}",
    )
    gui.root.mainloop()

if __name__ == "__main__":
    main()
