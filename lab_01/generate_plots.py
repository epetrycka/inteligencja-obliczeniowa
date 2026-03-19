import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "results.json"
FIG_DIR = ROOT / "figures"


def load_results():
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


def save_figure(fig, out_name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIG_DIR / out_name
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_task2_depth_duel(results):
    rows = results["task2_depth_duel"]
    labels = ["Nim", "Nimby"]
    wins_d4 = [rows[0]["wins_a"], rows[1]["wins_a"]]
    wins_d6 = [rows[0]["wins_b"], rows[1]["wins_b"]]

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.bar([i - width / 2 for i in x], wins_d4, width, label="Negamax AB d4")
    ax.bar([i + width / 2 for i in x], wins_d6, width, label="Negamax AB d6")

    ax.set_title("Task 2: Wygrane dla d4 vs d6")
    ax.set_ylabel("Liczba wygranych")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(max(wins_d4), max(wins_d6)) * 1.15)
    ax.legend()

    save_figure(fig, "task2_wins.png")


def plot_task6_times(results):
    rows = results["task6_algo_compare"]
    labels = [
        "Nim d4",
        "Nim d6",
        "Nimby d4",
        "Nimby d6",
    ]
    times_ab = [r["time_a_s"] for r in rows]
    times_noab = [r["time_b_s"] for r in rows]

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    ax.bar([i - width / 2 for i in x], times_ab, width, label="Negamax AB")
    ax.bar([i + width / 2 for i in x], times_noab, width, label="Negamax NoAB")

    ax.set_title("Task 6: Czas obliczen AB vs NoAB")
    ax.set_ylabel("Laczny czas [s]")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=15)
    ax.legend()

    save_figure(fig, "task6_times.png")


def plot_task8_expecti(results):
    rows = results["task8_expecti_compare"]
    labels = ["Depth 4", "Depth 6"]
    wins_negamax = [rows[0]["wins_a"], rows[1]["wins_a"]]
    wins_expecti = [rows[0]["wins_b"], rows[1]["wins_b"]]

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.bar([i - width / 2 for i in x], wins_negamax, width, label="Negamax AB")
    ax.bar([i + width / 2 for i in x], wins_expecti, width, label="ExpectiNegamax AB")

    ax.set_title("Task 8: Negamax vs ExpectiNegamax")
    ax.set_ylabel("Liczba wygranych")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(max(wins_negamax), max(wins_expecti)) * 1.15)
    ax.legend()

    save_figure(fig, "task8_wins.png")


def main():
    results = load_results()
    plot_task2_depth_duel(results)
    plot_task6_times(results)
    plot_task8_expecti(results)
    print("Saved plots to", FIG_DIR)


if __name__ == "__main__":
    main()
