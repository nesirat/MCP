#!/bin/bash

# Configuration
APP_NAME="mcp"
DEPLOY_DIR="/opt/$APP_NAME"
REPO_URL="https://github.com/yourusername/mcp.git"  # Update with your actual repo URL

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting deployment of $APP_NAME...${NC}"

# Create deployment directory if it doesn't exist
if [ ! -d "$DEPLOY_DIR" ]; then
    echo -e "${YELLOW}Creating deployment directory...${NC}"
    mkdir -p "$DEPLOY_DIR"
fi

# Clean up existing deployment
echo -e "${YELLOW}Cleaning up existing deployment...${NC}"
rm -rf "$DEPLOY_DIR"/*

# Clone repository
echo -e "${YELLOW}Cloning repository...${NC}"
git clone "$REPO_URL" "$DEPLOY_DIR"

# Navigate to deployment directory
cd "$DEPLOY_DIR"

# Make scripts executable
echo -e "${YELLOW}Setting up scripts...${NC}"
chmod +x scripts/*.sh

# Run setup script
echo -e "${YELLOW}Running setup script...${NC}"
./scripts/setup.sh

# Verify deployment
echo -e "${YELLOW}Verifying deployment...${NC}"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${YELLOW}Application is running at:${NC}"
    echo -e "  - API: http://$(hostname -I | awk '{print $1}'):8000"
    echo -e "  - API Documentation: http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo -e "  - Flower (Celery monitoring): http://$(hostname -I | awk '{print $1}'):5555"
    echo -e "${YELLOW}Default admin credentials:${NC}"
    echo -e "  - Email: admin@example.com"
    echo -e "  - Password: admin"
else
    echo -e "${RED}Deployment failed!${NC}"
    exit 1
fi 