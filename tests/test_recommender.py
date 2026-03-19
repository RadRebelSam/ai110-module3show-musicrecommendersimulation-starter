from pathlib import Path

from src.recommender import Song, UserProfile, Recommender, load_songs, score_song

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
    }
    total, reasons = score_song(user_prefs, song)
    assert isinstance(total, float)
    assert total > 0
    assert isinstance(reasons, list)
    assert all(isinstance(r, str) for r in reasons)
    assert any("+2.0" in r for r in reasons)
    assert any("+1.0" in r for r in reasons)


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
