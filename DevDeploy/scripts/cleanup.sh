#!/bin/bash
set -euo pipefail

# DevDeploy - Cleanup Script
# Removes stopped containers, unused images, and volumes.


DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"

echo " Running cleanup for DevDeploy..."

# Stop services if running
if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Stopping services..."
    docker compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true
fi

# Clean up
echo "Pruning unused containers, networks, and images..."
docker container prune -f
docker network prune -f
docker image prune -f

echo " Cleanup complete."
echo "Note: Volumes were NOT removed to preserve data."
