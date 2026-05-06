#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${HOSTINGER_APP_DIR:-$HOME/ai-legal-chambers}"
COMPOSE_FILE="$APP_DIR/docker-compose.yml"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Missing $COMPOSE_FILE. Copy deploy/hostinger/docker-compose.yml to the server first." >&2
  exit 1
fi

cd "$APP_DIR"

set -a
if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  source ".env"
fi
if [[ -f "images.env" ]]; then
  # shellcheck disable=SC1091
  source "images.env"
fi
set +a

if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
fi

docker compose pull
docker compose up -d --remove-orphans
docker compose ps
