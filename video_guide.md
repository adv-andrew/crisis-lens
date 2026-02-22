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

### 2. THE DEMO (0:20 – 1:15)

Screen recording, Person 2 narrates as voiceover. Pre-load every page. Zero spinners.

**PERSON 2 (voiceover):**

*(Map with animated timeline playing — 8 sec)*
> "CrisisLens scores every crisis on one number — the Overlooked Crisis Index. Severity, funding gaps, and media attention. Darker red, more overlooked."

*(Pause on 2026, hover South Sudan — 3 sec)*
> "South Sudan — most overlooked crisis in the world."

*(Crisis Drilldown — intelligence brief + cluster chart visible, 10 sec)*
> "Drill in: 9.9 million people in need, 89% funding gap. Camp Coordination — zero percent funded. This is the cluster-level view fund managers actually use."

*(Reallocation Simulator — drag slider, 12 sec)*
> "What if we redirected 10% from better-funded crises?"
*(drag slider)*
> "Millions more people reached. One policy change."

*(Funding Forecast — South Sudan trend, 7 sec)*
> "And the gap is widening. Statistically significant. This is an early warning system."

*(Quick flash of Outlier scatter + Recommender table — 5 sec)*
> "We benchmarked 8,000 projects. The top performers are 15x more efficient. The recommender finds the best models to scale."

---

### 3. THE METHODOLOGY (1:15 – 1:35)

**Cut to PERSON 3**, on camera. Formula on screen behind them:

> "OCI combines people in need, funding gap, and media neglect into one score. Five UN data sources, 24 crises, three years. Pipeline runs on Databricks. Documented in a research paper."

*(Flash paper PDF — 1 second)*

> "Every number is auditable. Every step is reproducible."

---

### 4. THE CLOSE (1:35 – 1:55)

**Cut to PERSON 4**, direct to camera:

> "91% average funding gap. 13 countries with almost zero media coverage. Millions of people — and nobody's watching."

> "CrisisLens doesn't just show the problem. It shows what to do about it."

**End card (5 sec):** "CrisisLens" + team names + GitHub URL.

---

## Timing Summary

| Scene | Duration | Who | Key Audience Hit |
|-------|----------|-----|-----------------|
| 1. Hook skit | 20 sec | Person 1 + 2 | Hackathon (creativity), UN (recognition) |
| 2. Demo | 55 sec | Person 2 voiceover | All three judge groups |
| 3. Methodology | 20 sec | Person 3 | Databricks + UN (rigor) |
| 4. Close + end card | 25 sec | Person 4 | Hackathon (engagement), UN (impact) |
| **Total** | **~2:00** | | |

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

1. **Overview Map** — animated timeline already playing (pre-check the box)
2. **Pause on 2026** — hover South Sudan
3. **Crisis Drilldown** — South Sudan, 2026 — show brief + cluster chart
4. **Reallocation Simulator** — drag slider 0% to 10-15%
5. **Funding Forecast** — South Sudan trend line
6. **Quick flash:** Outlier scatter + Recommender table (just show, minimal narration)

Total: 6 navigations in 55 seconds. Pre-load every page before recording.

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
