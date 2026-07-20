# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**Vibetcha**

A small recommender that matches songs to your vibe: your genre, your mood, and how loud you want it.

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

**Goal / Task.** VibeMatch tries to guess which songs you'll like. You tell it a genre, a mood, and how loud you want the music. It then picks the top 5 songs that fit best. It also explains why it picked each one.

**What it assumes about you.** It assumes you can name your taste in simple words. It assumes one genre, one mood, and one energy level is enough to describe you. It assumes you want the songs that match those choices most closely.

**Intended use.** This is a classroom project. It is for learning how recommenders turn data into suggestions. It is good for trying out "what if" taste profiles and seeing what comes back.

**Non-intended use.** This is not for real users or a real app. Do not use it to make real playlists or business decisions. It only knows 20 songs, so it is not fair to niche tastes. It should not be trusted as a serious measure of what "good" music is.

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

**The idea.** Every song starts with zero points. Then it earns points for each way it matches you. The songs with the most points win.

**How points are earned.**
- Same genre as you asked for: +2 points.
- Same mood as you asked for: +1 point.
- Loudness (energy) close to what you asked for: up to +2 points. The closer it is, the more points it gets.
- Acoustic preference: up to +0.5 points, if you said whether you like acoustic music.

**Turning that into a list.** We add up the points for every song. We sort them from most points to fewest. If two songs tie, the one with the lower song number goes first. Then we show the top 5, along with the reasons each song scored points.

**What changed from the starter.** The starter code was empty and just returned the first few songs. I built the real point system above. I also tested it hard and found some rough spots, like the genre check caring about capital letters.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

**Size.** The catalog is small. It has 20 songs.

**What each song lists.** Each song has a title, artist, genre, and mood. It also has numbers for energy (loudness), tempo, valence (how happy it sounds), danceability, and acousticness.

**Genres and moods.** There are 17 genres, from pop and lofi to metal and classical. But most genres have only one song each. Only pop and lofi have more than one. There are 6 moods: happy, intense, chill, moody, relaxed, and focused. Happy and intense are the most common.

**Did I change the data?** No. I used the starter song list as-is.

**What's missing.** The list is tiny, so it can't cover real music taste. It leans loud: 8 songs are high-energy and only 2 are quiet. The model also ignores three numbers it has: tempo, valence, and danceability. So someone who mainly wants "happy-sounding" or "danceable" songs can't really be matched.

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

**Mainstream tastes work best.** Pop and lofi fans get the best lists, because those are the only genres with more than one song. Their top picks feel right and stay on-genre.

**Loud vs. quiet is handled well.** If you ask for loud music, you get loud songs. If you ask for quiet music, you get calm ones. The energy score does this job cleanly.

**It explains itself.** Every pick comes with plain reasons, like "genre match" or "close energy match." So you can always see why a song was chosen.

**It's steady.** The same request always gives the same answer. Ties are broken the same way every time, so results never jump around.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

**Weakness discovered: genre almost never matters, so energy quietly runs the ranking.**
The scoring rule treats genre as the strongest signal (+2.0), but 15 of the catalog's 17 genres appear on exactly one song, so a genre match can only ever lift a single track and can't differentiate the rest of the list. As a result, the graded energy score (also worth up to +2.0, and awarded to *every* song) is what actually orders the recommendations, which contradicts the design's stated priority. This unfairly favors listeners whose taste sits near the catalog's crowded high-energy region — 8 of 20 songs have energy above 0.7 while only 2 fall below 0.3 — so a low-energy listener keeps getting the same two quiet tracks recommended no matter which genre they ask for. A profile sweep across 510 combinations confirmed it: versatile mid/low-energy songs like *Spacewalk Thoughts* reached 40% of all recommendation lists, while mainstream high-energy pop like *Sunrise City* appeared in only 12%, showing the ranking is driven by energy position rather than the genre the user actually named.

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

### Profiles I tested

I ran three everyday listener profiles through the recommender and read the top 5 songs for each:

- **High-Energy Pop** — likes pop, a happy mood, loud energy (0.88), not acoustic.
- **Chill Lofi** — likes lofi, a calm mood, quiet energy (0.35), likes acoustic.
- **Deep Intense Rock** — likes rock, an intense mood, loud energy (0.90), not acoustic.

I also stress-tested the system with "trick" profiles (a listener who wants a calm mood but very high energy, someone who types "Pop" with a capital P, a made-up mood like "sad") and ran a large sweep of 510 different profiles to see which songs get recommended the most.

### What surprised me

The biggest surprise was that a song can land near the top of your list **without matching the mood you asked for**. For the Happy Pop listener, the loud gym anthem *Gym Hero* came in at #2 even though its mood is tagged "intense," not "happy." In plain terms: the system hands out a big chunk of points just for being the right *style* (pop) and being *about as loud* as you wanted, and those two rewards alone are enough to beat songs that actually match your happy mood. So "Gym Hero" keeps showing up for the Happy Pop crowd because it checks two of the three boxes very strongly — right genre, right loudness — and the system doesn't punish it for having the wrong mood. It just quietly skips the mood bonus and moves on. I also confirmed the capital-letter "Pop" profile silently scored zero on genre, and the made-up "sad" mood was ignored with no warning.

### Comparing the profiles, two at a time

- **High-Energy Pop vs. Chill Lofi:** These are near opposites, and the lists flip completely. Pop fills up with loud, upbeat, non-acoustic tracks (*Sunrise City*, *Gym Hero*), while Lofi fills up with quiet, gentle, acoustic tracks (*Library Rain*, *Midnight Coding*). This makes sense because the two listeners asked for opposite loudness (0.88 vs. 0.35) and opposite feelings about acoustic music, so almost no song can please both.

- **High-Energy Pop vs. Deep Intense Rock:** These two share a lot, and that's the point. Both listeners want loud music (0.88 and 0.90), so both lists are packed with high-energy songs and *Gym Hero* actually appears in both. The only real difference is the very top pick — *Sunrise City* (pop) for one, *Storm Runner* (rock) for the other — because that top slot is where the genre match finally breaks the tie. This makes sense: when two people want the same loudness, they end up seeing many of the same loud songs, and only their favorite genre separates them.

- **Chill Lofi vs. Deep Intense Rock:** This is the sharpest contrast of all, with no shared songs. One list is quiet and acoustic (energy around 0.35), the other is loud and aggressive (energy around 0.90). Every song that scores well for one listener scores badly for the other, which is exactly what you'd want to see — the loudness setting alone is enough to send the two lists in completely different directions.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

1. **Let similar genres count.** Right now a metal fan gets no credit for a rock song. I would add "close genre" points so nearby styles still show up.

2. **Fix the easy bugs and grade the mood.** I would make the genre check ignore capital letters and check that energy is a real number. I would also give partial points for close moods, instead of all-or-nothing.

3. **Use the numbers we ignore, and grow the list.** I would score valence and danceability too, so "happy-sounding" and "danceable" tastes work. I would also add more songs, especially quiet ones, so the list is not so loud-heavy.

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  

I learned that a recommender is really just a points system. Small choices, like how many points genre gets, can change the whole list. The surprising part was that the data mattered more than the rules. Because most genres had only one song, genre barely did anything, and loudness quietly took over. It made me realize that a recommender can look confident and still be biased underneath. Now when a real music app suggests songs, I wonder what it is really scoring, and whose taste it might be quietly leaving out.

### Reflection on My Engineering Process

**What was your biggest learning moment during this project?**
My biggest learning moment was seeing that the data shaped the results more than my rules did. I set genre as the strongest signal. But most genres had only one song. So energy quietly ran the whole ranking. That taught me to test my system against real data, not just my design notes.

**How did using AI tools help you, and when did you need to double-check them?**
AI tools helped me draft the scoring code fast. They also helped me write clear reasons for each pick. I still had to double-check the actual output. I ran the program and read the top songs myself. That is how I caught the capital-letter genre bug and the loud-song bias.

**What surprised you about how simple algorithms can still "feel" like recommendations?**
It surprised me that a plain points system can feel smart. The lists looked personal and confident. But there was no learning behind them at all. It was just addition and sorting. Good explanations made the picks feel more trustworthy than they really were.

**What would you try next if you extended this project?**
I would add more songs, especially quiet ones, so the catalog is balanced. I would let similar genres share points, so a rock song helps a metal fan. I would also score valence and danceability. That would help people who want happy or danceable music.
