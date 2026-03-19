INF = float("inf")


def _negamax(game, depth, orig_depth, scoring, alpha=-INF, beta=INF):
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
        value = -_negamax(game, depth - 1, orig_depth, scoring, -beta, -alpha)

        if unmake_move:
            game.switch_player()
            game.unmake_move(move)

        if value > best_value:
            best_value = value
            best_move = move
            if depth == orig_depth:
                state.ai_move = move

        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best_value


class Negamax:
    def __init__(self, depth, scoring=None, win_score=INF, tt=None):
        self.scoring = scoring
        self.depth = depth
        self.tt = tt
        self.win_score = win_score
        self.alpha = 0.0

    def __call__(self, game):
        scoring = self.scoring if self.scoring else (lambda g: g.scoring())
        self.alpha = _negamax(
            game,
            self.depth,
            self.depth,
            scoring,
            -self.win_score,
            self.win_score,
        )
        return game.ai_move
