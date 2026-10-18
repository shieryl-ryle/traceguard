# Setup — deploy your own TraceGuard

Two parts: **A. a Google Cloud project** (done once) and **B. a local machine**. The exact IAM roles
and the deploy command are owned by [System Design §5 and §7](system-design.md). This page is the
step-by-step walkthrough, including the permission errors we hit and how to fix them.

> **Use a project and billing account you own.** Never use a work or employer account, project or
> billing (PRD BR-001, BR-008). Never paste keys, passwords or service-account JSON into the repo or
> any chat tool. TraceGuard needs none: it uses Application Default Credentials.

---

## A. Google Cloud project

### A1. Billing
1. Open the Google Cloud console with a personal Google account. Start the free trial, or use an
   existing billing account you own.
2. Confirm that **Billing → Account management** shows the account as open.

### A2. Project and budget
1. Click the project picker → **New project** → for example `traceguard-2026` → link it to your billing account.
2. Note the **Project ID**; it may differ from the name.
3. Go to **Billing → Budgets & alerts** and create a small budget (we used about $10) for the
   project, with alerts at 50/90/100%. A budget only sends alerts. Spend is actually capped by
   `--max-instances 2` and the AI call limits (BR-007).

### A3. Check the Gemini model
1. In **Vertex AI → Model Garden**, search for `gemini-3.5-flash` and confirm it is available in
   **asia-southeast1 (Singapore)**. Accept any terms it shows.
2. If it isn't available, `gemini-3.8-flash` on **global** is the alternative. Changing the model
   needs an ADR.
3. Do **not** use `gemini-2.5-*`. Those models retire on 2026-10-20.

### A4. Enable APIs and create the runtime service account
Install the gcloud CLI first (see B1), then run:
```bash
PROJECT_ID=<your-project-id>
gcloud auth login
gcloud config set project $PROJECT_ID

gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com aiplatform.googleapis.com

gcloud iam service-accounts create traceguard-run --display-name="TraceGuard runtime"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:traceguard-run@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### A5. Optional: let a teammate deploy (least privilege, never Owner or Editor)
If someone other than the project owner deploys, grant them exactly these roles:
```bash
DEPLOYER=<teammate-google-account>
for ROLE in roles/run.sourceDeveloper roles/serviceusage.serviceUsageConsumer \
            roles/aiplatform.user roles/logging.viewer; do
  gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$DEPLOYER" --role="$ROLE"
done
gcloud iam service-accounts add-iam-policy-binding \
  traceguard-run@$PROJECT_ID.iam.gserviceaccount.com \
  --member="user:$DEPLOYER" --role="roles/iam.serviceAccountUser"
```

### A6. Let source deploys build (needed before the first `gcloud run deploy --source`)
A source deploy builds in Cloud Build, which runs as the project's **default compute service
account** (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`). Without these two grants the
build fails with `caller does not have permission to act as service account`.
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
BUILD_SA=$PROJECT_NUMBER-compute@developer.gserviceaccount.com

# The deployer may start builds that run as the build SA (that one SA only)
gcloud iam service-accounts add-iam-policy-binding $BUILD_SA --project $PROJECT_ID \
  --member="user:$DEPLOYER" --role="roles/iam.serviceAccountUser"

# The build SA may build and deploy to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$BUILD_SA" --role="roles/run.builder"
```
If the project owner deploys, use the owner's account as `DEPLOYER`. On PowerShell, run the
commands one at a time with the values filled in.

### A7. Make the service public (owner, once, after the first deploy)
A deployer with the roles above can't change a service's access policy, so the first deploy ends
with `Setting IAM policy failed` and the URL returns HTTP 403. The project owner runs this once;
later deploys keep the setting:
```bash
gcloud run services add-iam-policy-binding traceguard --region asia-southeast1 --project $PROJECT_ID \
  --member="allUsers" --role="roles/run.invoker"
```
This only lets people use the app. It grants no management access.

### A8. Done when
- [ ] Billing is open and linked to the project, with a budget alert set
- [ ] The model ID and location are confirmed
- [ ] The APIs are enabled and `traceguard-run` exists with `roles/aiplatform.user`
- [ ] The A6 build grants are in place
- [ ] After the first deploy ([System Design §7](system-design.md)), A7 is done and the URL loads in a private window

If a deploy still fails with a permission error, grant only the role named in that error. Never
grant Owner or Editor.

---

## B. Local machine

### B1. Install once
| Tool | Where | Check |
|---|---|---|
| Git | `git-scm.com` | `git --version` |
| Python 3.12 (tick "Add to PATH" on Windows) | `python.org/downloads` | `python --version` → 3.12.x |
| Google Cloud CLI | `cloud.google.com/sdk/docs/install` | `gcloud --version` |

### B2. Get the code and authenticate
```bash
git clone https://github.com/shieryl-ryle/traceguard.git
cd traceguard
gcloud auth login
gcloud auth application-default login   # lets local code call Gemini as you (no keys)
gcloud config set project <PROJECT_ID>
```

### B3. Python environment
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1      macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

### B4. Environment variables (not secret)
Set these in your shell. If you use a `.env` file, it is gitignored; never commit it.
```bash
GOOGLE_CLOUD_PROJECT=<PROJECT_ID>
VERTEX_LOCATION=asia-southeast1
GEMINI_MODEL=gemini-3.5-flash
```

### B5. Run and test
`streamlit run app.py`, then see the test gates in [QA Test Plan §1](qa-test-plan.md).
