import argparse
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from easyAI import AI_Player, Negamax, TwoPlayerGame

INF = float("inf")


class NimbyGame(TwoPlayerGame):
    """Nim game with optional execution noise (Nimby)."""

    def __init__(
        self,
        players=None,
        piles=(3, 4, 5),
        max_removals_per_turn=None,
        error_probability=0.0,
        start_player=1,
        seed=None,
    ):
        self.players = players
        self.piles = list(piles)
        self.max_removals_per_turn = max_removals_per_turn
        self.error_probability = error_probability
        self.current_player = start_player
        self._rng = random.Random(seed)
        self._history: List[Tuple[int, int]] = []

    def possible_moves(self):
        return [
            f"{i + 1},{j}"
            for i in range(len(self.piles))
            for j in range(
                1,
                self.piles[i] + 1
                if self.max_removals_per_turn is None
                else min(self.piles[i] + 1, self.max_removals_per_turn + 1),
            )
        ]

    def _parse_move(self, move):
        pile_idx, intended = map(int, str(move).split(","))
        return pile_idx - 1, intended

    def chance_outcomes(self, move):
        """Return (probability, pile_index, removed_count) outcomes."""
        pile_idx, intended = self._parse_move(move)
        p = float(self.error_probability)
        if p <= 0.0 or intended <= 1:
            return [(1.0, pile_idx, intended)]
        return [(1.0 - p, pile_idx, intended), (p, pile_idx, intended - 1)]

    def apply_actual_move(self, pile_idx, removed):
        self.piles[pile_idx] -= removed
        self._history.append((pile_idx, removed))

    def unapply_last_actual_move(self):
        pile_idx, removed = self._history.pop()
        self.piles[pile_idx] += removed

    def make_move(self, move):
        outcomes = self.chance_outcomes(move)
        if len(outcomes) == 1:
            _, pile_idx, removed = outcomes[0]
            self.apply_actual_move(pile_idx, removed)
            return

        threshold = self._rng.random()
        cumulative = 0.0
        chosen = outcomes[-1]
        for outcome in outcomes:
            cumulative += outcome[0]
            if threshold <= cumulative:
                chosen = outcome
                break

        _, pile_idx, removed = chosen
        self.apply_actual_move(pile_idx, removed)

    def unmake_move(self, move):  # move is unused; last move is enough.
        self.unapply_last_actual_move()

    def show(self):
        print(" ".join(map(str, self.piles)))

    def win(self):
        return max(self.piles) == 0

    def is_over(self):
        return self.win()

    def scoring(self):
        return 100 if self.win() else 0

    def ttentry(self):
        return tuple(self.piles), self.current_player


class NegamaxNoAB:
    """Negamax without alpha-beta pruning."""

    def __init__(self, depth, scoring=None):
        self.depth = depth
        self.scoring = scoring
        self.alpha = 0.0

    def __call__(self, game):
        scoring = self.scoring if self.scoring else (lambda g: g.scoring())
        self.alpha = self._search(game, self.depth, self.depth, scoring)
        return game.ai_move

    def _search(self, game, depth, orig_depth, scoring):
        if depth == 0 or game.is_over():
            return scoring(game) * (1 + 0.001 * depth)

        possible_moves = game.possible_moves()
        best_move = possible_moves[0]
        best_value = -INF
        unmake_move = hasattr(game, "unmake_move")
        state = game

        if depth == orig_depth:
            state.ai_move = best_move

        for move in possible_moves:
            if not unmake_move:
                game = state.copy()

            game.make_move(move)
            game.switch_player()
            value = -self._search(game, depth - 1, orig_depth, scoring)

            if unmake_move:
                game.switch_player()
                game.unmake_move(move)

            if value > best_value:
                best_value = value
                best_move = move
                if depth == orig_depth:
                    state.ai_move = move

        return best_value


class ExpectiNegamaxAB:
    """Expectiminimax-like negamax with alpha-beta on decision nodes."""

    def __init__(self, depth, scoring=None, win_score=INF):
        self.depth = depth
        self.scoring = scoring
        self.win_score = win_score
        self.alpha = 0.0

    def __call__(self, game):
        scoring = self.scoring if self.scoring else (lambda g: g.scoring())
        self.alpha = self._search(
            game,
            depth=self.depth,
            orig_depth=self.depth,
            scoring=scoring,
            alpha=-self.win_score,
            beta=self.win_score,
        )
        return game.ai_move

    def _search(self, game, depth, orig_depth, scoring, alpha, beta):
        if depth == 0 or game.is_over():
            return scoring(game) * (1 + 0.001 * depth)

        possible_moves = game.possible_moves()
        best_move = possible_moves[0]
        best_value = -INF

        if depth == orig_depth:
            game.ai_move = best_move

        for move in possible_moves:
            expected_value = 0.0
            for probability, pile_idx, removed in game.chance_outcomes(move):
                game.apply_actual_move(pile_idx, removed)
                game.switch_player()
                child_value = -self._search(
                    game,
                    depth=depth - 1,
                    orig_depth=orig_depth,
                    scoring=scoring,
                    alpha=-beta,
                    beta=-alpha,
                )
                game.switch_player()
                game.unapply_last_actual_move()
                expected_value += probability * child_value

            if expected_value > best_value:
                best_value = expected_value
                best_move = move
                if depth == orig_depth:
                    game.ai_move = move

            if expected_value > alpha:
                alpha = expected_value
            if alpha >= beta:
                break

        return best_value


@dataclass
class MatchResult:
    wins_a: int = 0
    wins_b: int = 0
    draws: int = 0
    moves_a: int = 0
    moves_b: int = 0
    time_a_s: float = 0.0
    time_b_s: float = 0.0


class TimedAIPlayer(AI_Player):
    def __init__(self, ai_algo, slot_name, stats: MatchResult):
        super().__init__(ai_algo)
        self.slot_name = slot_name
        self.stats = stats

    def ask_move(self, game):
        t0 = time.perf_counter()
        move = self.AI_algo(game)
        dt = time.perf_counter() - t0

        if self.slot_name == "A":
            self.stats.moves_a += 1
            self.stats.time_a_s += dt
        else:
            self.stats.moves_b += 1
            self.stats.time_b_s += dt

        return move


def play_match(
    game_kwargs: Dict,
    ai_factory_a: Callable[[], object],
    ai_factory_b: Callable[[], object],
    n_games=100,
    seed_base=1234,
    nmoves=200,
):
    stats = MatchResult()

    for game_index in range(n_games):
        start_with_a = game_index % 2 == 0

        ai_a = TimedAIPlayer(ai_factory_a(), "A", stats)
        ai_b = TimedAIPlayer(ai_factory_b(), "B", stats)

        players = [ai_a, ai_b] if start_with_a else [ai_b, ai_a]

        game = NimbyGame(
            players=players,
            start_player=1,
            seed=seed_base + game_index,
            **game_kwargs,
        )

        game.play(nmoves=nmoves, verbose=False)

        if not game.is_over():
            stats.draws += 1
            continue

        winner_slot = game.current_player  # 1 or 2 in current players ordering

        if start_with_a:
            winner_agent = "A" if winner_slot == 1 else "B"
        else:
            winner_agent = "B" if winner_slot == 1 else "A"

        if winner_agent == "A":
            stats.wins_a += 1
        else:
            stats.wins_b += 1

    return stats


def make_negamax_ab(depth):
    return lambda: Negamax(depth)


def make_negamax_noab(depth):
    return lambda: NegamaxNoAB(depth)


def make_expecti_ab(depth):
    return lambda: ExpectiNegamaxAB(depth)


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


def parse_args():
    parser = argparse.ArgumentParser(description="Run Nim/Nimby experiments for lab_01.")
    parser.add_argument(
        "--out",
        default="lab_01/results.json",
        help="Output JSON path (default: lab_01/results.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    out_path = Path(args.out)
    results = run_experiments(out_path)
    print_summary(results)
    print(f"\nSaved results to: {out_path}")


if __name__ == "__main__":
    main()
