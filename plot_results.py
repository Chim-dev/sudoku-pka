# plot_results.py
import pandas as pd
import matplotlib.pyplot as plt

def plot_results(csv_path="results_25x25.csv"):
    # Baca CSV ke DataFrame
    df = pd.read_csv(csv_path)

    # Konversi kolom numerik kalau perlu
    df["time_ms"] = df["time_ms"].astype(float)
    df["recursion_steps"] = df["recursion_steps"].astype(int)
    df["peak_memory_kb"] = df["peak_memory_kb"].astype(float)

    # Hitung rata-rata per solver
    grouped = df.groupby("solver").agg(
        avg_time_ms=("time_ms", "mean"),
        avg_recursion=("recursion_steps", "mean"),
        avg_memory_kb=("peak_memory_kb", "mean"),
        success_rate=("success", "mean"),
    ).reset_index()

    print(grouped)

    # ---- Plot 1: Waktu eksekusi rata-rata ----
    plt.figure(figsize=(6, 4))
    plt.bar(grouped["solver"], grouped["avg_time_ms"], color=["#4e79a7", "#f28e2b", "#e15759"])
    plt.ylabel("Rata-rata waktu (ms)")
    plt.title("Rata-rata waktu eksekusi per solver")
    plt.tight_layout()
    plt.show()

    # ---- Plot 2: Langkah rekursif rata-rata ----
    plt.figure(figsize=(6, 4))
    plt.bar(grouped["solver"], grouped["avg_recursion"], color=["#76b7b2", "#59a14f", "#edc948"])
    plt.ylabel("Rata-rata langkah rekursif")
    plt.title("Rata-rata langkah rekursif per solver")
    plt.tight_layout()
    plt.show()

    # ---- Plot 3: Memori puncak rata-rata ----
    plt.figure(figsize=(6, 4))
    plt.bar(grouped["solver"], grouped["avg_memory_kb"], color=["#af7aa1", "#ff9da7", "#9c755f"])
    plt.ylabel("Rata-rata peak memory (KB)")
    plt.title("Rata-rata penggunaan memori per solver")
    plt.tight_layout()
    plt.show()

    # ---- Plot 4: Success rate ----
    plt.figure(figsize=(6, 4))
    # success_rate masih dalam 0..1 -> ubah ke persen
    plt.bar(grouped["solver"], grouped["success_rate"] * 100, color=["#bab0ab", "#4e79a7", "#f28e2b"])
    plt.ylabel("Success rate (%)")
    plt.title("Persentase puzzle yang berhasil diselesaikan")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_results()
