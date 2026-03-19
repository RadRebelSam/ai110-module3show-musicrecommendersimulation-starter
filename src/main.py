"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs

Switch scoring mode: set SCORING_MODE, or run  python -m src.main mood_first
"""

import sys

from tabulate import tabulate

from .recommender import get_strategy, load_songs, recommend_songs

WIDTH = 72

# Max width for the Reasons column (tabulate wraps / truncates long text).
_REASONS_COL_WIDTH = 64

# Strategy: "balanced" | "genre_first" | "mood_first" | "energy_focused"
SCORING_MODE = "balanced"

# Greedy diversity penalty on artist/genre repeats (see README).
USE_DIVERSITY = True

# Distinct taste profiles (UserProfile-shaped dicts for content-based scoring).
# Each tuple is (display_name, preferences).
STANDARD_PROFILES = [
    (
        "High-Energy Pop",
        {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.85,
            "likes_acoustic": False,
            "target_popularity": 88.0,
            "preferred_decade": "2020s",
            "favorite_mood_tags": "upbeat, euphoric",
        },
    ),
    (
        "Chill Lofi",
        {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.38,
            "likes_acoustic": True,
            "target_popularity": 55.0,
            "preferred_decade": "2020s",
            "favorite_mood_tags": "chill, cozy",
        },
    ),
    (
        "Deep Intense Rock",
        {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.92,
            "likes_acoustic": False,
            "target_popularity": 72.0,
            "preferred_decade": "2010s",
            "favorite_mood_tags": "aggressive, driving",
        },
    ),
]

# Edge-case / adversarial profiles for system evaluation (see README "System Evaluation").
ADVERSARIAL_PROFILES = [
    (
        "Conflicting: max energy + 'melancholic' mood",
        {
            "favorite_genre": "pop",
            "favorite_mood": "melancholic",
            "target_energy": 0.95,
            "likes_acoustic": False,
        },
    ),
    (
        "Genre mismatch: asks 'pop' but catalog uses 'indie pop' for some happy tracks",
        {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.78,
            "likes_acoustic": False,
        },
    ),
    (
        "Acoustic lover + metal genre (production style vs genre)",
        {
            "favorite_genre": "metal",
            "favorite_mood": "aggressive",
            "target_energy": 0.95,
            "likes_acoustic": True,
        },
    ),
]


def _reason_lines(explanation: str) -> list[str]:
    """Split semicolon-joined reasons into one line each for display."""
    return [part.strip() for part in explanation.split(";") if part.strip()]


def _reasons_cell(explanation: str) -> str:
    """One table cell: each reason on its own line for readability."""
    lines = _reason_lines(explanation)
    return "\n".join(lines) if lines else "(no reasons)"


def _print_recommendations(
    profile_name: str,
    user_prefs: dict,
    songs,
    k: int = 5,
    strategy=None,
    diversity: bool = True,
) -> None:
    """Print a formatted block of top-k recommendations for one profile."""
    recommendations = recommend_songs(
        user_prefs, songs, k=k, strategy=strategy, diversity=diversity
    )
    line = "=" * WIDTH
    print()
    print(line)
    print(f"{profile_name.upper():^{WIDTH}}")
    print(line)

    rows = []
    for rank, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        rows.append(
            [
                rank,
                song["title"],
                song["artist"],
                f"{score:.2f}",
                _reasons_cell(explanation),
            ]
        )

    table = tabulate(
        rows,
        headers=["#", "Title", "Artist", "Score", "Reasons"],
        tablefmt="grid",
        maxcolwidths=[4, 28, 22, 8, _REASONS_COL_WIDTH],
        stralign="left",
        numalign="left",
    )
    print(table)
    print(line)


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    mode = SCORING_MODE
    if len(sys.argv) > 1:
        mode = sys.argv[1].strip()
    strategy = get_strategy(mode)
    print(f"Scoring mode: {strategy.name}")
    print(f"Diversity (artist/genre spread): {USE_DIVERSITY}")

    print("\n--- Standard profiles ---")
    for profile_name, user_prefs in STANDARD_PROFILES:
        _print_recommendations(
            profile_name,
            user_prefs,
            songs,
            k=5,
            strategy=strategy,
            diversity=USE_DIVERSITY,
        )

    print("\n--- Adversarial / edge-case profiles ---")
    for profile_name, user_prefs in ADVERSARIAL_PROFILES:
        _print_recommendations(
            profile_name,
            user_prefs,
            songs,
            k=5,
            strategy=strategy,
            diversity=USE_DIVERSITY,
        )

    print()


if __name__ == "__main__":
    main()
