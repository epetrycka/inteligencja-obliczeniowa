import random
from typing import List, Tuple

from easyAI import TwoPlayerGame


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
