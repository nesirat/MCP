#!/bin/bash

# Create necessary directories
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Set permissions
chmod -R 777 logs
chmod -R 777 data

# Generate secret key if not exists
if [ ! -f .env ]; then
    echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
    echo "DEBUG=False" >> .env
fi

# Build and start containers
docker-compose build
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run database migrations
docker-compose exec app alembic upgrade head

# Create initial admin user
docker-compose exec app python -c "
from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
db = SessionLocal()
if not db.query(User).filter(User.email == 'admin@example.com').first():
    db_user = User(
        email='admin@example.com',
        hashed_password=get_password_hash('admin'),
        is_active=True,
        is_superuser=True
    )
    db.add(db_user)
    db.commit()
db.close()
"

echo "Setup completed successfully!" 