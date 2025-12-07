# read_results.py
import csv

def read_results(path="sudoku_pka/results_25x25.csv"):
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows[:10]:  # print 10 baris pertama
        print(row)

if __name__ == "__main__":
    read_results()
