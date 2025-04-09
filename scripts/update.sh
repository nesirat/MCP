#!/bin/bash

# Pull latest changes
git pull origin main

# Stop existing containers
docker-compose down

# Build and start containers
docker-compose build
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run database migrations
docker-compose exec app alembic upgrade head

# Restart Celery workers
docker-compose restart celery

echo "Update completed successfully!" 