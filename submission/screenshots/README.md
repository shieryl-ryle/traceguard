# Deck screenshots: provenance

| File | Slide | Shows |
|---|---|---|
| `slide2-c1-graph.png` | 2 | C-1 graph with A-07 selected and its evidence IDs in the selection panel |
| `slide3-brief.png` | 3 | Live AI output label, model and run time, rule flags with thresholds, first observation with citation chips |
| `slide3-citation-records.png` | 3 | Counterevidence, unknowns (data boundary), suggested checks, and the records cited by `RULE-FWD-01` |
| `slide3-graph-highlight.png` | 3 | TX-0004 and TX-0005 highlighted on the graph and starred in the timeline after clicking `RULE-FWD-01` |

**How they were captured:** on 2026-10-17, from the public Cloud Run URL
(`https://traceguard-343683630064.asia-southeast1.run.app`, revision 4). Capture used a fresh headless
Edge profile with no sign-in, at 1440×960 and 2× scale. Each brief is a **real** `gemini-3.5-flash` run
in `asia-southeast1` that passed validation on the first attempt.

**Rule (BR-006):** never replace these with screenshots from local fake-model test runs. Those runs
display "Live AI output" for scripted text.

**Interim:** these show C-1 on the **hand-derived sample evidence**. That is labelled on screen as
"sample evidence … not yet computed by graph tools". Retake all four after the TASK-003 graph tools
are wired in, so the deck shows computed evidence.
