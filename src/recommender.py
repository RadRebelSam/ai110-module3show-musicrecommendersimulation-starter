from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Strategy pattern: each mode supplies multipliers for the same scoring steps.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreWeights:
    """Numeric weights for one full pass over the scoring recipe."""

    genre_match: float
    mood_match: float
    energy_max: float
    acoustic: float
    popularity_max: float
    decade_match: float
    mood_tag_per: float
    mood_tag_cap: float


class ScoringStrategy(ABC):
    """Abstract strategy: encapsulates how strongly each signal contributes."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short id, e.g. 'balanced'."""

    @property
    @abstractmethod
    def weights(self) -> ScoreWeights:
        """Weight bundle used by the shared scorer."""

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        user = _prefs_to_user(user_prefs)
        song_obj = _dict_to_song(song)
        return _score_with_weights(user, song_obj, self.weights)


class _ConcreteStrategy(ScoringStrategy):
    def __init__(self, name: str, weights: ScoreWeights) -> None:
        self._name = name
        self._weights = weights

    @property
    def name(self) -> str:
        return self._name

    @property
    def weights(self) -> ScoreWeights:
        return self._weights


# Preset modes (tune these to taste — relative scale is what matters).
WEIGHTS_BALANCED = ScoreWeights(
    genre_match=1.0,
    mood_match=1.0,
    energy_max=6.0,
    acoustic=1.0,
    popularity_max=2.0,
    decade_match=1.5,
    mood_tag_per=0.75,
    mood_tag_cap=2.25,
)

WEIGHTS_GENRE_FIRST = ScoreWeights(
    genre_match=3.0,
    mood_match=0.5,
    energy_max=4.0,
    acoustic=1.0,
    popularity_max=1.5,
    decade_match=2.0,
    mood_tag_per=0.5,
    mood_tag_cap=1.5,
)

WEIGHTS_MOOD_FIRST = ScoreWeights(
    genre_match=0.5,
    mood_match=2.5,
    energy_max=4.0,
    acoustic=1.0,
    popularity_max=1.5,
    decade_match=1.0,
    mood_tag_per=1.0,
    mood_tag_cap=3.0,
)

WEIGHTS_ENERGY_FOCUSED = ScoreWeights(
    genre_match=0.5,
    mood_match=0.5,
    energy_max=10.0,
    acoustic=0.5,
    popularity_max=1.0,
    decade_match=1.0,
    mood_tag_per=0.5,
    mood_tag_cap=1.5,
)

STRATEGY_BALANCED = _ConcreteStrategy("balanced", WEIGHTS_BALANCED)
STRATEGY_GENRE_FIRST = _ConcreteStrategy("genre_first", WEIGHTS_GENRE_FIRST)
STRATEGY_MOOD_FIRST = _ConcreteStrategy("mood_first", WEIGHTS_MOOD_FIRST)
STRATEGY_ENERGY_FOCUSED = _ConcreteStrategy("energy_focused", WEIGHTS_ENERGY_FOCUSED)

DEFAULT_STRATEGY: ScoringStrategy = STRATEGY_BALANCED

STRATEGY_BY_NAME: Dict[str, ScoringStrategy] = {
    STRATEGY_BALANCED.name: STRATEGY_BALANCED,
    STRATEGY_GENRE_FIRST.name: STRATEGY_GENRE_FIRST,
    STRATEGY_MOOD_FIRST.name: STRATEGY_MOOD_FIRST,
    STRATEGY_ENERGY_FOCUSED.name: STRATEGY_ENERGY_FOCUSED,
}

# Diversity: penalize picking another song with the same artist/genre as already chosen.
_DIVERSITY_ARTIST_PENALTY = 1.5
_DIVERSITY_GENRE_PENALTY = 1.0


def get_strategy(mode: Optional[str] = None) -> ScoringStrategy:
    """Resolve a strategy id to a ScoringStrategy; unknown -> balanced."""
    if not mode:
        return DEFAULT_STRATEGY
    return STRATEGY_BY_NAME.get(mode.strip().lower(), DEFAULT_STRATEGY)


def _diversity_adjusted_score(
    raw_score: float,
    row: Dict,
    selected_rows: List[Dict],
    artist_penalty: float = _DIVERSITY_ARTIST_PENALTY,
    genre_penalty: float = _DIVERSITY_GENRE_PENALTY,
) -> float:
    """
    Subtract a penalty for each song already in the shortlist with the same
    artist or genre (fairness / spread across the catalog).
    """
    artist = str(row.get("artist", "")).strip()
    genre = str(row.get("genre", "")).strip()
    same_artist = sum(
        1 for r in selected_rows if str(r.get("artist", "")).strip() == artist
    )
    same_genre = sum(
        1 for r in selected_rows if str(r.get("genre", "")).strip() == genre
    )
    return raw_score - artist_penalty * same_artist - genre_penalty * same_genre


def _greedy_diverse_top_k(
    scored: List[Tuple[Dict, float, str]],
    k: int,
) -> List[Tuple[Dict, float, str]]:
    """
    Build top-k by repeatedly picking the best *diversity-adjusted* score among
    remaining candidates (not raw global sort).
    """
    remaining = list(scored)
    selected: List[Tuple[Dict, float, str]] = []
    while len(selected) < k and remaining:
        sel_rows = [row for row, _, _ in selected]

        def sort_key(item: Tuple[Dict, float, str]) -> Tuple[float, float, int]:
            row, raw, _ = item
            adj = _diversity_adjusted_score(raw, row, sel_rows)
            return (adj, raw, -int(row["id"]))

        best = max(remaining, key=sort_key)
        remaining.remove(best)
        selected.append(best)
    return selected


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
    popularity: int
    release_decade: str
    mood_tags: str


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
    target_popularity: Optional[float] = None
    preferred_decade: str = ""
    favorite_mood_tags: str = ""


def _split_tags(tag_str: str) -> Set[str]:
    """Lowercase comma-separated tags for overlap scoring."""
    return {t.strip().lower() for t in tag_str.split(",") if t.strip()}


def _user_profile_to_dict(user: UserProfile) -> Dict:
    """Serialize UserProfile into a prefs dict for score_song."""
    d: Dict = {
        "favorite_genre": user.favorite_genre,
        "favorite_mood": user.favorite_mood,
        "target_energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
        "preferred_decade": user.preferred_decade,
        "favorite_mood_tags": user.favorite_mood_tags,
    }
    if user.target_popularity is not None:
        d["target_popularity"] = user.target_popularity
    return d


def _prefs_to_user(user_prefs: Dict) -> UserProfile:
    return UserProfile(
        favorite_genre=str(user_prefs["favorite_genre"]),
        favorite_mood=str(user_prefs["favorite_mood"]),
        target_energy=float(user_prefs["target_energy"]),
        likes_acoustic=bool(user_prefs["likes_acoustic"]),
        target_popularity=(
            float(user_prefs["target_popularity"])
            if "target_popularity" in user_prefs
            else None
        ),
        preferred_decade=str(user_prefs.get("preferred_decade", "")).strip(),
        favorite_mood_tags=str(user_prefs.get("favorite_mood_tags", "")).strip(),
    )


def score_song(
    user_prefs: Dict,
    song: Dict,
    strategy: Optional[ScoringStrategy] = None,
) -> Tuple[float, List[str]]:
    """
    Content-based score for one catalog row. Delegates to the given strategy
    (default: balanced). Strategies swap ScoreWeights, not the feature logic.
    """
    strat = strategy or DEFAULT_STRATEGY
    return strat.score(user_prefs, song)


def _score_with_weights(
    user: UserProfile, song: Song, w: ScoreWeights
) -> Tuple[float, List[str]]:
    """Single scoring pass using the supplied weight bundle."""
    total = 0.0
    parts: List[str] = []

    if song.genre == user.favorite_genre:
        total += w.genre_match
        parts.append(
            f"Genre matches '{user.favorite_genre}' (+{w.genre_match:.1f})"
        )

    if song.mood == user.favorite_mood:
        total += w.mood_match
        parts.append(f"Mood matches '{user.favorite_mood}' (+{w.mood_match:.1f})")

    energy_pts = w.energy_max * (1.0 - abs(song.energy - user.target_energy))
    total += energy_pts
    parts.append(f"Energy similarity (+{energy_pts:.2f})")

    acoustic_aligned = (
        user.likes_acoustic and song.acousticness >= 0.5
    ) or (not user.likes_acoustic and song.acousticness < 0.5)
    if acoustic_aligned:
        total += w.acoustic
        parts.append(f"Acoustic preference aligned (+{w.acoustic:.1f})")

    if user.target_popularity is not None:
        tp = max(0.0, min(100.0, float(user.target_popularity)))
        sp = max(0.0, min(100.0, float(song.popularity)))
        pop_pts = w.popularity_max * (1.0 - abs(sp / 100.0 - tp / 100.0))
        total += pop_pts
        parts.append(f"Popularity match (+{pop_pts:.2f})")

    pref_dec = user.preferred_decade.strip()
    if pref_dec and song.release_decade.strip() == pref_dec:
        total += w.decade_match
        parts.append(f"Decade match '{pref_dec}' (+{w.decade_match:.1f})")

    if user.favorite_mood_tags.strip():
        want = _split_tags(user.favorite_mood_tags)
        have = _split_tags(song.mood_tags)
        overlap = want & have
        if overlap:
            tag_pts = min(
                w.mood_tag_cap,
                w.mood_tag_per * float(len(overlap)),
            )
            total += tag_pts
            tags_show = ", ".join(sorted(overlap))
            parts.append(f"Mood tags overlap [{tags_show}] (+{tag_pts:.2f})")

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
        popularity=int(round(float(row.get("popularity", 50)))),
        release_decade=str(row.get("release_decade", "") or "").strip(),
        mood_tags=str(row.get("mood_tags", "") or "").strip(),
    )


def _song_to_dict(song: Song) -> Dict:
    """Serialize a Song to a plain dict."""
    return asdict(song)


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(
        self,
        songs: List[Song],
        strategy: Optional[ScoringStrategy] = None,
    ):
        self.songs = songs
        self.strategy = strategy or DEFAULT_STRATEGY

    def recommend(
        self,
        user: UserProfile,
        k: int = 5,
        strategy: Optional[ScoringStrategy] = None,
        diversity: bool = True,
    ) -> List[Song]:
        strat = strategy or self.strategy
        user_dict = _user_profile_to_dict(user)
        scored: List[Tuple[float, Song]] = []
        for s in self.songs:
            total, _ = score_song(user_dict, _song_to_dict(s), strategy=strat)
            scored.append((total, s))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        if not diversity:
            return [s for _, s in scored[:k]]
        triples: List[Tuple[Dict, float, str]] = []
        for raw, s in scored:
            triples.append((_song_to_dict(s), raw, ""))
        picked = _greedy_diverse_top_k(triples, k)
        return [_dict_to_song(row) for row, _, _ in picked]

    def explain_recommendation(
        self,
        user: UserProfile,
        song: Song,
        strategy: Optional[ScoringStrategy] = None,
    ) -> str:
        strat = strategy or self.strategy
        _, parts = score_song(
            _user_profile_to_dict(user), _song_to_dict(song), strategy=strat
        )
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
                "popularity": int(round(float(raw.get("popularity", 50)))),
                "release_decade": (raw.get("release_decade") or "").strip(),
                "mood_tags": (raw.get("mood_tags") or "").strip(),
            }
            rows.append(row)
    return rows


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: Optional[ScoringStrategy] = None,
    diversity: bool = True,
) -> List[Tuple[Dict, float, str]]:
    """
    Recommendation = ranking: judge every row with the chosen strategy, then
    sort by score (highest first) and return the top `k` results.

    If ``diversity`` is True (default), top-k is chosen with a greedy rule that
    penalizes picking another song whose artist or genre already appears in the
    shortlist (see ``_diversity_adjusted_score``).

    Tie-break: higher score wins; if scores tie, lower `id` wins (stable ordering).

    Required by src/main.py
    """
    strat = strategy or DEFAULT_STRATEGY
    scored: List[Tuple[Dict, float, str]] = []
    for row in songs:
        total, reasons = score_song(user_prefs, row, strategy=strat)
        scored.append((row, total, _format_explanation(reasons)))
    ranked = sorted(scored, key=lambda t: (-t[1], t[0]["id"]))
    if not diversity:
        return ranked[:k]
    return _greedy_diverse_top_k(ranked, k)
