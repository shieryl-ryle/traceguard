# ADR-003 — Rule windows, thresholds, and trace semantics

- **Date:** 2026-10-17
- **Status:** Accepted
- **Owners:** Dzelle
- **Related:** PRD Q7, F-004, BR-003, BR-004, BR-010, TC-004, TASK-002, TASK-003,
  `tests/fixtures/rule_config.json`, `traceguard/graph/config.py`

### Context
PRD Q7 left the rule parameters open: the rapid-forwarding window, the fan-in window, and the
minimum sender count. TASK-002 cannot write expected outcomes, and TASK-003 cannot write the
tools, until the numbers and the exact window semantics are fixed. The UI sample (TASK-004/006)
already uses fan-in ≥ 3 senders in 30 min and forwarding within 60 min.

### Why now
The expected fixture outcomes (TC-004) are the proof that the numbers the analyst sees are
correct (PRD M1). They must be written against one agreed definition before the feature freeze
on 2026-10-18 2 PM Manila.

### Options considered
1. **Time-only forwarding** (outbound within 60 min of an inbound) — Pros: simplest; matches the
   UI sample. Cons: any account that pays a small bill within an hour of being paid matches,
   so C-2 would only avoid a match by timing.
2. **Time + amount forwarding** (outbound within 60 min of inbound transfers and ≥ 0.50 of their
   total) — Pros: closer to the public pass-through account typology; gives C-2 a second,
   explainable reason for no match. Cons: slightly more logic and output fields in TASK-003.

### Decision
1. **Fan-in (`RULE-FANIN-01`):** matches when ≥ 3 distinct senders transfer to the account
   within a 30-minute window (`window_seconds: 1800`). Candidate windows start at each inbound
   transfer and include transfers with `0 ≤ t − start ≤ 1800 s`. The reported window is the one
   with the most distinct senders; ties go to the earliest start. `window_end` is the last
   included transfer's timestamp. The tool reports this best window even when it does not match.
2. **Rapid forwarding (`RULE-FWD-01`):** each outbound transfer is evaluated against the inbound
   transfers with `0 ≤ t_out − t_in ≤ 3600 s`. It matches when at least one such inbound exists
   and `outbound_amount ≥ 0.50 × inbound_total`, compared exactly in `Decimal`. The account
   matches when any outbound matches. Every outbound transfer is reported in `evaluated`.
3. **Displayed figures:** `forwarded_ratio` is shown as a 2-decimal string **rounded down**, so
   the display never overstates the ratio relative to the threshold (4999.99 / 10000.00 → `"0.49"`,
   no match). Minutes are whole numbers (`window_span_minutes`, `minutes_after_last_inbound`).
   Amounts are decimal strings. Brief wording uses "ratio" or "share", never "%" (BR-004).
4. **`trace_funds`:** default `max_depth` is 3. Outbound traces follow only transfers with
   timestamp ≥ the previous hop (equal timestamps are followed). Inbound traces mirror this
   (≤). `start_time` bounds the first hop the same way. Each path ends with `stop_reason`
   `data_boundary` (no eligible next transfer in the dataset) or `max_depth` (more transfers
   exist past the limit). `truncated` is true whenever the trace returns at least one path: every path ends either at the data boundary or at the depth limit, so where the funds went next is never shown as known (BR-005). The UI and brief use the per-path `stop_reason`; `truncated` is only the summary flag for the "truncation notice" (PRD F-004). Outbound paths are listed in
   depth-first order of hop timestamp, then transaction ID; inbound paths by first transaction ID.
5. **Boundaries are inclusive to the second:** exactly 30:00 / 60:00 / ratio 0.50 match; 30:01,
   60:01 and ratio below 0.50 do not. `tests/fixtures/boundary_cases.json` pins each one.
6. The values above live in `traceguard/graph/config.py` for the app and in
   `tests/fixtures/rule_config.json` for tests; the two must agree (TASK-003 test).

### Why this option
The extra amount check costs one comparison and makes the forwarding flag defensible: C-2's
payday spending stays unflagged because it is small (`TX-0014`, ratio 0.12) or more than an hour
later (`TX-0015`, 60 min + 1 s), not because of a lucky timestamp. The 30/60-minute windows
and 3 senders keep the existing UI sample valid.

### Overrides
- **Prior ADRs:** none
- **Docs to reconcile:** PRD §13 Q7 → resolved by this ADR. System Design §2 tool contracts:
  `detect_rapid_forwarding` output becomes per-outbound `evaluated` entries with
  `inbound_total` and `forwarded_ratio`; `trace_funds` returns `paths[]` with `stop_reason`.
  The UI sample `sample_evidence.json` (TASK-006) uses `minutes_after_last_inbound` but no ratio.
- **Out of scope:** tool output field names beyond those pinned in `tests/fixtures/`; UI wording.

### Consequences
- **Easier:** TASK-003 has exact, hand-checked expected outputs for every tool and boundary.
- **Harder / owed:** the AI prompt and brief should explain the ratio condition, not just timing.
- **Follow-up:** TASK-003 implements `config.py` and the tools against these fixtures.
