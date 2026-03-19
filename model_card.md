# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeTape 1.0** — a small content-based music picker for our classroom catalog.

---

## 2. Intended Use and Non-Intended Use

**Intended use:** Pick songs from a **fixed CSV list** that **fit a simple taste profile** (favorite genre, mood, target energy, and acoustic vs studio lean). It is for **learning and demos**, not for shipping a real app.

**Non-intended use:** Do **not** use this for real users, A/B tests, or anything that needs fairness, scale, or fresh music. It does **not** learn from clicks or streams. It is **not** medical, legal, or safety advice.

**Goal / task:** Suggest **which tracks in our tiny library** best match a **made-up listener profile**. It predicts **nothing about the real world**—it only **ranks rows** we already have.

---

## 3. How the Model Works (Algorithm Summary)

Each song has **genre**, **mood**, **energy** (0–1), **acousticness**, **popularity** (0–100), **release decade**, and **mood tags** (comma-separated words like *nostalgic* or *euphoric*). **Tempo** and **valence** are still in the file but **not** in the score unless we add them later.

The user picks **genre**, **mood**, **target energy**, and **acoustic** taste. They **can** also set a **target popularity**, a **preferred decade**, and **favorite mood tags**—if they skip those, the model ignores them.

The score **adds points** for: genre, mood, **energy distance**, acoustic fit, and (when provided) **popularity distance** on a 0–100 scale, an **exact decade** match, and **shared mood tags** (each overlap adds a little, with a cap). We still use the **weight experiment** that **lowered genre** and **raised energy** so we can see sensitivity.

Higher total score = **more recommended**. There is **no machine learning**—just rules and addition.

---

## 4. Data Used

The catalog has **18 songs** in a CSV. Each row has title, artist, **genre**, **mood**, **energy**, **tempo**, **valence**, **danceability**, **acousticness**, plus **popularity** (0–100), **release_decade** (e.g. `2020s`), and **mood_tags** (comma-separated fine-grained tags like `nostalgic, warm`).

**Limits:** The list is **tiny**. Many genres appear **once**. **Lofi** shows up **three** times, so “favorite lofi” keeps seeing the **same** small set. **Indie pop** is **not** spelled **pop**, so the model treats them as **different**. Whole areas of taste (languages, lyrics) are still **missing**.

---

## 5. Strengths

It is **easy to explain** why a song ranked high—the app prints **reasons** with the score.

For profiles that **match the tags** (e.g. chill lofi with low energy), the top picks often **feel right**.

Same code path for **every** song, so behavior is **predictable** for class discussion.

---

## 6. Limitations and Bias (Observed Behavior)

**Energy** gets a slice of points for **every** song. After we **boosted** energy in the experiment, **energy-near** tracks could **beat** better genre or mood fits—like a **filter bubble** on one dial.

**Mood and genre** must match **exact text**. A “happy pop” seeker can still see **intense** pop (**Gym Hero**) high on the list because **genre + energy + acoustic** still add up—even without a **happy** mood match.

**Valence**, **danceability**, and **tempo** are in the file but **not** in the score, so listeners who care about those are **ignored**.

---

## 7. Evaluation Process

We ran **`python -m src.main`** so every profile could **see** ranked lists and reasons.

We tested **three** normal profiles (**High-Energy Pop**, **Chill Lofi**, **Deep Intense Rock**) and **three** **stress-test** profiles (weird mixes of energy and mood, **pop** vs **indie pop**, **metal** + acoustic).

We compared **before and after** the weight experiment and read the **printed reasons** to see if they matched our intuition.

---

## 8. Future Work (Ideas for Improvement)

Add **diversity rules** so the top five are not **all** the same artist or genre.

Fold in **valence** or **tempo** (scaled fairly) so “happy” is not only a **string match**.

Let **genre** fuzzy-match (e.g. map **indie pop** toward **pop**) or let users pick **more than one** genre.

---

## 9. Personal Reflection

**Biggest learning moment:** Separating **“the recipe on paper”** from **what users experience** was harder than I expected. Writing down genre points and energy points felt tidy; then **Gym Hero** still sat high for “happy pop” because the system only checks **exact words** and **numbers**, not feelings. That gap between spec and story was the real lesson.

**AI tools:** They sped up **boilerplate** (CSV loading, sorting, README structure) and helped me phrase tradeoffs in plain language. I still had to **run the code**, **read the CSV**, and **trace the score** myself whenever something looked wrong—especially after the **weight experiment**, where the list moved in ways the prose did not predict. AI suggestions are a draft; **the terminal and tests** are the truth.

**Why simple rules still “feel” like recommendations:** Even a handful of weighted checks produces an ordered list with **reasons** next to each song. Our brains treat that like a **judgment**, not a spreadsheet. That’s a little uncanny: **no ML**, but it still **nudges** what I notice first.

**What I would try next:** Add **diversity** (don’t let one artist dominate), **soften genre** so “indie pop” can talk to “pop,” and maybe a **second pass** that down-ranks repeats. I’d also log **scores for every song** once to see the long tail—not just the top five.

---

*For the engineering angle: this project reminded me that “simple” systems still need the same habits as big ones—clear specs, edge-case profiles, and a model card so future-me knows what we optimized for.*
