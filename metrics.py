import time
import tracemalloc
from dataclasses import dataclass

@dataclass
class Metrics:
    recursion_steps: int = 0
    time_ms: float = 0.0
    success: bool = False
    peak_memory_kb: float = 0.0

def run_with_metrics(solver_func, board, timeout_sec: float = 30.0) -> Metrics:
    metrics = Metrics()
    tracemalloc.start()
    start_time = time.perf_counter()

    success = solver_func(board, metrics, timeout_sec, start_time)

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics.time_ms = (end_time - start_time) * 1000.0
    metrics.success = success
    metrics.peak_memory_kb = peak / 1024.0
    return metrics
