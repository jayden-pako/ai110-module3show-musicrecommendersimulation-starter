"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path

from recommender import load_songs, recommend_songs

# Project root is the folder that contains both src/ and data/.
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"


def print_recommendations(user_prefs: dict, recommendations: list) -> None:
    """Render the ranked recommendations as a clean, readable terminal report."""
    width = 60
    print()
    print("=" * width)
    print("TOP RECOMMENDATIONS".center(width))
    print("=" * width)

    # Echo the profile we recommended for, so the output is self-explanatory.
    profile = "  |  ".join(f"{key}: {value}" for key, value in user_prefs.items())
    print(f"For your taste  ->  {profile}")
    print("-" * width)

    if not recommendations:
        print("\nNo recommendations found.\n")
        print("=" * width)
        return

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        title = song.get("title", "Unknown")
        artist = song.get("artist", "Unknown")

        # Header line: rank, title/artist on the left, score right-aligned.
        header = f"{rank}. {title} - {artist}"
        print(f"\n{header:<45}Score: {score:5.2f}")

        # Each scoring reason on its own indented bullet line.
        reasons = explanation.split(", ") if explanation else []
        if reasons:
            for reason in reasons:
                print(f"     - {reason}")
        else:
            print("     - no strong match")

    print("\n" + "=" * width)


def main() -> None:
    songs = load_songs(str(CSV_PATH))

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print_recommendations(user_prefs, recommendations)


if __name__ == "__main__":
    main()
