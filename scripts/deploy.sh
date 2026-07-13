#!/bin/bash
set -euo pipefail

# Fix its own line endings immediately (defensive)
if [ -f "$0" ]; then
  tr -d '\r' < "$0" > "${0}.clean" 2>/dev/null && mv "${0}.clean" "$0" || true
fi

APP_DIR="${APP_DIR:-/opt/devdeploy}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env}"
PROJECT_NAME="devdeploy"

echo "===================================="
echo "DevDeploy - Production application Deployment..."
echo "Started at $(date)"
echo "===================================="

# Ensure application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "Creating application directory: $APP_DIR"
    sudo mkdir -p "$APP_DIR"
    sudo chown -R "$USER":"$USER" "$APP_DIR" 2>/dev/null || true
fi

cd "$APP_DIR" || {
    echo "Error: Failed to change directory to '$APP_DIR'."
    exit 1
}

# Pre-flight checks
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found."
    exit 1
fi

if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: Docker Compose file '$DOCKER_COMPOSE_FILE' not found."
    exit 1
fi

echo "Pre-flight checks passed."
echo "Using compose file: $DOCKER_COMPOSE_FILE"
echo "Using environment file: $ENV_FILE"
echo "Application directory: $APP_DIR"

# docker-compose automatically loads .env from current directory
echo "Pulling latest Docker images..."
docker compose -f "$DOCKER_COMPOSE_FILE" pull --quiet || true

echo "Building latest Docker images..."
docker compose -f "$DOCKER_COMPOSE_FILE" build --pull

echo "Starting/updating services..."
docker compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans

echo "Running database migrations..."
docker compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py migrate --no-input

echo "Collecting static files..."
docker compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py collectstatic --no-input --clear

echo "Restarting application services..."
docker compose -f "$DOCKER_COMPOSE_FILE" restart web celery_worker celery_beat

echo "Performing health check..."
if [ -f "./scripts/healthcheck.sh" ]; then
    chmod +x ./scripts/healthcheck.sh
    ./scripts/healthcheck.sh
else
    echo "Warning: healthcheck.sh not found. Skipping health check."
    sleep 5
    docker compose -f "$DOCKER_COMPOSE_FILE" ps
fi

echo "Cleaning up unused Docker resources..."
docker system prune -f --volumes || true

echo ""
echo "===================================="
echo "Deployment completed successfully!"
echo "Time: $(date)"
echo "Public IP: ${EC2_PUBLIC_IP:-N/A}"
echo "===================================="