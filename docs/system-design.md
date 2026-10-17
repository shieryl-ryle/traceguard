# System Design — TraceGuard

**Status:** Draft v0.1 · **Last updated:** 2026-10-17

## 1. Architecture
```
Browser (analyst / judge, no login)
   │ HTTPS
   ▼
Cloud Run service "traceguard"  (asia-southeast1, max-instances 2, SA traceguard-run)
 └─ Streamlit app (app.py)  ── one process: UI + backend, no state
     ├─ traceguard/ui/        case queue · timeline · graph view · brief · export
     ├─ traceguard/graph/     loader → NetworkX MultiDiGraph (in memory) + 5 read-only tools
     ├─ traceguard/ai/        fixed retrieval workflow → Gemini call → citation + wording validation
     └─ data/                 seeded synthetic dataset, bundled in the image
                │ ADC (runtime service account), no API keys
                ▼
        Gemini on Vertex AI  (google-genai, VERTEX_LOCATION, GEMINI_MODEL)
```
**Responsibility split (BR-003):** the graph layer computes every path, window, count, sum, and
rule flag. The model only explains tool output in structured JSON. The validator decides whether
the brief can be shown.

**AI flow (locked, fixed workflow — BR-006):**
1. For the selected case, run every relevant tool on its `seed_ids` (≤ 4 tool rounds, BR-007).
2. Build an evidence bundle: tool outputs + the set of evidence IDs they returned. Cap at
   60,000 characters (provisional, PRD Q6); over the cap → readable error.
3. Call Gemini with `response_mime_type="application/json"` and a brief schema; timeout 30 s.
4. Validate: every cited ID ∈ evidence set (BR-002), no forbidden terms (BR-004), required
   sections present. Fail → regenerate once → fail again → error, no brief.
5. Render the brief and tool log, labelled with model ID and run time.

Gemini function calling is used only for F-011 (P1), if time allows.

## 2. Components
| Component | Responsibility | Location in repo |
|---|---|---|
| Entry point | Streamlit page wiring, session state for selection/highlight | `app.py` |
| Dataset | Seeded generator + generated JSON for C-1/C-2/C-3 | `data/` |
| Graph loader | Build `MultiDiGraph`: account + device nodes; one transfer edge per `transaction_id` (`kind="transfer"`); separate `kind="device_link"` edges | `traceguard/graph/loader.py` |
| Graph tools | `get_account_context`, `trace_funds`, `find_shared_devices`, `detect_rapid_forwarding`, `detect_fan_in`. Read-only and allowlisted, returning typed results with evidence IDs. No free-form queries | `traceguard/graph/tools.py` |
| Rule config | Window lengths, minimum sender counts, forwarding ratio, trace depth ([ADR-003](adr/ADR-003-rule-windows-and-thresholds.md)) | `traceguard/graph/config.py` |
| AI investigation | Retrieval workflow, prompt, Gemini client, schema parsing | `traceguard/ai/` |
| Validators | Citation check (BR-002), wording check (BR-004), payload cap (BR-007) | `traceguard/ai/validate.py` |
| UI | Queue, timeline, graph view, brief, citation highlight, export, error states | `traceguard/ui/` |
| Tests + expected outcomes | pytest; expected fixture outcomes **only here** (BR-010) | `tests/`, `tests/fixtures/` |
| Container | Streamlit on `$PORT`, `0.0.0.0`, headless | `Dockerfile`, `.dockerignore` |
| Submission assets | Proposal PDF, video script, architecture slide | `submission/` |

### Tool contracts
| Tool | Input | Output |
|---|---|---|
| `get_account_context` | `account_id` | account ID, label, inbound/outbound transfers, linked devices, evidence IDs |
| `trace_funds` | `account_id`, `direction`, `max_depth` (default 3), `start_time` | `paths[]` of time-ordered hops (equal timestamps followed), each with `stop_reason` `data_boundary` or `max_depth`; `truncated`, `truncation_reasons`, and a plain-language `notice` stating what is unknown |
| `find_shared_devices` | `account_ids` | device ID, account IDs, `relationship_id`s |
| `detect_rapid_forwarding` | `account_id`, config | `rule_id`, `matched`, `config`, `explanation`, and per-outbound `evaluated[]` entries with `inbound_transaction_ids`, `inbound_total`, `forwarded_ratio` (2-dp string, rounded down), `minutes_after_last_inbound`, `inbound_minus_outbound` (2-dp string when the inbound total exceeds the outbound amount, else null; a difference of amounts, not a claim about which money moved), `matched`; `contrasts[]` |
| `detect_fan_in` | `account_id`, config | `rule_id`, `matched`, `config`, `explanation`, `sender_count`, `sender_account_ids`, `transfer_count`, `transaction_ids`, `window_start`/`window_end`, `window_span_minutes`, `aggregate_amount`; `senders_on_shared_device` / `senders_not_on_shared_device` (senders linked to a device another sender in the window also uses), `shared_device_relationship_ids`; `contrasts[]` |

**Contrasts** (rule tools): `contrasts[]` holds deterministic counter-facts as `{text, evidence_ids}`,
quotable verbatim as counterevidence. Every figure and ID in `text` is a field value in the same
output; every `evidence_ids` entry is in the tool's evidence IDs. Fan-in adds one when the rule matched
and some window senders share a recorded device while others do not; rapid forwarding adds one per
matched outbound transfer with a positive `inbound_minus_outbound`. Contrast wording compares
amounts and describes recorded data only; it never says outgoing funds are the incoming funds (BR-005). Unmatched rules add none (their `explanation` already serves).

Window boundaries are inclusive at the configured length and exclusive beyond it (tested to the second, TC-004).

### AI module contract (`traceguard/ai/`, TASK-005)
- **Retriever** (provided by the graph layer): `(case_id, max_rounds) -> EvidenceBundle`. A bundle
  is a tuple of rounds; each round holds `ToolCall(tool, inputs, output, evidence_ids)`. `output`
  must be JSON-serialisable. A "tool round" is one batch of tool calls. The retriever stops at
  `max_rounds` (4), and `run_investigation` re-checks this as a backstop.
- **Figures must be ready to quote.** The validator rejects any number in brief text that does
  not appear in the tool output (BR-003). Tools should therefore emit display-ready values,
  e.g. `window_minutes: 30` next to `window_seconds: 1800`, and amounts as decimal strings.
- **IDs in free text are checked too.** Any account, device, transaction, relationship, or rule ID
  mentioned in brief text must appear in the tool output (BR-002, BR-005). IDs use an uppercase
  prefix plus a hyphen and contain a digit (e.g. `A-07`, `TX-0001`, `RULE-FANIN-01`).
- **Validation order:** structure → citations → figures → wording. On any problem, the workflow
  regenerates once, sending the problems back to the model; a second failure raises
  `InvestigationError("validation")` and shows no brief.
- **Evidence source:** the UI's `RETRIEVER` in `traceguard/ui/investigation.py` is
  `traceguard.graph.retriever.graph_retriever`. It runs a fixed two-round workflow over the bundled
  dataset: account context for each seed, then fan-in, rapid forwarding, outbound trace and shared
  devices. Case title, description and scenario label never reach model input. The case queue reads
  the same dataset through `traceguard.graph.loader.case_dicts()`. The hand-made S-1 sample is
  test-only, in `tests/ui_sample/`.
- **Citation navigation (F-007):** clicking an evidence ID in a validated brief highlights it in the
  graph and marks it ★ in the timeline's "Cited" column; a rule ID highlights the records it
  matched. The timeline's "Selected" column is the analyst's own row selection, never a citation.
- **Errors:** every failure is an `InvestigationError(kind, user_message)`. The UI shows
  `user_message`; logs record `kind` and the error code only, never prompts or evidence.

## 3. Data
All synthetic (BR-001), one currency (PHP), deterministic seed, about 20–40 accounts and 80–150
transactions. Bundled in the image as JSON under `data/`. No database, and no persistence across requests.

| Entity | Fields |
|---|---|
| Account | `account_id`, `label` |
| Device link | `relationship_id`, `account_id`, `device_id`, `observed_at` |
| Transaction | `transaction_id`, `sender_account_id`, `receiver_account_id`, `amount` (Decimal as string), `currency`, `timestamp` (ISO 8601, timezone-aware) |
| Case | `case_id`, `title`, `description`, `seed_ids`, `scenario_label` |
| Rule result | `rule_id`, `config`, `matched_evidence_ids`, `explanation` |
| AI brief | `case_id`, `observations[{text, evidence_ids}]`, `counterevidence[{text, evidence_ids}]`, `unknowns[]`, `suggested_checks[]`, `model`, `run_at`, `cached: bool` |

**Evidence ID namespace:** `transaction_id`, `relationship_id`, and `rule_id` values are the
only citable IDs. The model's schema has **no** numeric or flag fields (BR-003). `model`,
`run_at`, and `cached` are set by the server, not the model.

## 4. Integrations
| Service | Purpose | Auth method | Config (env var) |
|---|---|---|---|
| Gemini on Vertex AI | Brief synthesis (F-005, F-006, F-011) | ADC via the Cloud Run runtime SA `traceguard-run` (local: `gcloud auth application-default login`) | `GOOGLE_CLOUD_PROJECT`, `VERTEX_LOCATION`, `GEMINI_MODEL` |
| Cloud Run | Hosting (F-010) | Deployer's gcloud identity | — |
| Cloud Build / Artifact Registry | Source deploy build | Build SA (Compute Engine default SA unless overridden) with `roles/run.builder` | — |

**Model choice (PRD Q5, verify in Model Garden console before TASK-001):**
- **Default:** `GEMINI_MODEL=gemini-3.5-flash`, `VERTEX_LOCATION=asia-southeast1`. Stable and
  listed for Singapore. Keeps processing in-region alongside the Cloud Run region.
- **Alternative:** `gemini-3.8-flash` on `VERTEX_LOCATION=global` (newer, global-only; the
  global endpoint gives no in-region processing guarantee).
- **Do not use `gemini-2.5-*`.** These models retire on 2026-10-20, two days after submission
  and while judging is likely still running.
- Changing the model ID after TASK-001 needs an ADR (AGENTS.md "Ask before changing").

## 5. Security & privacy
- Secrets only via environment variables; never committed. **No secrets exist in this design.**
  Vertex AI is reached only through ADC on the runtime service account (BR-008).
- **Use a personal or hackathon-provided GCP project only.** Never use an employer's project or billing.
- Least-privilege service accounts. These are the exact roles; never grant Owner, Editor, or Admin:

| Principal | Role | Scope |
|---|---|---|
| `traceguard-run` (runtime SA) | `roles/aiplatform.user` | project |
| Build SA (`PROJECT_NUMBER-compute@developer.gserviceaccount.com` by default) | `roles/run.builder` | project. Required for source deploys (setup.md §A5b) |
| Dzelle (personal account) | project creator (owner by creation; not granted to anyone else) | owns billing and grants the roles below |
| Teammate deployer (Shieryl) | `roles/run.sourceDeveloper` | project |
| Teammate deployer | `roles/serviceusage.serviceUsageConsumer` | project |
| Teammate deployer | `roles/iam.serviceAccountUser` | the `traceguard-run` SA only |
| Teammate deployer | `roles/iam.serviceAccountUser` | the build SA only, so source deploys can run as it (setup.md §A5b) |
| Teammate deployer | `roles/aiplatform.user` | project (local live tests) |
| Teammate deployer | `roles/logging.viewer` | project |
| `allUsers` | `roles/run.invoker` | the `traceguard` service only. The owner grants it once (setup.md §A5c); the hackathon requires a public URL |

- No narrower GA role than `roles/aiplatform.user` covering only Gemini inference could be
  verified (`roles/aiplatform.expressUser` is Beta, scope unverified).
- **Cost controls:** `--max-instances 2` plus the BR-007 caps limit spend. Budget alerts only notify.
- **PII:** none. The data is synthetic only. Logs never include full evidence bundles or prompts beyond IDs and timings.
- Service is public (`--allow-unauthenticated`) by hackathon requirement. There is no authentication (PRD §11).

## 6. Stack currency
Agents must verify these versions against the official docs before emitting APIs.

| Library / service | Pinned version | Docs URL | Verified on |
|---|---|---|---|
| Python | 3.12 (`python:3.12-slim` image) | https://docs.python.org/3.12/ | 2026-10-17 |
| streamlit | 1.66.0 | https://docs.streamlit.io | 2026-10-17 (PyPI) |
| networkx | 3.7 (requires ≥ 3.12) | https://networkx.org/documentation/stable/ | 2026-10-17 (PyPI) |
| google-genai | 2.31.0 | https://googleapis.github.io/python-genai/ | 2026-10-17 (PyPI + source on `main`) |
| streamlit-agraph | 0.0.45 (last release 2023-01-28; browser spike passed 2026-10-17 on Python 3.14 — **3.12 unverified**; see ADR-002) | https://github.com/ChrisDelClea/streamlit-agraph | 2026-10-17 |
| pandas | 3.0.6 | https://pandas.pydata.org/docs/ | 2026-10-17 (PyPI) |
| pytest | 9.1.1 | https://docs.pytest.org | 2026-10-17 (PyPI) |
| mypy | 2.4.0 | https://mypy.readthedocs.io | 2026-10-17 (PyPI) |
| Gemini model | `gemini-3.5-flash` @ `asia-southeast1` (**console check pending, Q5**) | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions | 2026-10-17 (docs) |
| Cloud Run | source deploy + Dockerfile; `$PORT` (default 8080), listen on `0.0.0.0` | https://docs.cloud.google.com/run/docs/container-contract | 2026-10-17 |

**google-genai API notes (verified 2026-10-17):**
- Client: `genai.Client(vertexai=True, project=..., location=...)`. Current docs show the renamed
  flag `enterprise=True` (Vertex AI is now branded "Gemini Enterprise Agent Platform"). The
  `vertexai=True` flag is a supported legacy alias, and we keep it because it matches the locked decision.
  Never set both flags to conflicting values; that raises `ValueError`.
- JSON output: `types.GenerateContentConfig(response_mime_type="application/json",
  response_schema=<Pydantic model>)`, then read `response.parsed`. Do not set `response_json_schema`
  as well, because the two are mutually exclusive. Do not repeat the schema in the prompt.
- Timeout: `http_options=types.HttpOptions(timeout=30_000)`. **The value is in milliseconds.**
- Thinking: `thinking_config=types.ThinkingConfig(thinking_level=LOW)` on every call. Measured
  2026-10-17 on `gemini-3.5-flash` in `asia-southeast1`: 3–9 s per brief at LOW vs 20–28 s at the
  default level, and all LOW briefs passed validation. At the default level, one C-1 regeneration hit
  the 30 s deadline (Vertex 504). Changing the level needs a re-measure against the timeout.
- Health check: `GET /_stcore/health` returns 200 when ready.

**Graph view decision:** use streamlit-agraph. It returns the selected node ID to Python
(`agraph()` return value), which F-003/F-007 need. pyvis renders static HTML and returns nothing.
**Risks:** the package has had no release since 2023, and parallel edges are unverified. Give every
edge a unique `id` (= `transaction_id`). Spike this at the start of TASK-004; if it fails, fall back to
a selectbox-driven highlight. Record the outcome as an ADR.

## 7. Deployment (TASK-001)
```bash
PROJECT_ID=<your-project-id>
REGION=asia-southeast1
SA=traceguard-run@$PROJECT_ID.iam.gserviceaccount.com

gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com aiplatform.googleapis.com

gcloud iam service-accounts create traceguard-run --display-name="TraceGuard runtime"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" --role="roles/aiplatform.user"

gcloud run deploy traceguard --source . --region $REGION \
  --service-account $SA --allow-unauthenticated --max-instances 2 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_LOCATION=asia-southeast1,GEMINI_MODEL=gemini-3.5-flash
```
Dockerfile start command (shell form so `$PORT` expands):
`CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`

Before the first source deploy, apply the two build grants in [setup.md §A5b](setup.md): the
deployer gets `roles/iam.serviceAccountUser` on the build SA, and the build SA gets
`roles/run.builder`. Without them the build fails with `caller does not have permission to act
as service account` (seen 2026-10-17). For any other permission error, fix only the role it names.
