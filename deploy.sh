#!/bin/bash

# Exit on error
set -e

# Configuration
APP_NAME="vuln_mcp"
APP_DIR="/opt/$APP_NAME"
DB_NAME="vuln_mcp"
DB_USER="vuln_mcp"
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 32)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting deployment of $APP_NAME...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt update
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# Create application directory
echo -e "${YELLOW}Creating application directory...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

# Set up virtual environment
echo -e "${YELLOW}Setting up virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Set up PostgreSQL
echo -e "${YELLOW}Setting up PostgreSQL...${NC}"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Create environment file
echo -e "${YELLOW}Creating environment file...${NC}"
cat > $APP_DIR/.env << EOL
# Server Configuration
PORT=8000
HOST=0.0.0.0
DEBUG=False

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Security
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Data Limits
MAX_DATA_STORAGE_GB=100
MAX_CONCURRENT_USERS=50

# MCP Configuration
MCP_VERSION=1.0.0
MCP_AUTH_REQUIRED=true
EOL

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/$APP_NAME.service << EOL
[Unit]
Description=Vulnerability MCP Server
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Set up Nginx
echo -e "${YELLOW}Setting up Nginx...${NC}"
cat > /etc/nginx/sites-available/$APP_NAME << EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl start $APP_NAME
systemctl restart nginx

# Create initial admin user
echo -e "${YELLOW}Creating initial admin user...${NC}"
python3 -c "
from app.db.database import SessionLocal
from app.db import models
from passlib.context import CryptContext

db = SessionLocal()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

admin = models.User(
    email='admin@example.com',
    hashed_password=pwd_context.hash('admin123'),
    is_active=True,
    is_superuser=True
)
db.add(admin)
db.commit()
db.close()
"

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Please change the default admin password after first login${NC}"
echo -e "${YELLOW}Default credentials:${NC}"
echo -e "Email: admin@example.com"
echo -e "Password: admin123" 