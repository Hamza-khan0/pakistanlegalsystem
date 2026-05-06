# Hostinger Deployment

This deployment path assumes a Hostinger VPS or another Linux server with Docker and Docker Compose installed. Hostinger shared hosting usually cannot run the FastAPI backend or Docker containers.

## Server Files

Copy these files to the server application directory, for example `~/ai-legal-chambers`:

```text
deploy/hostinger/docker-compose.yml -> ~/ai-legal-chambers/docker-compose.yml
deploy/hostinger/deploy.sh          -> ~/ai-legal-chambers/deploy.sh
```

Create server-side environment files:

```text
~/ai-legal-chambers/.env
~/ai-legal-chambers/.env.backend
```

Example `.env`:

```bash
BACKEND_IMAGE=ghcr.io/hamza-khan0/pakistanlegalsystem/backend:latest
FRONTEND_IMAGE=ghcr.io/hamza-khan0/pakistanlegalsystem/frontend:latest
FRONTEND_PORT=3000
BACKEND_PORT=8000
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
INTERNAL_API_BASE_URL=http://backend:8000
CORS_ORIGINS=https://example.com,https://www.example.com
```

Example `.env.backend`:

```bash
cp backend.env.example .env.backend
```

Keep real secrets only on the server or in GitHub Actions secrets. Do not commit them.

## Manual Deploy

```bash
cd ~/ai-legal-chambers
chmod +x deploy.sh
./deploy.sh
```

## GitHub Actions Deploy

The `CD` workflow can SSH into the server after container images are published when these repository secrets are configured:

```text
HOSTINGER_HOST
HOSTINGER_USER
HOSTINGER_SSH_KEY
HOSTINGER_PORT
HOSTINGER_APP_DIR
GHCR_USERNAME
GHCR_TOKEN
```

`GHCR_USERNAME` and `GHCR_TOKEN` are only needed when the GHCR images are private.
