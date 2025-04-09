#!/bin/bash

echo "=== Starting Server Update ==="

# Pull latest changes
echo "Pulling latest changes from git..."
git clean -f
git pull origin main

# Stop and remove containers
echo "Stopping and removing containers..."
docker-compose down

# Rebuild and start containers
echo "Building and starting containers..."
docker-compose build --no-cache
docker-compose up -d

# Wait for containers to be ready
echo "Waiting for containers to be ready..."
sleep 5

# Reset admin user
echo "Resetting admin user..."
docker-compose exec -T app bash -c "cd /app && PYTHONPATH=/app python reset_admin.py"

echo "=== Server Update Complete ===" 