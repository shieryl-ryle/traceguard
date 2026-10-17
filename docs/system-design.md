# System Design — {{PROJECT_NAME}}

**Status:** Draft v0.1

## 1. Architecture
{{Diagram or short description: clients, services, data stores, external APIs.}}

## 2. Components
| Component | Responsibility | Location in repo |
|---|---|---|
| {{component}} | {{responsibility}} | `{{path}}` |

## 3. Data
{{Main entities and where they live. Split into data-model.md when this grows.}}

## 4. Integrations
| Service | Purpose | Auth method | Secret name (env var) |
|---|---|---|---|
| {{service}} | {{purpose}} | {{method}} | `{{ENV_VAR}}` |

## 5. Security & privacy
- Secrets only via environment variables; never committed.
- Least-privilege service accounts — list exact roles, never owner/editor/admin.
- {{PII handling, consent, retention}}

## 6. Stack currency
Pinned versions agents must verify against official docs before emitting APIs.

| Library / service | Pinned version | Docs URL | Verified on |
|---|---|---|---|
| {{library}} | {{version}} | {{url}} | {{YYYY-MM-DD}} |
