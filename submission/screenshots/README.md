# Deck screenshots: provenance

| File | Slide | Shows |
|---|---|---|
| `slide2-c1-graph.png` | 2 | C-1 graph, with A-07 selected and its evidence IDs in the selection panel |
| `slide3-brief.png` | 3 | The "Live AI output" label, model and run time, deterministic rule flags with thresholds, and the deterministic contrast with its citation chips |
| `slide3-citation-records.png` | 3 | Counterevidence quoting the tool contrasts; unknowns (data boundary and depth limit); suggested checks; the records cited by `RULE-FWD-01` |
| `slide3-graph-highlight.png` | 3 | The records matched by `RULE-FWD-01`, highlighted on the graph and starred in the timeline |

**Captured:** 2026-10-18, from the public Cloud Run URL
(`https://traceguard-343683630064.asia-southeast1.run.app`, revision `traceguard-00009-52w`).

**Setup:**
- a fresh headless Edge profile with no sign-in, at 1440×960 and 2× scale;
- real dataset C-1 (TASK-002), with evidence from the graph tools (TASK-003, including the contrasts);
- a real `gemini-3.5-flash` brief at LOW thinking, from `asia-southeast1`, that passed validation on the first attempt.

**Rule (BR-006):** never replace these with screenshots from local fake-model test runs. Those runs label scripted text as "Live AI output".

**Retake** if the UI, the dataset, or the prompt changes before submission. Rerun the same capture script against the live URL.
