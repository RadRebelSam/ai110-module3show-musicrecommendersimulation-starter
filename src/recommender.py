from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """

    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """

    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def _user_profile_to_dict(user: UserProfile) -> Dict:
    """Serialize UserProfile into a prefs dict for score_song."""
    return {
        "favorite_genre": user.favorite_genre,
        "favorite_mood": user.favorite_mood,
        "target_energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
    }


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Content-based score for one catalog row (Algorithm recipe from README).

    Point weights:
      - Genre match: +2.0 when song['genre'] == user_prefs['favorite_genre']
      - Mood match: +1.0 when song['mood'] == user_prefs['favorite_mood']
      - Energy similarity: +3.0 * (1 - |song.energy - target_energy|)
        (rewards closeness to the user's target, not higher energy in general)
      - Acoustic alignment (optional): +1.0 when likes_acoustic matches
        song acousticness (>= 0.5 vs < 0.5)

    Returns:
        (total_score, reasons) where each reason is human-readable, e.g.
        "Genre matches 'lofi' (+2.0)".
    """
    user = UserProfile(
        favorite_genre=str(user_prefs["favorite_genre"]),
        favorite_mood=str(user_prefs["favorite_mood"]),
        target_energy=float(user_prefs["target_energy"]),
        likes_acoustic=bool(user_prefs["likes_acoustic"]),
    )
    song_obj = _dict_to_song(song)
    return _score_recipe(user, song_obj)


def _score_recipe(user: UserProfile, song: Song) -> Tuple[float, List[str]]:
    """Apply README scoring rules; return total score and human-readable reasons."""
    total = 0.0
    parts: List[str] = []

    if song.genre == user.favorite_genre:
        total += 2.0
        parts.append(f"Genre matches '{user.favorite_genre}' (+2.0)")

    if song.mood == user.favorite_mood:
        total += 1.0
        parts.append(f"Mood matches '{user.favorite_mood}' (+1.0)")

    energy_pts = 3.0 * (1.0 - abs(song.energy - user.target_energy))
    total += energy_pts
    parts.append(f"Energy similarity (+{energy_pts:.2f})")

    acoustic_aligned = (
        user.likes_acoustic and song.acousticness >= 0.5
    ) or (not user.likes_acoustic and song.acousticness < 0.5)
    if acoustic_aligned:
        total += 1.0
        parts.append("Acoustic preference aligned (+1.0)")

    return total, parts


def _format_explanation(parts: List[str]) -> str:
    """Join scoring reason strings with '; ' for display."""
    return "; ".join(parts)


def _dict_to_song(row: Dict) -> Song:
    """Map a CSV row dict to a Song instance."""
    return Song(
        id=int(row["id"]),
        title=str(row["title"]),
        artist=str(row["artist"]),
        genre=str(row["genre"]),
        mood=str(row["mood"]),
        energy=float(row["energy"]),
        tempo_bpm=float(row["tempo_bpm"]),
        valence=float(row["valence"]),
        danceability=float(row["danceability"]),
        acousticness=float(row["acousticness"]),
    )


def _song_to_dict(song: Song) -> Dict:
    """Serialize a Song to a plain dict."""
    return asdict(song)


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        user_dict = _user_profile_to_dict(user)
        scored: List[Tuple[float, Song]] = []
        for s in self.songs:
            total, _ = score_song(user_dict, _song_to_dict(s))
            scored.append((total, s))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        return [s for _, s in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, parts = score_song(_user_profile_to_dict(user), _song_to_dict(song))
        return _format_explanation(parts)


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file using the csv module.
    Returns a list of dicts with numeric fields converted for math (float / int).

    Required by src/main.py
    """
    path = Path(csv_path)
    rows: List[Dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            if not raw or not any((v or "").strip() for v in raw.values()):
                continue
            row = {
                "id": int(raw["id"]),
                "title": (raw["title"] or "").strip(),
                "artist": (raw["artist"] or "").strip(),
                "genre": (raw["genre"] or "").strip(),
                "mood": (raw["mood"] or "").strip(),
                "energy": float(raw["energy"]),
                "tempo_bpm": int(round(float(raw["tempo_bpm"]))),
                "valence": float(raw["valence"]),
                "danceability": float(raw["danceability"]),
                "acousticness": float(raw["acousticness"]),
            }
            rows.append(row)
    return rows


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, str]]:
    """
    Recommendation = ranking: judge every row in the catalog with `score_song`, then
    sort by score (highest first) and return the top `k` results.

    Tie-break: higher score wins; if scores tie, lower `id` wins (stable ordering).

    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []
    for row in songs:
        total, reasons = score_song(user_prefs, row)
        scored.append((row, total, _format_explanation(reasons)))
    # sorted() returns a new list; it does not mutate `scored` in place.
    ranked = sorted(scored, key=lambda t: (-t[1], t[0]["id"]))
    return ranked[:k]
