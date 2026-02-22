# CrisisLens Video Presentation Guide

## Target Length: 2:00 (hard limit)

## Audience

Your judges are **UN humanitarian analysts**, **Databricks engineers**, and **hackathon organizers**. Each cares about different things:

| Judge | What they care about | What to show them |
|-------|---------------------|-------------------|
| **UN reps** | Operational usefulness. "Could I use this Monday morning?" | Cluster-level gaps, reallocation simulator, crisis briefs |
| **Databricks** | Technical depth, pipeline quality, Databricks usage | OCI formula, data pipeline, notebook mention |
| **Hackathon judges** | Rubric: creativity, impact, scope, clarity, soundness | The skit, the demo energy, the "above and beyond" features |

**Tone:** Professional but human. You're presenting to people who see real suffering in these numbers every day. Don't be performative about it — be direct. Let the data speak.

---

## Structure

### 1. THE HOOK (0:00 – 0:20)

**PERSON 1** sits at a desk, papers in hand, news anchor voice. Dress shirt or blazer — sell the bit:

> "Tonight's top stories: the conflict in Ukraine continues. The humanitarian situation in Gaza remains dire. World leaders meet to discuss—"

*Pauses. Shuffles to the next page. Looks at it. Looks at camera.*

> "...South Sudan? 9.9 million people in need? We don't... have anything on that."

*Sets papers down.*

**Hard cut to PERSON 2**, standing, casual:

> "That's the problem. Funding follows headlines, not need. 300 million people need help — and the world only sees the ones on TV."

*Beat.*

> "So we built CrisisLens."

**Why this works for your judges:** The UN reps will recognize this pattern immediately — it's the "forgotten crisis" problem they deal with daily. You're showing them you understand the real issue, not just the data.

---

### 2. THE DEMO (0:20 – 1:25)

Screen recording with Person 2 narrating as voiceover. Pre-load every page. Zero loading spinners. Mouse movements slow and deliberate.

**PERSON 2 (voiceover):**

*(Landing page / Map — show the animated timeline playing, 10 sec)*
> "CrisisLens scores every humanitarian crisis on a single number — the Overlooked Crisis Index. It combines four signals: how many people need help, how much funding is missing, and how invisible the crisis is in global media."

*(Pause animation on 2026, hover over South Sudan — 5 sec)*
> "South Sudan. OCI of 1.0 — the most overlooked crisis in the world."

*(Click into Crisis Drilldown — show the intelligence brief card, 10 sec)*
> "Every crisis gets an intelligence brief. South Sudan: 9.9 million people, severity classification Extreme, 89% funding gap. The most underfunded sector — Camp Coordination — has received literally zero dollars."

*(Scroll to cluster bar chart — 5 sec)*
> "These are cluster-level gaps. Fund managers operate at this level. This is the granularity that matters for reallocation decisions."

*(Navigate to Reallocation Simulator — 15 sec)*
> "And here's where it gets actionable. What happens if we redirect just 10% of funding from better-covered crises to the most overlooked?"

*(Drag the slider from 0 to 10-15%. Pause on the before/after chart.)*
> "That's the projected impact. Millions more people reached. One policy lever."

*(Navigate to Funding Forecast — show South Sudan trend, 8 sec)*
> "The funding gap isn't just bad — it's getting worse. South Sudan's gap has been widening since 2024. Statistically significant. This is an early warning system."

*(Navigate to Efficiency Outliers — show scatter plot, 7 sec)*
> "We also analyzed 8,000 CBPF projects. 265 benchmark projects achieve 15.6 times the median efficiency. Our recommender matches underperforming projects with the best models to learn from."

**Why this works:** You showed UN judges operational depth (cluster gaps, simulator). You showed Databricks judges analytical rigor (OCI formula, forecasts, z-scores). You showed hackathon judges six features in 60 seconds — scope and technical depth.

---

### 3. THE METHODOLOGY (1:25 – 1:45)

**Cut to PERSON 3**, on camera. The OCI formula displayed on a screen or whiteboard behind them:

> "The Overlooked Crisis Index combines three independent signals — people in need as a fraction of population, funding gap, and media neglect from Google Trends — into one reproducible score."

*(Point to the formula behind you)*

> "We integrated five UN data sources, computed OCI across 24 crisis contexts over three years, and ran the full pipeline in Databricks. The methodology is documented in a research paper."

*(Flash the paper PDF on screen for 2 seconds)*

> "Every number is auditable. Every step is reproducible."

**Why this works:** "Auditable" and "reproducible" are the magic words for UN judges. "Databricks" name-drop is essential for that prize pool. The paper flash signals academic rigor.

---

### 4. THE CLOSE (1:45 – 2:00)

**Cut to PERSON 4** (or all four together), direct to camera:

> "91.7% average funding gap across every crisis we track. 13 countries with virtually no media attention. Millions of people in crisis — and almost nobody is watching."

*Pause. Let it land.*

> "CrisisLens doesn't just show the problem. It shows what to do about it. The crises that don't make headlines still need funding."

**End card (5 sec):** "CrisisLens" + team names + GitHub URL. Clean. No music needed.

---

## Timing Summary

| Scene | Duration | Who | Key Audience Hit |
|-------|----------|-----|-----------------|
| 1. Hook skit | 20 sec | Person 1 + 2 | Hackathon (creativity), UN (recognition) |
| 2. Demo | 65 sec | Person 2 voiceover | All three judge groups |
| 3. Methodology | 20 sec | Person 3 | Databricks + UN (rigor) |
| 4. Close | 15 sec | Person 4 | Hackathon (engagement), UN (impact) |
| **Total** | **2:00** | | |

---

## Speaker Assignments

| Person | Role | Screen Time | Notes |
|--------|------|-------------|-------|
| Person 1 | News anchor skit | ~10 sec on camera | Sell the confusion. The joke is the system, not you. |
| Person 2 | Hook line + full demo narration | ~70 sec (mostly voiceover) | Most important role. Rehearse the mouse path. |
| Person 3 | Methodology explanation | ~20 sec on camera | Confidence matters here. You're talking to data scientists. |
| Person 4 | Closing statement | ~15 sec on camera | Direct to camera. No notes. Memorize two lines. |

---

## Key Stats to Overlay as Text

Add these as text overlays during the demo (big, bold, 2-3 seconds each):

- **"9.9M people in need"** (when showing South Sudan)
- **"89% funding gap"** (drilldown)
- **"0% funded"** (Camp Coordination cluster)
- **"15.6x efficiency"** (outlier scatter)
- **"91.7% average gap"** (closing)

---

## Demo Click Path (rehearse this exactly)

1. **Landing page** — let the animated map play for 3 seconds
2. **Overview Map** sidebar — check "Animate Timeline" — let it play 2024 to 2026
3. **Pause on 2026** — hover South Sudan
4. **Crisis Drilldown** — select South Sudan, 2026 — show intelligence brief + cluster chart
5. **Reallocation Simulator** — drag slider from 0% to 15% — show before/after chart
6. **Funding Forecast** — select South Sudan — show the trend line with projection
7. **Efficiency Outliers** — show the scatter plot — hover a green benchmark point

Total: 7 clicks/navigations in 65 seconds. Pre-load everything.

---

## Production Checklist

- [ ] Record skit scenes (1, 3, 4) with phone camera at eye level, good lighting
- [ ] Screen record demo separately (OBS Studio or Windows Game Bar)
- [ ] Pre-load every page before recording — click through once to warm the cache
- [ ] Zoom browser to 110-125% for readability on small screens
- [ ] Record audio in a quiet room — clear voice matters more than video quality
- [ ] Edit in Clipchamp (free, Windows 11) or CapCut
- [ ] Add text overlays for key stats (list above)
- [ ] Export at 1080p
- [ ] Time it — if over 2:00, see cuts below
- [ ] Watch it once as a judge — does it make you care?

---

## What to Cut If Over Time

In order (cut from bottom up):

1. Recommender mention in demo (saves 7 sec)
2. Forecast section in demo (saves 8 sec)
3. Paper flash — just say "documented in a paper", no visual (saves 3 sec)
4. Shorten skit — Person 1 says one headline, not two (saves 5 sec)
5. Last resort: replace skit with white-text-on-black stat: "9.9 million people need help in South Sudan. 89% of required funding hasn't arrived. Almost nobody is talking about it." (saves 10 sec but loses creativity points)

---

## What NOT to Do

- **Don't apologize** ("we ran out of time", "we wish we could have...")
- **Don't explain what a hackathon is** — the judges know
- **Don't say "machine learning" or "AI"** unless you mean it — your strength is statistical methodology, not buzzwords
- **Don't read from a script on camera** — memorize or use a teleprompter app
- **Don't show code** — judges see the repo. The video is for the story.
- **Don't use background music** — it competes with your voice in 2 minutes

---

## Filming Tips

- The skit is 15 seconds. One take. Slight awkwardness is the point — you're a student pretending to be a news anchor. That's the joke.
- Person 1: dress shirt or blazer. Even over a t-shirt. It's a 10-second commitment.
- The demo is 65% of the video. **Rehearse the mouse movements.** Slow, deliberate, no hunting for buttons.
- Person 3: stand in front of a whiteboard with the formula written on it. Or display it on a monitor behind you.
- Person 4's close should be direct to camera, zero notes. Two sentences. Memorize them.
- Hard cuts between scenes — no fade transitions. Feels more urgent in 2 minutes.
- If someone flubs a line, just re-record that 10-second segment. Don't redo the whole thing.
