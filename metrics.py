# metrics.py
import time
import tracemalloc
import psutil
from dataclasses import dataclass

@dataclass
class Metrics:
    recursion_steps: int = 0
    time_ms: float = 0.0
    success: bool = False
    peak_memory_kb: float = 0.0     # tracemalloc peak (Python allocations)
    peak_rss_kb: float = 0.0        # OS RSS peak (process resident set)

def run_with_metrics(solver_func, board, timeout_sec: float = 30.0) -> Metrics:
    metrics = Metrics()

    proc = psutil.Process()
    rss_start = proc.memory_info().rss  # bytes [web:225][web:224]
    rss_peak = rss_start

    tracemalloc.start()
    start_time = time.perf_counter()

    # jalankan solver
    success = solver_func(board, metrics, timeout_sec, start_time)

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # ambil RSS lagi setelah solve (simple peak estimate)
    rss_end = proc.memory_info().rss
    rss_peak = max(rss_peak, rss_end)

    metrics.time_ms = (end_time - start_time) * 1000.0
    metrics.success = success
    metrics.peak_memory_kb = peak / 1024.0
    metrics.peak_rss_kb = rss_peak / 1024.0
    return metrics
    