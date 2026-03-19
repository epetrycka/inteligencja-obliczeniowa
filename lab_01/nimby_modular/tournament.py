import time
from dataclasses import dataclass
from typing import Callable, Dict

from easyAI import AI_Player, Negamax

from .algorithms import ExpectiNegamaxAB, NegamaxNoAB
from .game import NimbyGame


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
