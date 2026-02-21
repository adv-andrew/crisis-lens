# CrisisLens Video Presentation Guide

## Target Length: 3–4 minutes

---

## Structure

### 1. THE HOOK (0:00 – 0:30)

**Visual:** Black screen. White text fades in one line at a time.

> "33.7 million people in Sudan need humanitarian aid."
> "94.9% of the funding hasn't arrived."
> "And nobody is talking about it."

**Cut to:** Team member on camera.

> "We built CrisisLens to find the crises the world is missing."

---

### 2. THE PROBLEM (0:30 – 1:00)

**Who speaks:** One person, casual and direct. Not reading a script.

**Visual:** Show the double-neglect scatter plot (media neglect vs funding gap) on screen while talking.

**Key points to hit:**
- "Humanitarian funding doesn't follow need. It follows headlines."
- "Ukraine and Palestine get media coverage and proportionally more funding. South Sudan, Chad, Central African Republic — equally severe, but invisible."
- Point at the upper-right quadrant of the scatter plot: "These countries are underfunded AND invisible. That's the worst place to be."

---

### 3. LIVE DEMO (1:00 – 2:30)

**Visual:** Clean screen recording of the Streamlit app. No bookmarks bar, no extra tabs.

**Demo flow (rehearse this exact sequence):**

1. **Landing page** — Show the headline stats. "The average funding gap across all crises is 91.7%."
2. **Map page** — Hover over red countries. "Darker red means more overlooked." Click South Sudan.
3. **Crisis Drilldown** — Show the OCI component breakdown. "Camp Coordination has a 100% funding gap. Logistics 99.3%. These clusters have received almost nothing."
4. **Reallocation Simulator** — Drag the slider from 0% to 15%. "What if we moved just 15% of funding from well-funded crises to the most overlooked? Here's what happens." Let the bar chart animate.
5. **Forecast page** — Show South Sudan's funding gap trend. "The gap isn't just bad — it's getting worse. Statistically."
6. **Recommender** — Quick flash. "And we can tell you which efficient projects to scale — these benchmarks achieve 15.6 times the median cost-effectiveness."

**Demo recording tips:**
- Zoom browser to 110–125% so text is readable on small screens
- Move the mouse slowly and deliberately
- Pre-load everything so there's zero spinner time
- Dark mode on your OS looks more polished

---

### 4. TECHNICAL DEPTH (2:30 – 3:15)

**Visual:** Show the OCI formula (screenshot from the paper or notebook).

**Who speaks:** A different team member. Walk through the formula in plain English:

> "We take how many people need help, normalize by population, multiply by how severe the crisis is, multiply by how underfunded it is, and then boost the score if nobody's even talking about it. Four signals, one number."

**Then flash the notebook briefly (2–3 seconds):**

> "The full pipeline runs on Databricks, writes to Delta Lake, and reproduces every number."

**Then hold up the paper or show the PDF (2 seconds):**

> "We also wrote a research paper documenting the full methodology, results, and limitations."

---

### 5. THE CLOSE (3:15 – 3:45)

**Visual:** Back to team on camera. One person delivers the closing.

> "The crises that don't make headlines still need funding. CrisisLens gives decision-makers the data to act on the ones the world is forgetting."

**End card:** Team name, GitHub link, tagline.

---

## Speaker Assignments (4 people, ~45 sec each)

| Section | Speaker | Time |
|---------|---------|------|
| Hook + Problem | Person 1 (strongest speaker) | 0:00 – 1:00 |
| Live Demo (narrating) | Person 2 (knows the app best) | 1:00 – 2:30 |
| Technical Depth | Person 3 | 2:30 – 3:15 |
| Close | Person 4 (or Person 1 for bookend) | 3:15 – 3:45 |

Practice the handoffs. "And here's [name] to walk you through the app."

---

## Production Checklist

- [ ] Record audio in a quiet room — audio matters more than video quality
- [ ] Use earbuds as mic if laptop mic is bad
- [ ] Screen record with OBS (free) or Windows Snipping Tool
- [ ] Edit in Clipchamp (free, built into Windows 11)
- [ ] Record demo and talking-head separately, splice together
- [ ] Add text overlays for key stats ("91.7%", "15.6x", "265 benchmarks")
- [ ] Export at 1080p minimum

---

## What NOT to Do

- Don't open with "Hi we're team CrisisLens and we built a dashboard"
- Don't spend time on setup/install instructions
- Don't show code scrolling (judges don't care about your imports)
- Don't read from a script word-for-word (use bullet notes, be natural)
- Don't apologize ("we didn't have time to..." — just skip it)
- Don't show the notebook cell-by-cell

---

## Skit Ideas

### Option A: "The News Anchor"

Open with one team member sitting at a desk pretending to be a news anchor. Papers shuffled, serious face.

> "Breaking news tonight: the conflict in [well-known crisis] continues to dominate headlines. Meanwhile—"

Cut to black. Text on screen: "Meanwhile, 13 crises received less than 30% of median media attention."

Back to the "anchor" who looks uncomfortable. Shuffles papers.

> "We... don't have anything on those."

Cut to another team member: "That's the problem. Let us show you."

Transition into the demo.

**Why this works:** It literally demonstrates the media attention bias your project measures. The skit IS the thesis.

---

### Option B: "The Donor's Dilemma"

Two team members. One is a "donor" sitting at a laptop. The other is standing behind them looking over their shoulder.

**Donor:** "Okay, I've got $10 million to allocate. Where should it go?"
**Advisor:** "Well, Sudan has 33 million people in need—"
**Donor:** "Sudan... I haven't seen anything about Sudan lately. What about [well-known crisis]?"
**Advisor:** "That one's already at 60% funding coverage."
**Donor:** "But it's all over the news. We should fund what people care about."
**Advisor:** "Or... we could fund what people need."

Beat. Donor looks at the camera.

> "We built a tool for that."

Cut to CrisisLens demo.

**Why this works:** It shows the exact decision-making failure your tool addresses, in a human and slightly funny way.

---

### Option C: "The Scroll" (low-effort, high-impact)

One person scrolling through their phone. Fast cuts of news headlines (Ukraine, Palestine, etc.) appearing on screen. Scrolling, scrolling.

Suddenly the phone shows a blank screen. Text overlay:

> "South Sudan. OCI: 1.000. 9.9 million people in need. 89.5% funding gap."
> "You've never seen this headline."

Person looks up from the phone at the camera.

> "That's why we built CrisisLens."

**Why this works:** Minimal setup, no acting required, and it mirrors how most people actually consume (or miss) crisis information.

---

### Option D: "The Whiteboard Pitch" (safest option)

Skip the skit. One person stands at a whiteboard (or holds a tablet showing a drawn diagram). Draws the OCI formula components while explaining them in plain English. Circle the media neglect term.

> "This is the part nobody else measures."

Simple, clean, professional. If your team isn't comfortable acting, this is the move.

---

## Recommended Approach

If your team has any acting energy: **Option A (News Anchor)** or **Option C (The Scroll)**. They're short (15–20 seconds), easy to film, and directly connect to the project's thesis.

If you want safe and polished: **Option D (Whiteboard)**.

Avoid anything longer than 30 seconds for the skit — it should set up the problem, not become the video.
