# Setup — TraceGuard

Two parts: **A. Google Cloud project** (TASK-000, owner Dzelle, done once) and **B. Local machine**
(everyone). Exact IAM roles and deploy commands are owned by
[System Design §5 and §7](system-design.md). This page is the step-by-step walkthrough.

> **Use a personal Google account only.** Never use a work or employer account, project, or
> billing (PRD BR-001, BR-008). Use a separate browser profile so accounts don't mix.
> Never paste keys, passwords, or service-account JSON into the repo or any chat tool.

---

## A. Google Cloud project (TASK-000 — Dzelle, timebox 60–90 min)

Shieryl's own account has already used its free trial. Its billing account is closed, so the
project lives on Dzelle's side.

### A1. Billing
1. Open `console.cloud.google.com/freetrial` with your **personal** Gmail.
   - **Have you never used a Google Cloud free trial?** Sign up: country Philippines, add a
     card for identity verification. Check the credit amount and terms on the signup page.
   - **Already used one, but you have a personal billing-enabled account?** Use that billing
     account and skip the trial.
   - **Neither works?** Tell Shieryl immediately. The fallback is upgrading Shieryl's account.
2. Confirm that **Billing → Account management** shows the account as open, with no red banner.

### A2. Project
1. Click the project picker → **New project** → name it `traceguard-2026` → link it to the billing account from A1.
2. Copy the **Project ID** (it may differ from the name) and send it to Shieryl privately.
3. Go to **Billing → Budgets & caps** → create a budget of about $10 scoped to `traceguard-2026`, with alerts at 50/90/100%.
   The budget only sends alerts. Spend is actually capped by `--max-instances 2` and the AI call limits (BR-007).

### A3. Check the Gemini model (PRD Q5)
1. In the console, go to **Vertex AI → Model Garden** and search for `gemini-3.5-flash`.
2. Confirm it is available in **asia-southeast1 (Singapore)**. Accept any terms it shows.
3. Not available there? Check `gemini-3.8-flash` on **global** and tell Shieryl. Changing the model needs an ADR.
4. Do **not** use `gemini-2.5-*`. Those models retire on 2026-10-20.

### A4. Enable APIs and create the runtime service account
Install the gcloud CLI first (see B1), then run:
```bash
PROJECT_ID=<project-id-from-A2>
gcloud auth login                      # personal account
gcloud config set project $PROJECT_ID

gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com aiplatform.googleapis.com

gcloud iam service-accounts create traceguard-run --display-name="TraceGuard runtime"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:traceguard-run@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### A5. Give Shieryl access (least privilege — never Owner or Editor)
```bash
SHIERYL=<shieryl-personal-gmail>
for ROLE in roles/run.sourceDeveloper roles/serviceusage.serviceUsageConsumer \
            roles/aiplatform.user roles/logging.viewer; do
  gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$SHIERYL" --role="$ROLE"
done
gcloud iam service-accounts add-iam-policy-binding \
  traceguard-run@$PROJECT_ID.iam.gserviceaccount.com \
  --member="user:$SHIERYL" --role="roles/iam.serviceAccountUser"
```

### A5b. Let source deploys build (needed before the first `gcloud run deploy --source`)
A source deploy builds in Cloud Build, which runs as the project's **default compute service
account** (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`). Without these two grants, the
build fails with `caller does not have permission to act as service account` (seen on 2026-10-17).
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
BUILD_SA=$PROJECT_NUMBER-compute@developer.gserviceaccount.com

# The deployer may start builds that run as the build SA (that one SA only)
gcloud iam service-accounts add-iam-policy-binding $BUILD_SA --project $PROJECT_ID \
  --member="user:$SHIERYL" --role="roles/iam.serviceAccountUser"

# The build SA may build and deploy to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$BUILD_SA" --role="roles/run.builder"
```
On PowerShell, run the commands one at a time with the values filled in.

### A5c. Make the service public (owner, once, after the first deploy)
The teammate deployer's roles can't change a service's access policy. So the first deploy finishes
with `Setting IAM policy failed`, and the URL returns HTTP 403 (seen 2026-10-17). The project owner
runs this once, and later deploys keep the setting:
```bash
gcloud run services add-iam-policy-binding traceguard --region asia-southeast1 --project $PROJECT_ID \
  --member="allUsers" --role="roles/run.invoker"
```
This only lets people call the app, which the hackathon requires for a public URL. It grants no management access.

### A6. Done when
- [ ] The billing account is open, and `traceguard-2026` is linked to it
- [ ] The budget alert is set
- [ ] The model ID and location are confirmed and sent to Shieryl
- [ ] The APIs are enabled and the `traceguard-run` service account exists with `roles/aiplatform.user`
- [ ] Shieryl can see the project in the console with her personal account
- [ ] The two A5b build grants are in place
- [ ] After the first deploy, A5c is done and the URL loads in an incognito window
- [ ] The Evidence column for TASK-000 in [implementation-plan.md](implementation-plan.md) is updated (no IDs or secrets)

The first deploy is TASK-001 ([System Design §7](system-design.md)). If it still fails with a
permission error, fix only the role named in that error. Never grant Owner or Editor.

---

## B. Local machine (everyone)

### B1. Install once
| Tool | Where | Check |
|---|---|---|
| Git | `git-scm.com` | `git --version` |
| Python 3.12 (tick "Add to PATH" on Windows) | `python.org/downloads` | `python --version` → 3.12.x |
| Google Cloud CLI | `cloud.google.com/sdk/docs/install` | `gcloud --version` |

### B2. Get the code and authenticate
```bash
git clone <repo-url>
cd <repo-folder>
gcloud auth login
gcloud auth application-default login   # lets local code call Gemini as you (no keys)
gcloud config set project <PROJECT_ID>
```

### B3. Python environment (once TASK-001 has added `requirements*.txt`)
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1      macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

### B4. Local environment variables (non-secret)
Set these in your shell. If you use a `.env` file, it is gitignored; never commit it.
```bash
GOOGLE_CLOUD_PROJECT=<PROJECT_ID>
VERTEX_LOCATION=asia-southeast1
GEMINI_MODEL=gemini-3.5-flash
```

### B5. Run and test
Commands live in [AGENTS.md](../AGENTS.md) (Build & run, Test) and [QA Test Plan §1](qa-test-plan.md).
