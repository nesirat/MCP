#!/bin/bash

# Farben für die Ausgabe
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[0;33m'

# Repository URL
REPO_URL="git@github.com:nesirat/Vulnerability-MCP-Server.git"

echo -e "${GREEN}=== MCP Server Installation ===${NC}"

# Prüfe und installiere curl falls nicht vorhanden
if ! command -v curl &> /dev/null; then
    echo "Installiere curl..."
    apt-get update && apt-get install -y curl
fi

# SSH Setup für GitHub
echo "Richte SSH für GitHub ein..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/known_hosts
chmod 644 ~/.ssh/known_hosts

# Füge GitHub zu known_hosts hinzu
echo "Füge GitHub zu known_hosts hinzu..."
ssh-keyscan github.com >> ~/.ssh/known_hosts

# Generiere SSH Key falls nicht vorhanden
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "Generiere neuen SSH Key..."
    ssh-keygen -t ed25519 -C "root@zabbix" -f ~/.ssh/id_ed25519 -N ""
fi

# Teste GitHub Verbindung
echo "Teste GitHub Verbindung..."
ssh -T git@github.com || true

# Prüfen ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo "Docker ist nicht installiert. Starte Installation..."
    
    # Update package list
    echo "Aktualisiere Paketliste..."
    apt-get update
    
    # Install Docker
    echo "Installiere Docker..."
    apt-get install -y docker.io
    
    # Install Docker Compose
    echo "Installiere Docker Compose..."
    apt-get install -y docker-compose
    
    # Start Docker service
    echo "Starte Docker Service..."
    systemctl start docker
    systemctl enable docker
    
    # Verify installation
    echo "Überprüfe Installation..."
    docker --version
    docker-compose --version
    systemctl status docker | cat
    
    echo -e "${GREEN}Docker Installation abgeschlossen!${NC}"
fi

# Prüfen ob Docker Compose installiert ist
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose ist nicht installiert. Bitte installieren Sie Docker Compose zuerst."
    exit 1
fi

# Prüfen ob das Repository bereits existiert
if [ -d "Vulnerability-MCP-Server" ]; then
    echo "Repository existiert bereits. Führe git pull aus..."
    cd Vulnerability-MCP-Server
    git pull origin main
else
    echo "Klone das Repository..."
    git clone "$REPO_URL"
    cd Vulnerability-MCP-Server
fi

# Docker Container starten
echo "Starte Docker Container..."
docker-compose up -d

# Funktion zum Testen der Installation
test_installation() {
    echo -e "${YELLOW}=== Führe Installationstests durch... ===${NC}"
    
    # Test 1: Docker Container Status
    echo "Test 1: Überprüfe Docker Container Status..."
    if docker ps | grep -q "vulnerability-mcp-server"; then
        echo -e "${GREEN}✓ Docker Container laufen${NC}"
    else
        echo -e "${RED}✗ Docker Container laufen nicht${NC}"
        return 1
    fi
    
    # Test 2: Datenbank-Verbindung
    echo "Test 2: Überprüfe Datenbank-Verbindung..."
    if docker exec vulnerability-mcp-server_db_1 pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Datenbank ist erreichbar${NC}"
    else
        echo -e "${RED}✗ Datenbank ist nicht erreichbar${NC}"
        return 1
    fi
    
    # Test 3: API-Verfügbarkeit
    echo "Test 3: Überprüfe API-Verfügbarkeit..."
    if curl -s http://localhost:8000/docs > /dev/null; then
        echo -e "${GREEN}✓ API ist erreichbar${NC}"
    else
        echo -e "${RED}✗ API ist nicht erreichbar${NC}"
        return 1
    fi
    
    # Test 4: Admin-Benutzer
    echo "Test 4: Überprüfe Admin-Benutzer..."
    if docker exec vulnerability-mcp-server_app_1 python -c "from app.database import SessionLocal; from app.models import User; db = SessionLocal(); admin = db.query(User).filter(User.email == 'admin@mcp.local').first(); print('✓' if admin else '✗')" | grep -q "✓"; then
        echo -e "${GREEN}✓ Admin-Benutzer existiert${NC}"
    else
        echo -e "${RED}✗ Admin-Benutzer existiert nicht${NC}"
        return 1
    fi
    
    echo -e "${GREEN}=== Installationstests abgeschlossen ===${NC}"
    return 0
}

# Funktion zum Ermitteln der Server-IP
get_server_ip() {
    if command -v ip &> /dev/null; then
        ip addr show | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | cut -d/ -f1 | head -n1
    else
        hostname -I | awk '{print $1}'
    fi
}

# Nach der Installation
echo "Warte auf Container-Start..."
sleep 10

# Führe die Installation aus
docker-compose exec -T app python install.py

# Führe Tests durch
test_installation

# Ermittle die Server-IP
SERVER_IP=$(get_server_ip)

echo -e "${GREEN}=== Installation abgeschlossen! ===${NC}"
echo "Die Anwendung ist unter http://${SERVER_IP}:8000 erreichbar"
echo "Admin-Anmeldedaten:"
echo "Email: admin@mcp.local"
echo "Passwort: Admin@123" 