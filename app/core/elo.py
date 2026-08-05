DEFAULT_K_FACTOR = 32


def calculate_elo_change(winner_rating: int, loser_rating: int, k: int = DEFAULT_K_FACTOR) -> int:
    """
    Standard Elo rating adjustment for a two-player match.

    Returns the number of points the winner gains. Elo is zero-sum between
    two players, so the loser loses exactly the same number of points
    (the underlying score deltas S-E are exact opposites, so rounding each
    independently still yields symmetric values).
    """
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    return round(k * (1 - expected_winner))
