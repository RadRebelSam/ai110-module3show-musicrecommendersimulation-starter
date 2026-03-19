import math
from pathlib import Path

from src.recommender import (
    Recommender,
    Song,
    UserProfile,
    _greedy_diverse_top_k,
    get_strategy,
    load_songs,
    score_song,
)

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
            popularity=80,
            release_decade="2020s",
            mood_tags="upbeat, bright",
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
            popularity=40,
            release_decade="2020s",
            mood_tags="chill, cozy",
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_score_song_returns_numeric_score_and_reason_strings():
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }
    song = {
        "id": 1,
        "title": "Test",
        "artist": "A",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120,
        "valence": 0.9,
        "danceability": 0.8,
        "acousticness": 0.2,
        "popularity": 80,
        "release_decade": "2020s",
        "mood_tags": "upbeat, bright",
    }
    total, reasons = score_song(user_prefs, song)
    assert isinstance(total, float)
    assert isinstance(reasons, list)
    assert all(isinstance(r, str) for r in reasons)
    joined = " ".join(reasons)
    assert "Genre matches" in joined
    assert "Mood matches" in joined
    assert "Energy similarity" in joined
    # Perfect genre/mood/energy match + acoustic (see _GENRE_MATCH_POINTS, _ENERGY_SIMILARITY_MAX)
    assert math.isclose(total, 1.0 + 1.0 + 6.0 + 1.0)


def test_load_songs_parses_csv_and_numeric_types():
    csv_path = Path(__file__).resolve().parent.parent / "data" / "songs.csv"
    songs = load_songs(str(csv_path))
    assert len(songs) >= 1
    first = songs[0]
    assert isinstance(first["id"], int)
    assert isinstance(first["title"], str)
    assert isinstance(first["energy"], float)
    assert isinstance(first["tempo_bpm"], int)
    assert isinstance(first["valence"], float)
    assert isinstance(first["popularity"], int)
    assert "release_decade" in first


def test_get_strategy_unknown_falls_back_to_balanced():
    assert get_strategy("not_a_real_mode").name == "balanced"


def test_greedy_diversity_skips_second_same_artist_when_better_alternative_exists():
    """Second slot should not be another track from artist A if B is close behind."""
    items = [
        ({"id": 1, "artist": "A", "genre": "pop"}, 10.0, "x"),
        ({"id": 2, "artist": "A", "genre": "pop"}, 9.0, "x"),
        ({"id": 3, "artist": "B", "genre": "pop"}, 8.0, "x"),
    ]
    out = _greedy_diverse_top_k(items, k=2)
    ids = [row["id"] for row, _, _ in out]
    assert ids == [1, 3]


def test_recommend_songs_accepts_diversity_flag():
    """diversity=False uses raw sort; diversity=True uses greedy penalty pass."""
    from src.recommender import recommend_songs

    songs = [
        {
            "id": 1,
            "title": "a",
            "artist": "A",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.8,
            "tempo_bpm": 120,
            "valence": 0.9,
            "danceability": 0.8,
            "acousticness": 0.2,
            "popularity": 80,
            "release_decade": "2020s",
            "mood_tags": "upbeat",
        },
    ]
    prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }
    assert len(recommend_songs(prefs, songs, k=1, diversity=False)) == 1
    assert len(recommend_songs(prefs, songs, k=1, diversity=True)) == 1


def test_advanced_prefs_add_popularity_decade_and_tag_points():
    """When optional keys are set, extra math terms apply."""
    song = {
        "id": 1,
        "title": "Test",
        "artist": "A",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "tempo_bpm": 120,
        "valence": 0.9,
        "danceability": 0.8,
        "acousticness": 0.2,
        "popularity": 80,
        "release_decade": "2020s",
        "mood_tags": "upbeat, nostalgic",
    }
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
        "target_popularity": 80.0,
        "preferred_decade": "2020s",
        "favorite_mood_tags": "upbeat, nostalgic",
    }
    total, reasons = score_song(user_prefs, song)
    joined = " ".join(reasons)
    assert "Popularity match" in joined
    assert "Decade match" in joined
    assert "Mood tags overlap" in joined
    assert total > 9.0


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""
