# CI/CD

The repository includes three GitHub Actions workflows.

## CI

File: `.github/workflows/ci.yml`

Runs on pushes, pull requests, and manual dispatch.

Backend checks:

- install Python dependencies
- compile backend source
- run Alembic migrations
- seed demo data
- start FastAPI
- verify case-type model endpoint
- verify legal-issue model endpoint
- verify Research & Draft endpoints

Frontend checks:

- `npm ci`
- `npm run lint`
- `npm run build`

CI intentionally disables external LLM and live web search by default. Those integrations are verified through safe fallback behavior unless provider keys are configured in a deployment environment.

## Runtime Certification

File: `.github/workflows/runtime-certification.yml`

Manual workflow for a deeper pre-demo check. It starts backend and frontend, then runs:

```bash
python -m app.seed.verify_runtime
```

This produces certification artifacts under `verification_reports/` and uploads them to the GitHub Actions run.

## CD

File: `.github/workflows/cd.yml`

Runs after CI completes successfully on the default branch, or manually.

It builds and publishes:

```text
ghcr.io/Hamza-khan0/pakistanlegalsystem/backend:<commit-sha>
ghcr.io/Hamza-khan0/pakistanlegalsystem/frontend:<commit-sha>
```

It also publishes `latest` tags on the default branch.

The workflow uploads a Hostinger deployment bundle containing:

```text
docker-compose.yml
deploy.sh
images.env
```

## Hostinger Deploy

The CD workflow can deploy to a Hostinger VPS when manually dispatched with `deploy_hostinger=true` and these secrets configured:

```text
HOSTINGER_HOST
HOSTINGER_USER
HOSTINGER_SSH_KEY
HOSTINGER_PORT
HOSTINGER_APP_DIR
GHCR_USERNAME
GHCR_TOKEN
```

`GHCR_USERNAME` and `GHCR_TOKEN` are only required if package visibility is private.

The server must already have Docker and Docker Compose installed. Shared hosting plans generally cannot run this backend.

## First Push Setup

This workspace was initially not a Git repository. Before CI/CD can run:

```bash
git init
git branch -M main
git remote add origin https://github.com/Hamza-khan0/pakistanlegalsystem.git
git add .
git commit -m "Prepare AI Legal Chambers for CI/CD"
git push -u origin main
```

If GitHub asks for authentication, sign in through Git Credential Manager or install and authenticate GitHub CLI.
