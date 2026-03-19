INF = float("inf")


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
