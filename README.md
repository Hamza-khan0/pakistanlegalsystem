# AI Legal Chambers by HAMZA KHAN AND NABEEGH

AI Legal Chambers is a Pakistani legal-tech workspace that now combines:

- a polished legal operations frontend
- a persistent legal matter backend
- grounded chamber workflows
- a crawler/OCR/corpus pipeline for English and Urdu legal materials
- supervised ML/DNN prediction tasks
- Phase 9 training-readiness, calibration, reranking, benchmarking, and evaluation reporting

## Stack

### Frontend

- Next.js 16 App Router
- TypeScript
- Tailwind CSS v4
- Lucide React

### Backend

- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- Alembic
- Uvicorn
- PostgreSQL-ready configuration with SQLite local fallback
- python-multipart
- pypdf
- PyMuPDF
- pytesseract
- Pillow
- httpx
- Beautiful Soup 4
- scikit-learn
- PyTorch
- Hugging Face transformers

## Phase 9 Highlights

- Dataset readiness validation for all four tasks:
  - class distribution
  - split health
  - weak-label share
  - OCR-quality signal
  - leakage warnings
- Retrieval benchmark framework comparing:
  - lexical retrieval
  - semantic retrieval
  - hybrid retrieval with reranking
- Calibration scaffolding with:
  - reliability-bin payloads
  - confidence histograms
  - expected calibration error
  - calibration-ready metadata for later scaling methods
- Exportable evaluation reports in JSON + Markdown
- Chamber quality scoring that tracks:
  - retrieval mode
  - grounding strength
  - critic flags
  - unsupported-claim warnings
  - memory-source usage
- `/models`, `/knowledge`, `/workspace`, and `/cases/[id]` upgraded with training-readiness and evaluation surfaces

## Tier 1 Training Data Preparation

The project now includes a practical Tier 1 data-preparation layer. It prepares real legal data for manual/local/cloud training, but it does not start final model training automatically.

### Supported import paths

- Local folder import from `backend/data/tier1/manual_import/`
- Kaggle import from configured dataset slugs when `KAGGLE_USERNAME` and `KAGGLE_KEY` are set
- Hugging Face import when `HF_TOKEN` and the optional `datasets` package are available

Supported local files:

- `.txt`
- `.json`
- `.jsonl`
- `.csv`
- `.pdf` through the existing extraction/OCR pipeline where supported

### Tier 1 environment variables

Keep credentials in environment variables only:

```bash
KAGGLE_USERNAME=
KAGGLE_KEY=
HF_TOKEN=
TIER1_DATA_DIR=backend/data/tier1
TIER1_RAW_DIR=backend/data/tier1/raw
TIER1_PROCESSED_DIR=backend/data/tier1/processed
TIER1_LABEL_AUDIT_DIR=backend/data/tier1/label_audit
TRAINING_EXPORT_DIR=training_export
```

Kaggle/Hugging Face imports return clear warnings when credentials are missing. They should not crash and should not expose secrets to the frontend.

### Tier 1 workflow

Put manually downloaded legal data in:

```text
backend/data/tier1/manual_import/
```

Then run:

```bash
cd backend
python -m app.seed.prepare_tier1_data
```

This runs:

- local import
- optional Kaggle import if credentials are configured
- optional Hugging Face import if configured
- weak-label extraction for all four prediction tasks
- deterministic dataset build
- training bundle export

It does not train final models.

### Individual Tier 1 commands

```bash
cd backend
python -m app.seed.import_tier1_local
python -m app.seed.import_tier1_kaggle
python -m app.seed.import_tier1_huggingface
python -m app.seed.build_tier1_datasets
python -m app.seed.export_training_bundle
```

### Tier 1 API routes

```text
POST /api/tier1/import/local
POST /api/tier1/import/kaggle
POST /api/tier1/import/huggingface
GET /api/tier1/documents
GET /api/tier1/documents/{document_id}
GET /api/tier1/labels
GET /api/tier1/labels/audit
PATCH /api/tier1/labels/{label_id}
POST /api/tier1/datasets/build
GET /api/tier1/datasets/readiness
POST /api/tier1/export/training-bundle
GET /api/tier1/reports
```

### Training export

Exports are written to:

```text
training_export/
training_export_bundle.zip
```

The bundle includes task/split JSONL files, metadata reports, readiness reports, source reports, and a training README. It excludes credentials and does not trigger model training.

## Prediction Tasks

Phase 8 continues to support these four prediction tasks:

1. `case_outcome`
2. `maintainability`
3. `risk_scoring`
4. `case_type`

These predictions remain explicitly framed as predictive assistance only, not guaranteed legal truth.

## Multilingual Model Design

### Baselines

- TF-IDF + Logistic Regression for text-heavy tasks
- Random Forest for risk-scoring baseline

### Transformer path

The default multilingual transformer path remains:

- `distilbert-base-multilingual-cased`

Phase 8 adds cleaner configurability for stronger multilingual experimentation through:

- `ML_TRANSFORMER_MODEL_NAME`
- `ML_TRANSFORMER_STRONG_MODEL_NAME`

Example stronger option:

- `xlm-roberta-base`

This keeps the project practical on modest hardware while still supporting a more serious multilingual NLP architecture for the semester project.

### Hybrid deep model

The hybrid model combines:

- tokenized text representation
- structured legal/procedural features
- an MLP classifier head

It remains especially useful for:

- maintainability prediction
- risk scoring

## Semantic Retrieval Architecture

Phase 8 adds a real semantic retrieval layer over the legal corpus.

### Index build

The semantic index:

- encodes legal source chunks with a multilingual transformer encoder
- stores normalized embeddings on disk
- persists index metadata in the database
- records vector dimension, source count, corpus version, and model name

### Retrieval modes

The system now supports:

- `Lexical`
- `Semantic`
- `Hybrid`

`SEMANTIC_QUERY_MODE=fast` is the local development default. It keeps semantic search responsive by scoring persisted semantic-index records with deterministic multilingual concept overlap. Set `SEMANTIC_QUERY_MODE=transformer` when you want each query encoded through the configured transformer model.

### Hybrid retrieval

Hybrid retrieval combines:

- lexical relevance
- semantic similarity
- task-aware weighting
- lightweight reranking bonuses for:
  - statutes/rules in procedural tasks
  - case-law style sources in research tasks
  - language match
  - citation/section overlap

### Chamber integration

Grounded chamber workflows now persist:

- retrieval mode
- fusion weights
- semantic index metadata
- richer source-level grounding diagnostics

## Explainability and Diagnostics

### Prediction diagnostics

Phase 8 adds:

- model diagnostics endpoint
- case prediction explanation endpoint
- richer prediction UI notes
- per-language evaluation exposure

### Retrieval diagnostics

Phase 8 adds:

- semantic index status endpoint
- retrieval leaderboard/evaluation endpoints
- run grounding diagnostics endpoint
- source-level explanation fields in the UI

The system remains honest about limitations. Transformer explanations are lightweight and do not pretend to offer perfect token-level interpretability.

## Project Structure

```text
app/
components/
  chamber/
  knowledge/
  models/
lib/
types/
backend/
  alembic/
  app/
    api/
    core/
    db/
    models/
    schemas/
    seed/
      crawl_sources/
      legal_sources/
      ml_labels.json
    services/
      agents/
      corpus/
      crawling/
      grounding/
      intelligence/
      knowledge/
        embeddings.py
        hybrid_retrieval.py
        retrieval.py
        semantic_index.py
      llm/
      memory/
      ml/
        datasets/
        training/
          diagnostics.py
      ocr/
      orchestration/
    utils/
  uploads/
  crawl_storage/
  exports/
  ml_artifacts/
```

## Environment Setup

Copy `.env.example` to `.env` and adjust values if needed.

### Core variables

```bash
DATABASE_URL=sqlite:///./backend/dev.db
UPLOADS_DIR=backend/uploads
CRAWL_STORAGE_DIR=backend/crawl_storage
CORPUS_EXPORTS_DIR=backend/exports/corpus
CRAWL_SEED_DIR=backend/app/seed/crawl_sources
ML_ARTIFACTS_DIR=backend/ml_artifacts
RETRIEVAL_ARTIFACTS_DIR=backend/ml_artifacts/retrieval
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173
LLM_PROVIDER=local
LLM_PROVIDER_LABEL=Chamber Local Intelligence
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_WEB_SEARCH_MODEL=gpt-4o-mini
LIVE_WEB_SEARCH_ENABLED=false
LLM_DRAFTING_ENABLED=false
SEARCH_PROVIDER=openai
WEB_SEARCH_MAX_RESULTS=8
WEB_SEARCH_TIMEOUT_SECONDS=30
WEB_SOURCE_FETCH_TIMEOUT_SECONDS=20
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_DEFAULT_LANGUAGES=eng
ML_TRANSFORMER_MODEL_NAME=distilbert-base-multilingual-cased
ML_TRANSFORMER_STRONG_MODEL_NAME=xlm-roberta-base
ML_TRANSFORMER_MAX_LENGTH=256
ML_TRANSFORMER_EPOCHS=2
ML_TRANSFORMER_BATCH_SIZE=4
ML_HYBRID_EPOCHS=16
ML_HYBRID_BATCH_SIZE=8
ML_DEFAULT_INFERENCE_FAMILY=Baseline
ML_EMBEDDING_MODEL_NAME=distilbert-base-multilingual-cased
SEMANTIC_QUERY_MODE=fast
SEMANTIC_INDEX_BATCH_SIZE=8
SEMANTIC_RETRIEVAL_TOP_K=10
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
INTERNAL_API_BASE_URL=http://127.0.0.1:8000
```

### OpenAI-assisted research and drafting

The Research & Draft workflow works without external providers. If no OpenAI key is configured, it uses local corpus retrieval and deterministic memo/draft generation.

To enable LLM-assisted research and drafting:

```bash
OPENAI_API_KEY=sk-...
LLM_DRAFTING_ENABLED=true
OPENAI_MODEL=gpt-4o-mini
```

To enable live web legal search through the OpenAI Responses API web search tool:

```bash
OPENAI_API_KEY=sk-...
LIVE_WEB_SEARCH_ENABLED=true
SEARCH_PROVIDER=openai
OPENAI_WEB_SEARCH_MODEL=gpt-4o-mini
```

No Tavily, SerpAPI, Bing, or Google CSE key is required. Keep `OPENAI_API_KEY` server-side only. The frontend receives provider availability and privacy warnings, never secret values. When enabled, selected case text, research queries, and retrieved source excerpts may be sent to the configured OpenAI API.

### Urdu OCR

For scanned Urdu OCR, local Tesseract Urdu data is still required:

```bash
OCR_DEFAULT_LANGUAGES=eng+urd
```

## Backend Setup

Install backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Run migrations:

```bash
cd backend
alembic upgrade head
```

Seed the application:

```bash
cd backend
python -m app.seed.seed_data
```

## Corpus and Crawl Commands

```bash
cd backend
python -m app.seed.register_crawl_sources
python -m app.seed.run_crawl
python -m app.seed.process_crawled_documents
python -m app.seed.ingest_legal_sources
python -m app.seed.build_corpus
python -m app.seed.export_corpus
```

## Phase 7 / 8 ML Commands

Build supervised datasets:

```bash
cd backend
python -m app.seed.build_ml_datasets
```

Train the model suite:

```bash
cd backend
python -m app.seed.train_ml_suite
```

## Phase 8 / 9 Retrieval Commands

Run the backend and use the new API routes:

### Build semantic index

```bash
curl -X POST http://127.0.0.1:8000/api/retrieval/index/build ^
  -H "Content-Type: application/json" ^
  -d "{}"
```

### Check semantic index status

```bash
curl http://127.0.0.1:8000/api/retrieval/index/status
```

### Semantic search

```bash
curl -X POST http://127.0.0.1:8000/api/retrieval/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"article 199 writ maintainability public law relief\",\"taskType\":\"research_memo\",\"limit\":5}"
```

### Hybrid search

```bash
curl -X POST http://127.0.0.1:8000/api/retrieval/hybrid-search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"order vii rule 11 plaint rejection jurisdiction objections\",\"taskType\":\"preliminary_objections\",\"limit\":5}"
```

### Retrieval evaluation snapshot

```bash
curl http://127.0.0.1:8000/api/retrieval/leaderboard
```

### Run retrieval benchmarks

```bash
curl -X POST http://127.0.0.1:8000/api/retrieval/benchmarks/run ^
  -H "Content-Type: application/json" ^
  -d "{}"
```

### List retrieval benchmarks

```bash
curl http://127.0.0.1:8000/api/retrieval/benchmarks
```

## Prediction and Diagnostics API Examples

### Build datasets

```bash
curl -X POST http://127.0.0.1:8000/api/ml/datasets/build ^
  -H "Content-Type: application/json" ^
  -d "{}"
```

### Train a model

```bash
curl -X POST http://127.0.0.1:8000/api/ml/train ^
  -H "Content-Type: application/json" ^
  -d "{\"datasetId\":\"<dataset-id>\",\"modelFamily\":\"Baseline\"}"
```

### Predict for a case

```bash
curl -X POST http://127.0.0.1:8000/api/cases/green-valley-dha/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"caseId\":\"green-valley-dha\"}"
```

### Model diagnostics

```bash
curl http://127.0.0.1:8000/api/ml/models/<model-id>/diagnostics
```

### Calibration scaffold

```bash
curl -X POST http://127.0.0.1:8000/api/ml/models/<model-id>/calibration/build
```

### Case prediction explanations

```bash
curl http://127.0.0.1:8000/api/cases/green-valley-dha/predictions/explain
```

## Phase 9 Evaluation Commands

Validate dataset readiness:

```bash
cd backend
python -m app.seed.validate_ml_datasets
```

Run retrieval benchmarks:

```bash
cd backend
python -m app.seed.run_retrieval_benchmarks
```

Build evaluation reports:

```bash
cd backend
python -m app.seed.build_evaluation_reports
```

API routes:

```bash
curl http://127.0.0.1:8000/api/evaluation/datasets/readiness
curl -X POST http://127.0.0.1:8000/api/evaluation/reports/build -H "Content-Type: application/json" -d "{}"
curl http://127.0.0.1:8000/api/cases/green-valley-dha/quality-summary
curl http://127.0.0.1:8000/api/runs/<run-id>/quality
```

## Research & Draft Pipeline

The case workspace now includes a `Research & Draft` workflow button. It runs the `research_draft_pipeline`:

- assembles case facts, documents, notes, timeline, prior research, and prediction context
- uses the trained XLM-R legal issue classifier when available, with rule fallback
- builds issue-aware Pakistani-law research queries
- retrieves local Pakistani legal sources through hybrid lexical/semantic retrieval
- optionally searches live Pakistani legal web sources when a configured provider is available
- optionally uses `gpt-4o-mini` or the configured OpenAI model to produce source-grounded research and a full legal draft
- falls back to deterministic memo and draft-skeleton generation if external search or LLM is unavailable
- produces a structured research memo, generated draft, source trace, gaps, critic review, lawyer checklist, and drafting instructions
- stores the run in `research_runs` and writes Markdown/PDF artifacts under `backend/generated/research_runs/`

The workflow is AI-assisted only. The LLM is not treated as a source of law. It is instructed to use only retrieved local/web sources as authorities, avoid fabricated citations, and mark missing authority as a research gap. Every output includes the warning that lawyer review is required.

Fallback matrix:

- No live web and no LLM: local corpus retrieval plus deterministic research memo and draft skeleton.
- Live web configured and no LLM: local + web sources plus deterministic memo/draft skeleton.
- LLM configured and no live web: local sources plus LLM-assisted memo/draft.
- Live web and LLM configured: local + web source retrieval, LLM-assisted memo/draft, critic review, Markdown/PDF artifact generation.

API routes:

```text
GET  /api/research/health
POST /api/research/runs
GET  /api/research/runs/{run_id}
GET  /api/research/cases/{case_id}/runs
GET  /api/research/runs/{run_id}/markdown
GET  /api/research/runs/{run_id}/pdf
POST /api/research/web-search/test
```

Verification:

```bash
cd backend
python scripts/verify_research_workflow.py
python scripts/verify_research_workflow_llm_web.py
python scripts/verify_research_endpoints.py
```

## Frontend Integration

Phase 8 is surfaced in:

- `/knowledge`
  - semantic index status
  - semantic/hybrid search experiments
  - retrieval leaderboard
  - retrieval benchmark runner
  - reranking posture
- `/models`
  - richer multilingual model metadata
  - per-language diagnostics visibility
  - dataset readiness cards
  - calibration scaffolding
  - report export surface
- `/data`
  - Tier 1 local/Kaggle/Hugging Face import controls
  - imported document and source summaries
  - weak-label audit and correction queue
  - per-task Tier 1 readiness cards
  - manual training bundle export
- `/workspace`
  - chamber runs show retrieval mode and grounding diagnostics
  - chamber quality posture
- `/agents`
  - agent run inspection inherits richer grounding traces
- `/cases/[id]`
  - one-click Research & Draft pipeline
  - live web/LLM/full-draft toggles when providers are available
  - detected legal issues, query plan, retrieved Pakistani sources grouped by origin, memo, generated draft, critic warnings, lawyer checklist, and PDF/Markdown links
  - prediction diagnostics notes
  - richer grounded legal basis cards
  - model/dataset quality warnings
  - case-quality summary

## Frontend Commands

```bash
npm install
npm run lint
npm run build
npm run dev -- --hostname 127.0.0.1 --port 3001
```

`npm run dev` uses Next's webpack dev server for local certification stability. Turbopack remains available with:

```bash
npm run dev:turbo -- --hostname 127.0.0.1 --port 3001
```

## CI/CD

The project includes GitHub Actions workflows under `.github/workflows/`:

- `ci.yml` verifies backend compile/migrations/seed/API smoke checks and frontend lint/build.
- `runtime-certification.yml` is a manual full-system certification run that starts backend + frontend and runs `python -m app.seed.verify_runtime`.
- `cd.yml` publishes backend and frontend Docker images to GitHub Container Registry after CI passes, and can deploy to a Hostinger VPS when deployment secrets are configured.

Deployment assets live in:

```text
backend/Dockerfile
frontend.Dockerfile
deploy/hostinger/docker-compose.yml
deploy/hostinger/deploy.sh
docs/CI_CD.md
docs/PROJECT_STRUCTURE.md
```

The Hostinger path assumes a VPS with Docker. Shared hosting is not sufficient for the FastAPI backend, OCR/model dependencies, and persistent volumes.

## Backend Run Command

Recommended Windows-safe local command:

```powershell
cd backend
python scripts\dev_start_backend.py
```

The helper tries `8000`, then falls back to `8001`, `8002`, or `8010` if Windows blocks or reserves a port. If it starts on a fallback port, update `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001
```

Direct uvicorn still works when port `8000` is available:

```powershell
cd backend
python -m uvicorn app.main:app --reload --app-dir . --host 127.0.0.1 --port 8000
```

See [docs/LOCAL_DEV_START.md](docs/LOCAL_DEV_START.md) for the full backend/frontend startup flow.

## Runtime Certification

Use this before Tier 1 import or manual/cloud training:

```bash
cd backend
python -m compileall app
alembic upgrade head
python -m app.seed.seed_data
python -m app.seed.verify_runtime
```

The verifier writes:

```text
verification_reports/latest_runtime_certification.json
verification_reports/latest_runtime_certification.md
verification_reports/browser_route_certification.txt
```

The certification script exercises case CRUD, document upload/extraction, legal retrieval, semantic/hybrid retrieval, chamber runs, crawler/corpus export, baseline ML training, prediction, calibration scaffolding, evaluation reports, frontend routes, CORS preflights, and cleanup of its temporary matter.
Certification uses `PASS` for working runtime behavior, `WARN` for intentionally scaffolded or skipped-heavy checks, and `FAIL` for broken runtime behavior. A warning-only report is acceptable for MVP presentation, but not for final real-data training.

Training safety notes:

- Chamber agents are functional orchestrated MVP service roles, not independently trained autonomous agents.
- Baseline training is safe for local smoke tests.
- Final transformer/hybrid training should wait for real Tier 1 data and preferably GPU/cloud resources.
- Calibration is scaffolded until fitted against stronger real labels.
- Reranking is heuristic and cross-encoder-ready until a learned reranker is trained.
- Tier 1 import/export APIs are implemented, but the seeded sample data is tiny and only useful for smoke testing. Real legal data still needs to be imported and audited before manual/cloud training.

## CORS in Development

The backend uses FastAPI `CORSMiddleware` with explicit local development origins by default:

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3001`

You can override these with:

```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173
```

The middleware is configured with:

- `allow_credentials=True`
- `allow_methods=["*"]`
- `allow_headers=["*"]`

So browser preflight `OPTIONS` requests and normal API calls from the local frontend both succeed after a backend restart.

## Known Limitations

Phase 9 intentionally does not yet provide:

- full national-scale corpus completeness
- production MLOps or distributed training
- final citation validation against live authoritative sources
- final legal outcome benchmarking on a large real-world court-result corpus
- trained cross-encoder reranking
- final calibrated probabilities trained on large real data
- full explainable AI tooling
- enterprise security hardening
- strong final datasets without real Tier 1 import and human label audit
- automatic final DNN/cloud training

The Phase 9 + Tier 1 preparation goal is to make the system training-ready and evaluation-ready before spending money on larger real-data training. It now shows whether datasets are strong enough, how models compare, how retrieval modes compare, how reliable grounded chamber outputs currently are, and whether imported Tier 1 labels are ready for manual training.
