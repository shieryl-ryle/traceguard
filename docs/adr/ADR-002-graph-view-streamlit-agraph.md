# ADR-002 — Graph view uses streamlit-agraph 0.0.45

- **Date:** 2026-10-17
- **Status:** Proposed
- **Owners:** Shieryl
- **Related:** F-003, F-007, TASK-004, `traceguard/ui/graph_view.py`, System Design §6

### Context
The bootstrap input left the graph view open between pyvis and streamlit-agraph ("pick after checking
current docs"). F-003 needs a node click to show that node's IDs and evidence in Python, and F-007
needs evidence IDs to highlight graph elements. Repeated transfers between the same pair must
stay visible as separate edges (MultiDiGraph rule, PRD F-003).

### Why now
TASK-004 cannot build the graph panel until the component is chosen, and the feature freeze is
2026-10-18 2 PM Manila.

### Options considered
1. **pyvis 0.3.2** — Pros: popular, simple `from_nx`. Cons: renders static HTML via
   `components.html`; clicks never reach Python, so F-003 selection would need a separate widget;
   last release 2023-02-24.
2. **streamlit-agraph 0.0.45** — Pros: returns the clicked node ID to Python; passes edge options
   straight to vis-network (unique `id`, per-edge curvature). Cons: last PyPI release 2023-01-28;
   edge clicks return nothing in the released build; double-click calls `window.open(<node title>)`.
3. **Custom Streamlit component around vis-network** — Pros: full control. Cons: a frontend build
   we do not have time for.

### Decision
1. The graph view uses `streamlit-agraph==0.0.45`.
2. Every transfer is its own edge with `id = transaction_id`; parallel transfers between the same
   pair get increasing `smooth.roundness` so each stays visible.
3. Node selection comes from the `agraph()` return value. Transaction and device-link
   highlighting (F-007) is done by restyling edges from Python, not by edge clicks.
4. Node `title` is set to `None` so the double-click `window.open` handler stays inert.
5. Fallback if the component breaks on Cloud Run: a selectbox of node IDs driving the same
   highlight logic (`build_elements` is component-independent).

### Why this option
It is the only option that returns the analyst's selection to Python without a custom frontend
build. A spike on 2026-10-17 in headless Edge confirmed: a node click returned `A-07`;
TX-0002/TX-0003 (same pair) rendered as two edges; highlighting TX-0003 coloured only that edge.

### Overrides
- **Prior ADRs:** none
- **Docs to reconcile:** System Design §6 already names streamlit-agraph. Mark the spike as
  passed there. 3.12 is still unverified: the spike ran on Python 3.14.0, and the package is pure Python.
- **Out of scope:** graph layout algorithm and styling beyond what F-003/F-007 need.

### Consequences
- **Easier:** node-driven evidence panel; citation highlight from the brief.
- **Harder / owed:** no edge-click selection. Transactions are selected from the timeline or a citation instead.
  This depends on an unmaintained package, which is pinned exactly.
- **Follow-up:** verify on Cloud Run (Python 3.12 image) during TASK-004 integration.
