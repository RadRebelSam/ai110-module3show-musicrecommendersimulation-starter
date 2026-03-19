"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs

WIDTH = 72


def _reason_lines(explanation: str) -> list[str]:
    """Split semicolon-joined reasons into one line each for display."""
    return [part.strip() for part in explanation.split(";") if part.strip()]


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Taste profile for content-based scoring (matches UserProfile fields in recommender.py)
    user_prefs = {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.38,
        "likes_acoustic": True,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    line = "=" * WIDTH
    print()
    print(line)
    print(f"{'TOP RECOMMENDATIONS':^{WIDTH}}")
    print(line)

    for rank, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        title = song["title"]
        print()
        print(f"  {rank}. {title}")
        print(f"      Score: {score:.2f}")
        print("      Reasons:")
        for reason in _reason_lines(explanation):
            print(f"        - {reason}")
        if rank < len(recommendations):
            print()

    print(line)
    print()


if __name__ == "__main__":
    main()
