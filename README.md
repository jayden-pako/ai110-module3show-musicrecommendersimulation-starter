# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

**Overview**
- This is a rule based recommender.
- It does not learn from behavior.
- It scores each song against a stated taste profile.
- It ranks songs by score.
- It returns the top K.
- It favors transparency over scale.

**Inputs**
- `UserProfile.favorite_genre`
- `UserProfile.favorite_mood`
- `UserProfile.target_energy`
- `UserProfile.likes_acoustic`
- `songs.csv`. One row per song.

**Song features used**
- `genre`. Category match.
- `mood`. Category match.
- `energy`. Numeric closeness.
- `acousticness`. Acoustic preference.
- `valence`, `danceability`, `tempo_bpm`. Optional numeric closeness.

**Algorithm Recipe (finalized)**
- Step 1. Load `songs.csv` into a list.
- Step 2. Cast every numeric field to a float.
- Step 3. Start each song at a total of 0.0.
- Step 4. Add 2.0 if `genre` equals `favorite_genre`.
- Step 5. Add 1.0 if `mood` equals `favorite_mood`.
- Step 6. Add energy points. Formula: `2.0 * max(0, 1 - abs(target_energy - energy))`.
- Step 7. Record a reason for each award.
- Step 8. Repeat Steps 3 to 7 for every song.
- Step 9. Sort by total. Highest first.
- Step 10. Break ties by song `id`. Lowest first.
- Step 11. Return the top K. Default K is 5.
- Step 12. Return an empty result if no song scores above 0.

**Point values**
- Genre match. Plus 2.0.
- Mood match. Plus 1.0.
- Energy closeness. 0.0 up to plus 2.0.
- Maximum score. 5.0.

**Why these weights**
- Genre is a stable taste signal. It earns the most.
- Mood is situational. It earns half of genre.
- Energy is continuous. It earns graded points by closeness.

**Potential biases**
- The system may over prioritize genre. It can bury great songs that match the user mood.
- The genre check needs an exact label. A metal fan gets no credit for a rock song.
- The mood check is all or nothing. A near mood fit earns nothing.
- Only energy uses closeness. Taste in valence and danceability is lost by default.
- The catalog is tiny. Results skew toward the most common genres.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Below is a sample of the recommender's terminal output showing the top recommendations (song titles, scores, and reasons):

```
============================================================
                    TOP RECOMMENDATIONS
============================================================
For your taste  ->  genre: pop  |  mood: happy  |  energy: 0.8
------------------------------------------------------------

1. Sunrise City - Neon Echo                  Score:  4.96
     - genre match: pop (+2.0)
     - mood match: happy (+1.0)
     - close energy match (+1.96)

2. Gym Hero - Max Pulse                      Score:  3.74
     - genre match: pop (+2.0)
     - close energy match (+1.74)

3. Stayin' Alive - Bee Gees                  Score:  2.98
     - mood match: happy (+1.0)
     - close energy match (+1.98)

4. Rooftop Lights - Indigo Parade            Score:  2.92
     - mood match: happy (+1.0)
     - close energy match (+1.92)

5. Uptown Funk - Mark Ronson ft. Bruno Mars  Score:  2.62
     - mood match: happy (+1.0)
     - energy match (+1.62)

============================================================
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



