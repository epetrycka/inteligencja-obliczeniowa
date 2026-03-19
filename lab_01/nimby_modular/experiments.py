import json
from pathlib import Path

from .tournament import (
    make_expecti_ab,
    make_negamax_ab,
    make_negamax_noab,
    play_match,
)


def run_experiments(out_json: Path):
    results = {
        "settings": {
            "piles": [3, 4, 5],
            "probability_nimby": 0.1,
            "games_depth_duel": 200,
            "games_algo_compare": 100,
            "games_expecti": 100,
            "nmoves_cap": 200,
        },
        "task2_depth_duel": [],
        "task6_algo_compare": [],
        "task8_expecti_compare": [],
    }

    variants = [
        ("nim_deterministic", 0.0),
        ("nimby_probabilistic", 0.1),
    ]

    # Task 2: two Negamax depths compared on deterministic and probabilistic variants.
    for variant_name, error_probability in variants:
        stats = play_match(
            game_kwargs={"piles": (3, 4, 5), "error_probability": error_probability},
            ai_factory_a=make_negamax_ab(4),
            ai_factory_b=make_negamax_ab(6),
            n_games=200,
            seed_base=10000 if error_probability == 0.0 else 20000,
        )

        results["task2_depth_duel"].append(
            {
                "variant": variant_name,
                "agent_a": "NegamaxAB_d4",
                "agent_b": "NegamaxAB_d6",
                "games": 200,
                "wins_a": stats.wins_a,
                "wins_b": stats.wins_b,
                "draws": stats.draws,
                "time_a_s": round(stats.time_a_s, 6),
                "time_b_s": round(stats.time_b_s, 6),
                "avg_move_a_ms": round(1000.0 * stats.time_a_s / max(stats.moves_a, 1), 4),
                "avg_move_b_ms": round(1000.0 * stats.time_b_s / max(stats.moves_b, 1), 4),
            }
        )

    # Task 6: Negamax with and without alpha-beta for two depths.
    for variant_name, error_probability in variants:
        for depth in (4, 6):
            stats = play_match(
                game_kwargs={"piles": (3, 4, 5), "error_probability": error_probability},
                ai_factory_a=make_negamax_ab(depth),
                ai_factory_b=make_negamax_noab(depth),
                n_games=100,
                seed_base=(30000 if error_probability == 0.0 else 40000) + depth,
            )

            results["task6_algo_compare"].append(
                {
                    "variant": variant_name,
                    "agent_a": f"NegamaxAB_d{depth}",
                    "agent_b": f"NegamaxNoAB_d{depth}",
                    "games": 100,
                    "wins_a": stats.wins_a,
                    "wins_b": stats.wins_b,
                    "draws": stats.draws,
                    "time_a_s": round(stats.time_a_s, 6),
                    "time_b_s": round(stats.time_b_s, 6),
                    "avg_move_a_ms": round(1000.0 * stats.time_a_s / max(stats.moves_a, 1), 4),
                    "avg_move_b_ms": round(1000.0 * stats.time_b_s / max(stats.moves_b, 1), 4),
                }
            )

    # Task 8: Expectiminimax-style agent vs classic Negamax in Nimby only.
    for depth in (4, 6):
        stats = play_match(
            game_kwargs={"piles": (3, 4, 5), "error_probability": 0.1},
            ai_factory_a=make_negamax_ab(depth),
            ai_factory_b=make_expecti_ab(depth),
            n_games=100,
            seed_base=50000 + depth,
        )

        results["task8_expecti_compare"].append(
            {
                "variant": "nimby_probabilistic",
                "agent_a": f"NegamaxAB_d{depth}",
                "agent_b": f"ExpectiNegamaxAB_d{depth}",
                "games": 100,
                "wins_a": stats.wins_a,
                "wins_b": stats.wins_b,
                "draws": stats.draws,
                "time_a_s": round(stats.time_a_s, 6),
                "time_b_s": round(stats.time_b_s, 6),
                "avg_move_a_ms": round(1000.0 * stats.time_a_s / max(stats.moves_a, 1), 4),
                "avg_move_b_ms": round(1000.0 * stats.time_b_s / max(stats.moves_b, 1), 4),
            }
        )

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def print_summary(results):
    print("=== TASK 2: DEPTH DUEL (NEGAMAX AB) ===")
    for row in results["task2_depth_duel"]:
        print(
            f"{row['variant']}: {row['agent_a']} vs {row['agent_b']} -> "
            f"wins {row['wins_a']}:{row['wins_b']}, draws {row['draws']}, "
            f"avg move ms {row['avg_move_a_ms']}:{row['avg_move_b_ms']}"
        )

    print("\n=== TASK 6: NEGAMAX WITH/WITHOUT ALPHA-BETA ===")
    for row in results["task6_algo_compare"]:
        print(
            f"{row['variant']}: {row['agent_a']} vs {row['agent_b']} -> "
            f"wins {row['wins_a']}:{row['wins_b']}, draws {row['draws']}, "
            f"time s {row['time_a_s']}:{row['time_b_s']}"
        )

    print("\n=== TASK 8: EXPECTI-NEGAMAX VS NEGAMAX ===")
    for row in results["task8_expecti_compare"]:
        print(
            f"{row['variant']}: {row['agent_a']} vs {row['agent_b']} -> "
            f"wins {row['wins_a']}:{row['wins_b']}, draws {row['draws']}, "
            f"time s {row['time_a_s']}:{row['time_b_s']}"
        )
