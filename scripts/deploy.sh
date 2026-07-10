#!/bin/bash
set -euo pipefail

# Fix its own line endings immediately (defensive)
if [ -f "$0" ]; then
  tr -d '\r' < "$0" > "${0}.clean" 2>/dev/null && mv "${0}.clean" "$0" || true
fi


# This script is designed to be run on the EC2 instance.
# It is typically called by GitHub Actions CD workflow.

APP_DIR="${APP_DIR:-/opt/devdeploy}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env}"
PROJECT_NAME="devdeploy"

echo "===================================="
echo "DevDeploy - Production application Deployment..."
echo "Started at $(date)"
echo "===================================="

# Pre flight checks
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found."
    echo "Please ensure the runtime environment file is present."
    exit 1
fi

if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: Docker Compose file '$DOCKER_COMPOSE_FILE' not found."
    echo "Please ensure the Docker Compose file is in the current directory."
    exit 1
fi

echo " Pre-flight checks passed. Proceeding with deployment..."
echo " - Using compose file: $DOCKER_COMPOSE_FILE"
echo " - Environment file: $ENV_FILE"
echo " - Application directory: $APP_DIR"

# Ensure we're in the correct directory

if [! -d "$APP_DIR" ]; then
    echo " Creating application directory: $APP_DIR"
    sudo mkdir -p "$APP_DIR"
    sudo chown -R "$USER":"$USER" "$APP_DIR" 2>/dev/null || true
fi

cd "$APP_DIR" || {
    echo "Error: Failed to change directory to '$APP_DIR'."
    exit 1
}

# Copy latest compose and nginx config (if running from CI)
# Load environment variables

echo "Loading environment variables from $ENV_FILE..."
set -a 
source "$ENV_FILE"
set +a

# pull / Build the latest images
echo "Pulling the latest Docker images..."
docker-compose -f "$DOCKER_COMPOSE_FILE" pull --quiet || true
docker-compose -f "$DOCKER_COMPOSE_FILE" build --pull

# Deploy Services
echo "Starting / updating services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans

# Run Django Management Commands
echo "Running Django migrations..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py migrate --no-input

echo "Collecting static files..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py collectstatic --no-input --clear

# Restart Services (ensures clean state)
echo "Restarting services to ensure a clean state..."
docker-compose -f "$DOCKER_COMPOSE_FILE" restart web celery_worker celery_beat

# Health Check
echo "Performing health check on the web service..."
if [ -f "./scripts/health_check.sh" ]; then
    ./scripts/health_check.sh
else
    echo "Warning: Health check script not found. Skipping health check."
    sleep 5
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
fi

# Cleanup
echo "Cleaning up unused Docker resources..."
docker system prune -f --volumes || true

echo ""
echo "===================================="
echo "Deployment completed successfully!"
echo "Time: $(date)"
echo "Public IP: ${EC2_PUBLIC_IP:-N/A}"
echo "===================================="
