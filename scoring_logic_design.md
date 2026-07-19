# Scoring Logic Design — Point-Weighting Strategy

This document defines **how every factor is weighted and combined** into a single
score, and — most importantly — **justifies the balance between factors** so the
weights aren't arbitrary. It is the bridge between the raw data (`songs.csv`,
the user profile) and the ranked recommendations.

> **Headline answer to "how much should a Mood match count vs a Genre match?"**
> A full Mood fit is worth **1.5× a full Genre match** (Mood contributes up to
> **0.60** of the final score, Genre up to **0.40**). The reasoning is in §4.

---

## 1. Design principles (the rules the weights must obey)

Every weighting decision below is downstream of five principles. When two weight
choices compete, the one that better serves these wins.

| # | Principle | What it forces the scoring to do |
|---|-----------|----------------------------------|
| P1 | **Transparency over cleverness** | Every point a song earns must be explainable in one sentence ("+0.24 for a strong energy match"). No black-box terms. |
| P2 | **Reward proximity, not magnitude** | A song scores highest *at* the user's target and decays in **either** direction. High energy is not "good" — *matching* the wanted energy is. |
| P3 | **Situational fit leads, taste filters** | *What the user wants right now* (mood + audio feel) is the primary driver; *what genres they like* is the filter that keeps results in-taste. |
| P4 | **Graded, never binary** | Genres and moods are similarities on a 0–1 scale (rock is *closer* to metal than to lofi), not match/no-match. Binary bonuses throw away information. |
| P5 | **Decoupled features** | Each numeric feature is judged on its own (target, tolerance). An intense song can want high energy **without** being punished for low valence. |

---

## 2. The factors and their weights (at a glance)

Two levels of weighting. The **top-level blend** decides how much taste vs.
situational-fit matters. The **feature weights** decide, *within* the situational
fit, which audio features pull hardest.

### Level 1 — Top-level blend (the big decision)

| Factor | Weight | Max contribution | Why this weight |
|--------|:------:|:----------------:|-----------------|
| **Mood fit** (mood + all numeric features) | `0.60` | 0.60 | Primary driver — it answers "does this fit what I want to hear right now?" (P3) |
| **Genre affinity** (graded) | `0.40` | 0.40 | Taste filter — keeps results in genres the user actually likes, but shouldn't override a perfect situational fit |
| **Total** | `1.00` | 1.00 | Score is normalized to 0.0–1.0 |

### Level 2 — Feature weights *inside* mood fit

| Feature | Weight | Why |
|---------|:------:|-----|
| **energy** | `1.5` | Most discriminating & best-spread feature (0.06→0.93 in the catalog); most tied to listening context (gym vs. study). Earns the heaviest pull. |
| **valence** | `1.0` | Meaningful but often given a *wide tolerance* per mood, so it rarely dominates. |
| **danceability** | `1.0` | Baseline. |
| **acousticness** | `1.0` | Baseline; very well-spread, strong separator of "electronic vs. organic". |
| **tempo_bpm** | `1.0` | Baseline. Tolerance is expressed in **BPM** (e.g. ±35), not 0–1, so its raw scale never dominates. |

---

## 3. The point-weighting strategy (how a song earns its score)

A song accumulates points in a fixed "budget" that always sums to 1.0. Think of
it as **60 points for fit, 40 points for taste**, then scaled to 0–1.

```
                          FINAL SCORE (0.0 – 1.0)
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                        │
   MOOD FIT  × 0.60                                     GENRE AFFINITY × 0.40
        │                                                        │
        │  pick the user's BEST-fitting mood profile             │  graded 0–1:
        │  (workout / focus / …) so a listener with              │  own affinity, OR a
        │  range isn't averaged into the middle                  │  liked genre's affinity
        │                                                        │  discounted by genre-to-
        │  mood_fit = numeric × mood_multiplier                  │  genre similarity
        │                                                        │
   ┌────┴───────────────────────────────┐                       │  (rock 0.55 vs. metal
   │ numeric = weighted avg of per-      │                       │   borrowed 0.85×0.55…)
   │ feature closeness (Level-2 weights) │                       │
   │                                     │                       │
   │ mood_multiplier = 1.00 if the song's│                       │
   │ mood ∈ profile.preferred_moods,     │                       │
   │ else 0.85 (a 15% soft penalty —     │                       │
   │ never a hard zero, per P4)          │                       │
   └─────────────────────────────────────┘                      │
```

### 3.1 Per-feature closeness (the atom of the whole system)

For one numeric feature with a `(target, tolerance)` spec:

```
closeness = max(0, 1 − |song_value − target| / tolerance)
```

- `1.0` exactly on target, decaying **linearly** to `0.0` once the song drifts a
  full tolerance away, in **either** direction (P2).
- Tolerance is the "how picky am I about this feature" knob. Wide tolerance on
  valence = "I don't care much about positivity"; tight tolerance on energy =
  "energy must be right." This is how features get **decoupled** (P5).

### 3.2 Numeric aggregate (within one mood)

```
numeric = Σ (feature_weight × closeness) / Σ feature_weight
```

Energy's `1.5` weight means it counts for `1.5 / 5.5 ≈ 27%` of the numeric block
when all five features are present, vs. `18%` each for the others.

### 3.3 Mood fit

```
mood_fit = numeric × mood_multiplier
mood_multiplier = 1.00  if song.mood ∈ profile.preferred_moods
                = 0.85  otherwise
```

The multiplier is a **soft** categorical signal: a song with the right audio
numbers but the "wrong" mood label loses 15%, not everything — because mood
labels overlap and are noisy (P4).

### 3.4 Genre affinity (graded)

```
genre_score = max over every liked genre g of:
                 similarity(song.genre, g) × affinity(g)
similarity(x, x) = 1.0        # identical
similarity(x, y) = table value, else 0.0
```

So a `rock` song (own affinity 0.55) can borrow from `metal` if the user likes
metal, discounted by the 0.85 rock↔metal similarity — it never collapses to a
hard 0 just because "rock" wasn't the #1 pick.

### 3.5 The final combination

```
final_score = 0.60 × mood_fit + 0.40 × genre_score        # already 0.0 – 1.0
```

No extra normalization needed — both inputs are 0–1 and the weights sum to 1.

---

## 4. THE key decision — Mood vs. Genre, and why 0.60 / 0.40

The user asked this directly, and the two source designs **disagreed**, so it
gets a dedicated section.

### The tension in the existing material

| Source | Claim | Encoded as |
|--------|-------|------------|
| `plan.txt` (Phase 2b) | **Genre > Mood** | `genre_bonus 0.20` vs `mood_bonus 0.10` |
| `user1.py` | **Mood > Genre** | `mood_weight 0.6` vs `genre_weight 0.4` |

Both arguments are *locally* correct — they're answering **different questions**:

- **plan.txt is right that genre is the more *reliable signal*.** Genre is stable
  (instrumentation, production), lines up tightly with the audio features, and a
  bare "mood" label like *chill* spans lofi, jazz, and ambient — so as a raw
  clue, a genre match tells you more than a mood label match.
- **user1.py is right about what the recommender is *for*.** People choose music
  by **situation** — "I'm working out," "I need to focus." Mood + the audio feel
  is the *need*; genre is the *preference filter*. A perfect-genre song at the
  wrong energy gets skipped; a great-fit song in an acceptable genre gets played.

### The resolution

The two aren't really in conflict once you separate **signal reliability** from
**decision priority**:

1. **Decision priority → Mood leads (P3).** The product's job is "what should I
   play *now*," so situational fit is the primary axis. Mood gets the larger
   top-level weight: **0.60**.
2. **Signal reliability → genre stays strong and is spent well.** We honor
   plan.txt's insight in *two* places instead of the top-level weight:
   - Genre still gets a large **0.40** — not a token 0.10-style bonus.
   - The unreliable part of "mood" (the noisy categorical label) is demoted to a
     **soft 0.85 multiplier**, while the *reliable* part of mood (the actual
     audio features: energy, tempo, acousticness…) is what fills the 0.60 bucket.

So "Mood" winning doesn't mean "trust the fuzzy label more than genre." It means
**the audio-driven situational fit** wins, and the fuzzy label itself is
deliberately weak.

### Why not 50/50, and why not 70/30

- **50/50** is the "no opinion" answer. The whole point of a design is to commit;
  a tie leaves ranking to whichever block happens to have more spread on a given
  query, which is unstable across users (P3 has no teeth).
- **70/30** makes genre a near-afterthought — a death-metal track would out-rank
  a loved-genre track just for nailing the tempo. That breaks taste-filtering.
- **60/40** keeps mood as the clear driver while genre still has real veto power:
  a 0.40-point genre gap (loved vs. disliked) can only be overcome by a ~0.67
  mood-fit advantage, which requires a genuinely better situational match.

**Net effect on the user's literal question:** a full Mood fit (0.60) is worth
**1.5×** a full Genre match (0.40).

---

## 5. Reliability guardrails (why this balance is "healthy," not fragile)

| Risk | How the weighting defends against it |
|------|--------------------------------------|
| One feature dominates | Everything is normalized 0–1 *before* weighting; tempo's BPM scale is contained by a BPM-denominated tolerance, not raw subtraction. |
| Fuzzy label over-trusted | Categorical mood is only a 0.85–1.0 multiplier; categorical genre is graded, never binary. |
| Listener with range gets averaged to mush | We take the user's **best-fitting** mood profile, not the average across moods. |
| A single missing feature zeroes a song | Aggregate divides by the weight of *present* features only; absent features are skipped, not scored 0. |
| Weights feel arbitrary later | Every weight is a named constant in one place (§6) with a documented "effect if increased." |

---

## 6. Tunable constants (single source of truth)

| Constant | Default | Effect if increased |
|----------|:-------:|---------------------|
| `mood_weight` | `0.60` | Situational/audio fit dominates ranking more |
| `genre_weight` | `0.40` | Taste filtering dominates more (keep the two summing to 1.0) |
| `weight_energy` | `1.5` | Energy pulls harder inside the numeric aggregate |
| `weight_{valence,dance,acoustic,tempo}` | `1.0` | Baseline pull for each |
| `mood_label_penalty` | `0.85` | Raise toward 1.0 to ignore the mood *label*; lower to trust it more |
| feature `tolerance` (per mood) | varies | Wider = "I'm not picky about this feature"; narrower = stricter |
| `k` | `5` | How many songs are returned |

---

## 7. Worked examples

**User 1** (`user1.py`): loves pop (affinity 1.0); moods = *workout* & *focus*.

### Example A — a song that fits both taste and situation
`Sunrise City` — pop, happy, energy 0.82, valence 0.84, dance 0.79, acoustic 0.18, tempo 118

- `genre_score` = 1.00 (pop, direct)
- Best mood = **workout**. Per-feature closeness (targets in `user1.py`):
  energy 0.67 (×1.5), valence 0.78, dance 0.88, acoustic 0.68, tempo 0.66
  → numeric = `(1.5·0.67 + 0.78 + 0.88 + 0.68 + 0.66) / 5.5 ≈ 0.73`
  → mood label *happy* ∈ preferred → multiplier 1.0 → `mood_fit ≈ 0.73`
- **final = 0.60·0.73 + 0.40·1.00 ≈ 0.84** → strong recommendation.

### Example B — great genre, wrong situation
`Clair de Lune` — classical, relaxed, energy 0.06, valence 0.21, tempo 66, acoustic 0.98

- `genre_score` ≈ 0.20 (classical affinity is low; no strong liked-neighbor)
- Best mood = **focus**, but energy 0.06 vs target 0.35 (tol 0.20) → closeness 0;
  acoustic fits well but numeric stays low → `mood_fit ≈ 0.30`
- **final ≈ 0.60·0.30 + 0.40·0.20 ≈ 0.26** → correctly ranked low: neither the
  taste nor the situation matches.

### Example C — showing the 1.5× ratio
Imagine two songs with identical, mediocre mood_fit = 0.50:
- Song X: perfect genre (1.0) → final = 0.60·0.50 + 0.40·1.0 = **0.70**
- Song Y: disliked genre (0.0) → final = 0.60·0.50 + 0.40·0.0 = **0.30**

The 0.40 genre gap is exactly the "value of a full genre match." To beat Song X,
Song Y would need its mood_fit to rise by `0.40 / 0.60 ≈ 0.67` — i.e. a full
genre match ≈ two-thirds of the entire mood-fit range, confirming Mood(0.60) is
1.5× Genre(0.40).

---

## 8. How this maps to code

| Design element | Code location |
|----------------|---------------|
| `genre_score` (graded affinity + similarity) | `data/user1.py::genre_score` |
| per-feature closeness | `data/user1.py::_range_score` |
| numeric aggregate + mood multiplier | `data/user1.py::mood_match` |
| best-mood selection + final blend | `data/user1.py::score_song` |
| top-level weights | `user["genre_weight"]`, `user["mood_weight"]` |
| feature weights | `data/user1.py::feature_weights` |

**Note on `plan.txt` / `src/recommender.py`:** the starter `UserProfile`
(single-point `favorite_genre`, `favorite_mood`, `target_energy`,
`likes_acoustic`) is the *simple* form of this same design. It collapses each
mood profile to one target and each genre to match/no-match. To port these
weights there, use the same **0.60 / 0.40** split but replace graded genre with
a `+0.40 if favorite_genre == song.genre` bonus and mood fit with the single
`target_energy` closeness — the *balance* is identical, only the resolution
drops. If you keep that path, update Phase 2b in `plan.txt` (currently
`genre 0.20 / mood 0.10`) to match this document so the project has one story.
