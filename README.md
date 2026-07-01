# cloudops-rag-eval

FastAPI service for document QA over a small synthetic Acme CloudOps Platform corpus. The
service demonstrates local retrieval with Chroma, grounded answers with citations, request
IDs, structured JSON logs, a lightweight evaluation harness, Docker, Terraform for Cloud Run,
and GitHub Actions checks.

The corpus is fictional and intentionally small enough to review during an interview. It does
not contain private company, client, or challenge documents.

## Architecture

```text
Client
  |
  v
FastAPI /v1/ask
  |
  +--> request/correlation ID middleware
  +--> structured JSON logging with masking
  |
  v
RAG service
  |
  +--> Chroma local index
  |      |
  |      v
  |    synthetic markdown docs
  |
  +--> answer provider
         |
         +--> mock provider by default
         +--> optional Gemini or OpenAI-compatible provider
```

For the demo, source docs live in the repo and are copied into the image. Retrieval uses a
local Chroma index with deterministic local embeddings. In a GCP production version, document
storage could move to Cloud Storage and retrieval could use Vertex AI embeddings with
AlloyDB/pgvector, Vertex AI Vector Search, or another managed backend based on latency and
scale needs.

## Stack

- Python 3.12
- FastAPI lifespan startup
- Pydantic v2 and `pydantic-settings`
- Chroma local retrieval
- `uv` dependency management
- Ruff, mypy, pytest, pre-commit
- Docker
- Terraform for Cloud Run and Artifact Registry
- GitHub Actions CI without deployment

## Local setup

```bash
uv sync
cp .env.example .env
uv run uvicorn cloudops_rag_eval.main:app --reload
```

Open:

- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/readyz`
- `http://127.0.0.1:8000/docs`

For a reproducible local run without Docker, use the lockfile:

```bash
uv sync --locked
uv run --frozen uvicorn cloudops_rag_eval.main:app --host 127.0.0.1 --port 8000
```

Ask a question:

```bash
curl -s http://127.0.0.1:8000/v1/ask \
  -H 'content-type: application/json' \
  -H 'x-request-id: demo-001' \
  -d '{"question":"How should I keep a Cloud Run demo cheap?"}' | jq
```

The default `LLM_PROVIDER=mock` does not require any API key. To use Gemini Flash:

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

To use an OpenAI-compatible chat completions endpoint:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

Do not commit `.env` files or secrets.

## API

`GET /healthz`

Returns process health.

`GET /readyz`

Confirms the corpus was loaded and indexed.

`GET /v1/documents`

Lists synthetic source documents and sections.

`POST /v1/ask`

```json
{
  "question": "What should I check if a Cloud Run revision keeps restarting?",
  "top_k": 4
}
```

Response fields:

- `answer`: grounded answer or refusal
- `citations`: source chunks with document ID, section, score, and excerpt
- `grounded`: whether retrieval found usable context
- `refusal`: whether the service declined to invent unsupported details
- `request_id`: request ID propagated through middleware

## Quality checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
uv run rag-eval
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra init -backend=false
terraform -chdir=infra validate
docker build --tag cloudops-rag-eval:local .
```

Install pre-commit hooks:

```bash
uv run pre-commit install
```

## Evaluation

The evaluation set lives in `eval/questions.json`. It checks whether retrieval returns
expected source documents and whether unsupported topics are refused.

```bash
uv run rag-eval --json
uv run rag-eval --fail-under 0.8
```

Example topics include Cloud Run cost controls, startup loops, API token scopes, artifact
permissions, and unsupported Kubernetes deployment requests.

## Docker

```bash
docker build --tag cloudops-rag-eval:local .
docker run --rm -p 8080:8080 cloudops-rag-eval:local
```

## Manual GCP deployment

Terraform is under `infra/`. It creates:

- Artifact Registry Docker repository
- Cloud Run v2 service
- Cloud Run service account
- optional budget alert

Defaults are intentionally small: Cloud Run min instances `0`, max instances `2`, 1 CPU,
512 MiB memory, no bucket, no database, no NAT gateway, no Cloud SQL, and no Firestore.

Check current pricing before deploying:

- [Cloud Run pricing](https://cloud.google.com/run/pricing)
- [Google Cloud free features](https://docs.cloud.google.com/free/docs/free-cloud-features)

Install Terraform:

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

Create the Artifact Registry repository first:

```bash
export PROJECT_ID="$(gcloud config get-value project)"
export REGION="us-central1"
export REPO="cloudops-rag-eval"
export IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/app:demo"

terraform -chdir=infra init
terraform -chdir=infra apply \
  -target=google_project_service.required \
  -target=google_artifact_registry_repository.app \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="image=$IMAGE"
```

Build and push:

```bash
gcloud auth configure-docker "$REGION-docker.pkg.dev"
docker build --tag "$IMAGE" .
docker push "$IMAGE"
```

Apply the Cloud Run service and optional budget alert:

```bash
terraform -chdir=infra apply \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="image=$IMAGE" \
  -var="llm_provider=gemini" \
  -var="gemini_api_key_secret=cloudops-rag-eval-gemini-api-key" \
  -var="gemini_model=gemini-2.5-flash" \
  -var="budget_billing_account_id=XXXXXX-XXXXXX-XXXXXX" \
  -var="budget_alert_email=you@example.com"
```

Skip the budget variables if you do not have billing-budget permissions, but create a budget
alert in the console before an interview demo.

Create or update the Gemini secret before applying with `llm_provider=gemini`:

```bash
printf '%s' "$GEMINI_API_KEY" | gcloud secrets create cloudops-rag-eval-gemini-api-key \
  --data-file=- \
  --replication-policy=automatic

printf '%s' "$GEMINI_API_KEY" | gcloud secrets versions add cloudops-rag-eval-gemini-api-key \
  --data-file=-
```

Clean up after the demo:

```bash
terraform -chdir=infra destroy \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="image=$IMAGE"

gcloud artifacts docker images delete "$IMAGE" --quiet
```

## Notes

- The app uses synthetic docs for a fictional Acme CloudOps Platform.
- The local Chroma index is rebuilt at startup from markdown files.
- Logs are JSON and include request/correlation IDs.
- Sensitive log fields and email addresses are masked.
- CI runs checks and Docker build validation only; it does not deploy.
