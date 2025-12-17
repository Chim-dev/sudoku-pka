import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)  # bantu Ctrl+C di sebagian backend [web:279]

import pandas as pd
import matplotlib.pyplot as plt


def plot_results(csv_path: str, tag: str = ""):
    try:
        df = pd.read_csv(csv_path)

        # --- Kolom wajib ---
        df["time_ms"] = df["time_ms"].astype(float)
        df["recursion_steps"] = df["recursion_steps"].astype(int)
        df["success"] = df["success"].astype(int)

        # --- Kolom memori (kompatibel lama & baru) ---
        if "py_peak_kb" in df.columns:
            df["py_peak_kb"] = df["py_peak_kb"].astype(float)
        if "rss_kb" in df.columns:
            df["rss_kb"] = df["rss_kb"].astype(float)
        if "peak_memory_kb" in df.columns:
            df["peak_memory_kb"] = df["peak_memory_kb"].astype(float)

        # --- Aggregate per solver ---
        agg_dict = {
            "avg_time_ms": ("time_ms", "mean"),
            "avg_recursion": ("recursion_steps", "mean"),
            "success_rate": ("success", "mean"),
        }
        if "py_peak_kb" in df.columns:
            agg_dict["avg_py_peak_kb"] = ("py_peak_kb", "mean")
        if "rss_kb" in df.columns:
            agg_dict["avg_rss_kb"] = ("rss_kb", "mean")
        if "peak_memory_kb" in df.columns:
            agg_dict["avg_peak_memory_kb"] = ("peak_memory_kb", "mean")

        grouped = df.groupby("solver").agg(**agg_dict).reset_index()

        # Urutan solver konsisten
        order = ["dfs", "csp", "dlx"]
        grouped["solver"] = pd.Categorical(grouped["solver"], categories=order, ordered=True)
        grouped = grouped.sort_values("solver")

        print(f"\n=== {csv_path} {tag} ===")
        print(grouped)

        suffix = f" ({tag})" if tag else ""

        # Buat semua figure dulu
        plt.figure(figsize=(6, 4))
        plt.bar(grouped["solver"], grouped["avg_time_ms"])
        plt.ylabel("Rata-rata waktu (ms)")
        plt.title("Rata-rata waktu eksekusi per solver" + suffix)
        plt.tight_layout()

        plt.figure(figsize=(6, 4))
        plt.bar(grouped["solver"], grouped["avg_recursion"])
        plt.ylabel("Rata-rata node pencarian")
        plt.title("Rata-rata node pencarian (recursion_steps)" + suffix)
        plt.tight_layout()

        if "avg_py_peak_kb" in grouped.columns:
            plt.figure(figsize=(6, 4))
            plt.bar(grouped["solver"], grouped["avg_py_peak_kb"])
            plt.ylabel("Rata-rata Python peak (KB)")
            plt.title("Rata-rata Python peak memory (tracemalloc)" + suffix)
            plt.tight_layout()

        if "avg_rss_kb" in grouped.columns:
            plt.figure(figsize=(6, 4))
            plt.bar(grouped["solver"], grouped["avg_rss_kb"])
            plt.ylabel("Rata-rata RSS (KB)")
            plt.title("Rata-rata RSS memory (OS)" + suffix)
            plt.tight_layout()

        if "avg_peak_memory_kb" in grouped.columns:
            plt.figure(figsize=(6, 4))
            plt.bar(grouped["solver"], grouped["avg_peak_memory_kb"])
            plt.ylabel("Rata-rata peak_memory_kb (KB)")
            plt.title("Rata-rata peak_memory_kb (CSV lama)" + suffix)
            plt.tight_layout()

        plt.figure(figsize=(6, 4))
        plt.bar(grouped["solver"], grouped["success_rate"] * 100)
        plt.ylabel("Success rate (%)")
        plt.title("Persentase puzzle yang berhasil diselesaikan" + suffix)
        plt.ylim(0, 100)
        plt.tight_layout()

        # show sekali (blocking). Tutup window untuk lanjut ke run berikutnya. [web:277]
        plt.show()

        # setelah window ditutup, bersihkan figure agar run berikutnya tidak numpuk
        plt.close("all")  # [web:280][web:289]

    except KeyboardInterrupt:
        plt.close("all")  # tutup semua window saat Ctrl+C [web:280][web:289]
        raise


if __name__ == "__main__":
    plot_results("results_25x25_120.csv", tag="timeout=120s")
    plot_results("results_25x25_300.csv", tag="timeout=300s")
