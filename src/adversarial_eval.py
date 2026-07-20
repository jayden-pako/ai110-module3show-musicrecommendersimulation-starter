"""
Adversarial / edge-case evaluation harness for the Music Recommender.

Runs a battery of "trick" user profiles through recommend_songs() to probe the
scoring logic in recommender.py for silent failures, crashes, and design gaps.

Each case declares:
  - the profile dict,
  - what weakness it targets,
  - what we EXPECT to happen (so a surprising result is easy to spot).

Run:  python src/adversarial_eval.py
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional

from recommender import load_songs, recommend_songs, score_song

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"


@dataclass
class Case:
    name: str
    profile: Dict
    targets: str          # the weakness being probed
    expectation: str      # what we predict happens


CASES = [
    Case(
        "1. Self-contradicting (intense mood, near-zero energy)",
        {"genre": "rock", "mood": "intense", "energy": 0.05},
        "semantic contradiction between mood and energy (treated as independent)",
        "a calm rock song can out-rank a genuinely intense one; no conflict detected",
    ),
    Case(
        "2. Phantom mood ('sad' exists in no song)",
        {"genre": "pop", "mood": "sad", "energy": 0.8},
        "silent no-op: mood points awarded to nobody, no warning",
        "ranking collapses to genre+energy; mood factor silently absent",
    ),
    Case(
        "3. Case-sensitivity trap ('Pop'/'Happy')",
        {"genre": "Pop", "mood": "Happy", "energy": 0.8},
        "== is case-sensitive; recommender.py never normalizes case",
        "genre+mood score 0 despite looking correct -> likely BUG",
    ),
    Case(
        "4. Out-of-range energy (5.0)",
        {"genre": "pop", "mood": "happy", "energy": 5.0},
        "no input validation; max(0, 1-distance) clamps to 0 for all",
        "every song gets 0 energy points; ranked by genre+mood only -> BUG/degrade",
    ),
    Case(
        "5. Empty profile ({})",
        {},
        "degenerate ranking / fallback determinism",
        "all scores 0.0; returns ids 1-5 in order; 'no strong match'",
    ),
    Case(
        "6. Weight-balance stress (off-genre song with perfect energy)",
        {"genre": "pop", "energy": 0.06},
        "'genre is strongest signal' claim vs a tuned off-genre competitor",
        "classical/ambient tracks with energy~0.06 climb high despite wrong genre",
    ),
    Case(
        "7. Type confusion (energy as string '0.9')",
        {"genre": "pop", "energy": "0.9"},
        "no type coercion on the profile; arithmetic on str",
        "TypeError -> likely CRASH",
    ),
    Case(
        "8. Acoustic contradiction (high-energy intense + likes_acoustic)",
        {"genre": "pop", "mood": "intense", "energy": 0.95, "likes_acoustic": True},
        "cross-factor incoherence; acoustic is a weak 0.5 signal",
        "acoustic nudges ties only; does not drive ranking",
    ),
]


def run_case(case: Case, songs) -> None:
    width = 74
    print("\n" + "=" * width)
    print(case.name)
    print("-" * width)
    print(f"  profile:     {case.profile}")
    print(f"  targets:     {case.targets}")
    print(f"  expectation: {case.expectation}")
    print("-" * width)

    try:
        recs = recommend_songs(case.profile, songs, k=5)
    except Exception as exc:  # deliberately broad: we want to SEE crashes
        print(f"  !! RAISED {type(exc).__name__}: {exc}")
        return

    if not recs or all(score == 0.0 for _, score, _ in recs):
        print("  (all top scores are 0.0 -- no factor contributed)")

    for rank, (song, score, explanation) in enumerate(recs, start=1):
        title = song.get("title", "?")
        genre = song.get("genre", "?")
        energy = song.get("energy", "?")
        print(f"  {rank}. {title:<22} [{genre:<9} e={energy}] "
              f"score={score:5.2f}  <- {explanation}")


def main() -> None:
    songs = load_songs(str(CSV_PATH))
    print(f"Loaded {len(songs)} songs from {CSV_PATH.name}")
    print("ADVERSARIAL EVALUATION -- probing score_song() / recommend_songs()")
    for case in CASES:
        run_case(case, songs)
    print("\n" + "=" * 74)
    print("Done. Compare each block's result against its 'expectation' line.")


if __name__ == "__main__":
    main()
