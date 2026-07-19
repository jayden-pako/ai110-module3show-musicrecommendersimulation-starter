# user1.py
# A single user's taste profile used as a comparison reference against songs.csv.
#
# Three design fixes over a naive single-point profile:
#   1. Genre is a graded affinity map + a genre-similarity table, so the system
#      can tell that "rock" is closer to "metal" than to "lofi" (not just
#      match / no-match).
#   2. Every numeric feature is a (target, tolerance) RANGE, so energy and
#      valence are decoupled -- an intense mood can want high energy WITHOUT
#      being punished for low valence.
#   3. The user holds MULTIPLE mood profiles (workout, focus, ...), so one
#      listener can express range instead of collapsing to one narrow point.

# ---------------------------------------------------------------------------
# Fix 1: graded genre taste + genre-to-genre similarity
# ---------------------------------------------------------------------------

# How much the user likes each genre outright (0.0 = dislikes, 1.0 = loves).
# Unlisted genres fall back to 0.0 but can still score via genre_similarity.
genre_affinity = {
    "pop": 1.0,
    "indie pop": 0.9,
    "synthwave": 0.8,
    "electronic": 0.75,
    "funk": 0.7,
    "disco": 0.7,
    "r&b": 0.65,
    "hip hop": 0.6,
    "rock": 0.55,
    "reggae": 0.5,
    "lofi": 0.45,
    "jazz": 0.4,
    "blues": 0.35,
    "metal": 0.3,
    "country": 0.3,
    "ambient": 0.25,
    "classical": 0.2,
}

# Symmetric similarity between genres (0.0 = unrelated, 1.0 = same family).
# Lets an unliked genre borrow affinity from a liked neighbour, and lets the
# system rank *similar* genres closer together. Only near pairs are listed;
# missing pairs are treated as 0.0 (and identical genres as 1.0).
genre_similarity = {
    ("pop", "indie pop"): 0.85,
    ("pop", "synthwave"): 0.6,
    ("pop", "funk"): 0.5,
    ("synthwave", "electronic"): 0.8,
    ("electronic", "disco"): 0.65,
    ("disco", "funk"): 0.75,
    ("funk", "r&b"): 0.7,
    ("r&b", "hip hop"): 0.7,
    ("hip hop", "electronic"): 0.5,
    ("rock", "metal"): 0.85,
    ("rock", "blues"): 0.6,
    ("blues", "jazz"): 0.65,
    ("jazz", "r&b"): 0.5,
    ("reggae", "blues"): 0.4,
    ("lofi", "ambient"): 0.7,
    ("lofi", "jazz"): 0.55,
    ("ambient", "classical"): 0.5,
    ("country", "blues"): 0.45,
}


def genre_score(song_genre):
    """Best affinity for a genre: its own affinity, or a liked genre's
    affinity discounted by how similar the two genres are."""
    song_genre = song_genre.lower().strip()
    best = genre_affinity.get(song_genre, 0.0)
    for liked_genre, liked_affinity in genre_affinity.items():
        sim = genre_similarity.get((song_genre, liked_genre)) \
            or genre_similarity.get((liked_genre, song_genre)) \
            or (1.0 if song_genre == liked_genre else 0.0)
        best = max(best, sim * liked_affinity)
    return best


# ---------------------------------------------------------------------------
# Fix 2 + 3: multiple mood profiles, each a set of (target, tolerance) ranges
# ---------------------------------------------------------------------------
# A feature scores 1.0 at its target and falls to ~0.0 once the difference
# exceeds its tolerance. Because energy and valence have SEPARATE tolerances,
# a high-energy / any-valence mood no longer conflicts with itself.
# tempo_bpm tolerance is in BPM; the rest are on the 0.0 - 1.0 scale.

mood_profiles = {
    # Upbeat, danceable, happy -- gym / party listening.
    "workout": {
        "preferred_moods": ["intense", "happy"],
        "features": {
            "energy":        {"target": 0.88, "tolerance": 0.18},
            "valence":       {"target": 0.75, "tolerance": 0.40},  # wide: intensity ok
            "danceability":  {"target": 0.82, "tolerance": 0.25},
            "acousticness":  {"target": 0.10, "tolerance": 0.25},
            "tempo_bpm":     {"target": 130,  "tolerance": 35},
        },
        "weight": 1.0,
    },
    # Calm, low-energy, acoustic -- study / focus listening.
    "focus": {
        "preferred_moods": ["chill", "focused", "relaxed"],
        "features": {
            "energy":        {"target": 0.35, "tolerance": 0.20},
            "valence":       {"target": 0.55, "tolerance": 0.45},  # wide: mood-neutral
            "danceability":  {"target": 0.55, "tolerance": 0.30},
            "acousticness":  {"target": 0.80, "tolerance": 0.30},
            "tempo_bpm":     {"target": 80,   "tolerance": 25},
        },
        "weight": 0.8,
    },
}

# How much each feature pulls the numeric similarity within a mood.
feature_weights = {
    "energy": 1.5,
    "valence": 1.0,
    "danceability": 1.0,
    "acousticness": 1.0,
    "tempo_bpm": 1.0,
}


def _range_score(value, spec):
    """1.0 at target, decaying to 0.0 as |value - target| reaches tolerance."""
    diff = abs(value - spec["target"])
    return max(0.0, 1.0 - diff / spec["tolerance"])


def mood_match(song, mood):
    """Weighted numeric fit of a song to one mood profile (0.0 - 1.0)."""
    profile = mood_profiles[mood]
    total = weighted = 0.0
    for feature, spec in profile["features"].items():
        if feature not in song:
            continue
        w = feature_weights.get(feature, 1.0)
        weighted += w * _range_score(float(song[feature]), spec)
        total += w
    numeric = weighted / total if total else 0.0
    mood_bonus = 1.0 if song.get("mood") in profile["preferred_moods"] else 0.85
    return numeric * mood_bonus


# ---------------------------------------------------------------------------
# The user: graded genre taste + a set of moods. This is the comparison factor.
# ---------------------------------------------------------------------------

user = {
    "name": "User 1",
    "genre_affinity": genre_affinity,
    "genre_similarity": genre_similarity,
    "mood_profiles": mood_profiles,
    "feature_weights": feature_weights,
    # Blend of genre taste vs. how well the song fits ANY of the user's moods.
    "genre_weight": 0.4,
    "mood_weight": 0.6,
}


def score_song(song):
    """Overall taste match for a song dict (keys mirror songs.csv columns).
    Uses the user's best-fitting mood, so a listener with range isn't
    averaged into the middle."""
    g = genre_score(song.get("genre", ""))
    best_mood = max(mood_profiles, key=lambda m: mood_match(song, m))
    m = mood_match(song, best_mood)
    overall = user["genre_weight"] * g + user["mood_weight"] * m
    return overall, best_mood, g, m


if __name__ == "__main__":
    # Demo: prove the profile separates similar genres AND handles range.
    demo_songs = [
        {"title": "Storm Runner",   "genre": "rock",  "mood": "intense",
         "energy": 0.91, "valence": 0.48, "tempo_bpm": 152,
         "danceability": 0.66, "acousticness": 0.10},
        {"title": "Enter Sandman",  "genre": "metal", "mood": "intense",
         "energy": 0.90, "valence": 0.40, "tempo_bpm": 123,
         "danceability": 0.50, "acousticness": 0.00},
        {"title": "Midnight Coding", "genre": "lofi", "mood": "chill",
         "energy": 0.42, "valence": 0.56, "tempo_bpm": 78,
         "danceability": 0.62, "acousticness": 0.71},
        {"title": "Sunrise City",   "genre": "pop",   "mood": "happy",
         "energy": 0.82, "valence": 0.84, "tempo_bpm": 118,
         "danceability": 0.79, "acousticness": 0.18},
    ]

    print(f"Taste profile for {user['name']}\n")
    ranked = sorted(demo_songs, key=lambda s: score_song(s)[0], reverse=True)
    for song in ranked:
        overall, mood, g, m = score_song(song)
        print(f"{song['title']:<16} {song['genre']:<7} "
              f"overall={overall:.2f}  genre={g:.2f}  "
              f"mood_fit={m:.2f} (best: {mood})")
