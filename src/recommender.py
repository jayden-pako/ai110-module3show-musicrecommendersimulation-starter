import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# --- Scoring constants (Phase 4 Point System — single source of truth) --------
# See scoring_logic_design.md / plan.txt for the fairness rationale behind these.
GENRE_PTS = 2.0            # exact genre match: strongest, most stable taste signal
MOOD_PTS = 1.0             # exact mood match: situational, worth half of genre
ENERGY_MAX = 2.0           # graded energy closeness caps at the same weight as genre
ACOUSTIC_PTS = 0.5         # optional secondary signal (only if likes_acoustic given)
ENERGY_CLOSE_THRESHOLD = 0.15   # |target - energy| within this counts as a "close" match

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

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked by how well they match the user profile."""
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended to the user."""
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    # Columns that should be whole numbers, everything else numeric is a float.
    int_fields = {"id", "tempo_bpm"}
    float_fields = {"energy", "valence", "danceability", "acousticness"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = dict(row)
            for field in int_fields:
                if field in song:
                    song[field] = int(song[field])
            for field in float_fields:
                if field in song:
                    song[field] = float(song[field])
            songs.append(song)

    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    # Implements the Phase 4 Point System: a song starts at 0.0 and EARNS points
    # for each way it matches the user. Every award also emits a human-readable
    # reason in the "<factor> (+points)" form so the recommendation is explainable.
    #
    # user_prefs is the dict main.py builds, e.g.
    #   {"genre": "pop", "mood": "happy", "energy": 0.8}
    # (an optional "likes_acoustic": bool enables the P4 acoustic award).

    total = 0.0
    reasons: List[str] = []

    # P1 — Genre match (+2.0): exact, high-confidence taste signal.
    fav_genre = user_prefs.get("genre") or user_prefs.get("favorite_genre")
    if fav_genre is not None and song.get("genre") == fav_genre:
        total += GENRE_PTS
        reasons.append(f"genre match: {fav_genre} (+{GENRE_PTS:.1f})")

    # P2 — Mood match (+1.0): real but situational, so worth half of genre.
    fav_mood = user_prefs.get("mood") or user_prefs.get("favorite_mood")
    if fav_mood is not None and song.get("mood") == fav_mood:
        total += MOOD_PTS
        reasons.append(f"mood match: {fav_mood} (+{MOOD_PTS:.1f})")

    # P3 — Energy closeness (0.0–2.0): graded, rewards proximity to the target
    # (a near miss still earns most of the points; a large miss earns almost none).
    target_energy = user_prefs.get("energy", user_prefs.get("target_energy"))
    if target_energy is not None and "energy" in song:
        distance = abs(target_energy - song["energy"])
        energy_pts = ENERGY_MAX * max(0.0, 1.0 - distance)
        total += energy_pts
        label = "close energy match" if distance <= ENERGY_CLOSE_THRESHOLD else "energy match"
        reasons.append(f"{label} (+{energy_pts:.2f})")

    # P4 — Acoustic preference (0.0–0.5, optional): only when the user expressed one.
    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None and "acousticness" in song:
        acoustic = song["acousticness"]
        acoustic_pts = ACOUSTIC_PTS * (acoustic if likes_acoustic else 1.0 - acoustic)
        total += acoustic_pts
        pref = "acoustic" if likes_acoustic else "non-acoustic"
        reasons.append(f"{pref} preference (+{acoustic_pts:.2f})")

    return total, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    # Score every song, then rank (Phase 3 rules R7-R9).
    # Pythonic: one comprehension scores all songs; each item pairs the song with
    # its (score, reasons) so we never re-score during sorting.
    scored = [(song, *score_song(user_prefs, song)) for song in songs]

    # R7 sort by score DESC, R8 tie-break by song id ASC (stable, repeatable).
    # A tuple key sorts by score descending first, then id ascending.
    scored.sort(key=lambda item: (-item[1], item[0].get("id", 0)))

    # R9 take the top k, turning each song's reason list into one explanation string.
    return [
        (song, score, ", ".join(reasons) if reasons else "no strong match")
        for song, score, reasons in scored[:k]
    ]
