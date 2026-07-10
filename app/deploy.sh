#!/bin/bash

echo "🚀 Starting Production Deployment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${YELLOW}⚠️  .env.production not found. Creating from example...${NC}"
    cp .env.example .env.production
    echo -e "${YELLOW}⚠️  Please update .env.production with production values!${NC}"
    exit 1
fi

# Build images
echo -e "${GREEN}📦 Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build

# Run migrations
echo -e "${GREEN}🗄️  Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

# Collect static files
echo -e "${GREEN}📁 Collecting static files...${NC}"
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

# Start services
echo -e "${GREEN}🎬 Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Show status
echo -e "${GREEN}📊 Service status:${NC}"
docker-compose -f docker-compose.prod.yml ps

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}🌐 Application available at http://localhost${NC}"