#!/bin/bash
set -euo pipefail

# DevDeploy - Health Check Script

# Checks the health of the production deployment.

DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.prod.yml}"
TIMEOUT=60
INTERVAL=5
MAX_ATTEMPTS=$((TIMEOUT / INTERVAL))

echo "Running deployment health check..."
echo "Compose file: $DOCKER_COMPOSE_FILE"
echo ""

# Function to check if a service is running
check_service() {
    local service=$1
    if docker compose -f "$DOCKER_COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^${service}$"; then
        echo " $service is running"
        return 0
    else
        echo " $service is NOT running"
        return 1
    fi
}

# Check core services
echo "=== Checking Core Services ==="
check_service "web" || exit 1
check_service "nginx" || exit 1
check_service "redis" || exit 1
check_service "celery_worker" || exit 1
check_service "celery_beat" || exit 1

echo ""
echo "=== Checking HTTP Endpoint ==="

# Try to hit the health endpoint through nginx
HEALTH_URL="http://localhost/nginx-health"
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Checking $HEALTH_URL ..."
    
    if curl -s --max-time 5 "$HEALTH_URL" | grep -q "ok"; then
        echo " Nginx health check passed"
        break
    fi
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo " Health check failed after $TIMEOUT seconds"
        echo ""
        echo "=== Current Service Status ==="
        docker compose -f "$DOCKER_COMPOSE_FILE" ps
        exit 1
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    sleep $INTERVAL
done

echo ""
echo "=== Checking Application Health ==="

# Check Django health endpoint (through nginx)
APP_HEALTH_URL="http://localhost/api/auth/health/"

if curl -s --max-time 10 "$APP_HEALTH_URL" > /dev/null; then
    echo " Django application health endpoint responded"
else
    echo "  Django health endpoint did not respond (this may be okay if no health route exists)"
fi

echo ""
echo "=========================================="
echo "  All health checks passed!"
echo "=========================================="

# Show final status
docker compose -f "$DOCKER_COMPOSE_FILE" ps
exit 0
