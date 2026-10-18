# Deck screenshots: provenance

| File | Slide | Shows |
|---|---|---|
| `slide2-c1-graph.png` | 2 | C-1 graph, with A-07 selected and its evidence IDs in the selection panel |
| `slide3-brief.png` | 3 | The "Live AI output" label, model and run time, deterministic rule flags with thresholds, and the deterministic contrast with its citation chips |
| `slide3-citation-records.png` | 3 | Counterevidence quoting the tool contrasts; unknowns (data boundary and depth limit); suggested checks; the records cited by `RULE-FWD-01` |
| `slide10-verified-panel.png` | 10 | The full "Verified before display" panel of a live C-1 brief |
| `slide10-follow-up-refusal.png` | 10 | Case C-3: follow-up "Who owns A-22?" refused as not answerable from the case data (retaken 2026-10-18 on revision `traceguard-00013-qrg`, 2× scale, cropped to the follow-up block) |
| `logo-google-cloud.png`, `logo-gemini.png`, `logo-vertex-ai.png` | 7 | Service marks rendered from the video's `story.html` (Gemini and Vertex AI: LobeHub Icons, MIT; Google Cloud: Simple Icons, CC0, recoloured). Trademarks belong to Google |
| `slide3-graph-highlight.png` | 3 | The records matched by `RULE-FWD-01`, highlighted on the graph and starred in the timeline |

**Layout:** graph and AI brief side by side, with the Verified panel and follow-up question (PRs #20 to #22).

**Captured:** 2026-10-18, from the public Cloud Run URL
(`https://traceguard-343683630064.asia-southeast1.run.app`, revision `traceguard-00009-52w`).

**Setup:**
- a fresh headless Edge profile with no sign-in, at 1440×960 and 2× scale;
- real dataset C-1 (TASK-002), with evidence from the graph tools (TASK-003, including the contrasts);
- a real `gemini-3.5-flash` brief at LOW thinking, from `asia-southeast1`, that passed validation on the first attempt.

**Rule (BR-006):** never replace these with screenshots from local fake-model test runs. Those runs label scripted text as "Live AI output".

**Retake** if the UI, the dataset, or the prompt changes before submission. Rerun the same capture script against the live URL.
