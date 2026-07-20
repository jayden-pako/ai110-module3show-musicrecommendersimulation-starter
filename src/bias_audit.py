"""
Filter-bubble / bias audit for the recommender scoring logic.

Uses recommender.py (score_song / recommend_songs) against data/songs.csv to
measure, empirically:
  A. Catalog shape   -- how genre / mood / energy are distributed.
  B. Coverage bubble -- sweep many diverse profiles, count how often each song
                        reaches a top-5. Songs that never appear are invisible;
                        songs that always appear are the "bubble".
  C. Underserved users -- for each genre a real listener could name, how strong
                        is the best match they can get?

Run:  python src/bias_audit.py
"""

from pathlib import Path
from collections import Counter
from itertools import product

from recommender import load_songs, recommend_songs, score_song

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"


def section(title):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


def catalog_shape(songs):
    section("A. CATALOG SHAPE")
    genres = Counter(s["genre"] for s in songs)
    moods = Counter(s["mood"] for s in songs)
    print(f"\nGenres ({len(genres)} distinct over {len(songs)} songs):")
    for g, n in genres.most_common():
        bar = "#" * n
        flag = "  <- singleton" if n == 1 else ""
        print(f"  {g:<11} {n}  {bar}{flag}")
    singletons = sum(1 for n in genres.values() if n == 1)
    print(f"  => {singletons}/{len(genres)} genres have exactly ONE song.")

    print(f"\nMoods ({len(moods)} distinct):")
    for m, n in moods.most_common():
        print(f"  {m:<9} {n}  {'#' * n}")

    print("\nEnergy distribution (bucketed):")
    buckets = Counter()
    for s in songs:
        e = s["energy"]
        b = "0.0-0.3" if e < 0.3 else "0.3-0.5" if e < 0.5 else \
            "0.5-0.7" if e < 0.7 else "0.7-1.0"
        buckets[b] += 1
    for b in ["0.0-0.3", "0.3-0.5", "0.5-0.7", "0.7-1.0"]:
        print(f"  {b}  {buckets[b]:2d}  {'#' * buckets[b]}")
    hi = sum(1 for s in songs if s["energy"] > 0.7)
    lo = sum(1 for s in songs if s["energy"] < 0.3)
    print(f"  => {hi} songs are high-energy (>0.7), only {lo} are low-energy (<0.3).")


def coverage_bubble(songs):
    section("B. COVERAGE BUBBLE  (sweep of diverse profiles)")
    genres = sorted({s["genre"] for s in songs})
    moods = sorted({s["mood"] for s in songs})
    energies = [0.1, 0.3, 0.5, 0.7, 0.9]

    appearances = Counter()
    n_profiles = 0
    for g, m, e in product(genres, moods, energies):
        n_profiles += 1
        recs = recommend_songs({"genre": g, "mood": m, "energy": e}, songs, k=5)
        for song, _score, _why in recs:
            appearances[song["title"]] += 1

    print(f"\nSwept {n_profiles} profiles ({len(genres)} genres x "
          f"{len(moods)} moods x {len(energies)} energy levels).")
    pct = lambda c: 100 * c / n_profiles

    print("\nMost-recommended (the bubble):")
    for title, c in appearances.most_common(6):
        print(f"  {title:<24} in {c:4d} top-5s  ({pct(c):5.1f}% of profiles)")

    ranked = appearances.most_common()
    print("\nLeast-recommended / invisible:")
    all_titles = {s["title"] for s in songs}
    seen = set(appearances)
    for title in sorted(all_titles - seen):
        print(f"  {title:<24} NEVER appears in any top-5")
    for title, c in ranked[-4:]:
        print(f"  {title:<24} in {c:4d} top-5s  ({pct(c):5.1f}%)")


def underserved_users(songs):
    section("C. UNDERSERVED USERS  (best score a genre fan can get)")
    # A believable listener names a genre + the mood that genre tends to carry.
    genres = sorted({s["genre"] for s in songs})
    print("\nFor each genre, the strongest single match at that genre's own")
    print("best energy (so this is the BEST case for that listener):")
    rows = []
    for g in genres:
        members = [s for s in songs if s["genre"] == g]
        # give the user their genre's own average energy & most common mood
        avg_e = sum(s["energy"] for s in members) / len(members)
        mood = Counter(s["mood"] for s in members).most_common(1)[0][0]
        prof = {"genre": g, "mood": mood, "energy": round(avg_e, 2)}
        top = recommend_songs(prof, songs, k=1)[0]
        rows.append((g, len(members), top[1], top[0]["genre"] == g))
    rows.sort(key=lambda r: r[2])
    print(f"\n  {'genre':<11}{'#songs':>7}{'best score':>12}   top match on-genre?")
    for g, n, sc, on in rows:
        print(f"  {g:<11}{n:>7}{sc:>12.2f}   {'yes' if on else 'NO'}")
    print("\n  (max possible = 5.0; low best-scores = a taste the catalog barely serves)")


def main():
    songs = load_songs(str(CSV_PATH))
    catalog_shape(songs)
    coverage_bubble(songs)
    underserved_users(songs)


if __name__ == "__main__":
    main()
