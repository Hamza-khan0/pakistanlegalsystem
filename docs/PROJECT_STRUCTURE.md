# Project Structure

AI Legal Chambers is organized as a two-service application with explicit boundaries between source code, generated artifacts, model/data assets, deployment assets, and verification tooling.

## Source Layout

```text
app/                         Next.js App Router pages
components/                  Frontend UI components
lib/                         Frontend API client and utilities
types/                       Shared frontend TypeScript types
public/                      Static frontend assets
backend/app/                 FastAPI application source
backend/app/api/routes/      Backend route modules
backend/app/models/          SQLAlchemy models
backend/app/schemas/         Pydantic schemas
backend/app/services/        Domain services and ML/retrieval workflows
backend/app/seed/            Seed data and command modules
backend/scripts/             Runtime verification scripts
backend/alembic/             Database migration environment and versions
deploy/hostinger/            Hostinger VPS Docker deployment assets
docs/                        Architecture, CI/CD, and operations notes
.github/workflows/           CI, CD, and runtime certification workflows
```

## Generated or Local-Only Paths

These paths are intentionally ignored and should not be committed:

```text
backend/dev.db
backend/uploads/
backend/crawl_storage/
backend/data/
backend/exports/
backend/generated/
backend/ml_artifacts/
backend/trained_models/
backend/trainedmodels/
training_export/
verification_reports/
*.log
*.out.log
*.err.log
```

They contain local uploads, OCR/crawl output, trained model bundles, generated PDFs, runtime reports, and debugging logs.

## Cleanup Rule

Do not delete local legal data or trained models during source cleanup. Keep source cleanup focused on:

- `.gitignore` coverage
- CI/CD automation
- documentation
- Docker/deployment assets
- source files that are imported by the app

Use `scripts/maintenance/clean-local-artifacts.ps1` only when you intentionally want to move local logs into an ignored archive folder.
