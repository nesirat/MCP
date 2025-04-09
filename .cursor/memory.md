# Cursor Memory for Vulnerability MCP Server

## Project Context
This is a web application for managing and monitoring vulnerabilities. The application is built using Python FastAPI, Docker, and PostgreSQL.

## Key Files and Their Purposes

### Backend Files
- `app/config.py`: Configuration settings and environment variables
- `app/models.py`: Database models and schemas
- `app/main.py`: Main application entry point and API routes

### Frontend Files
- `app/index.html`: Main login page
- `app/dashboard.html`: User dashboard
- `app/admin.html`: Admin panel
- `app/register.html`: User registration page
- `app/main.js`: Frontend JavaScript functionality

### Configuration Files
- `docker-compose.yml`: Container orchestration
- `Dockerfile`: Application container definition
- `.env`: Environment variables
- `requirements.txt`: Python dependencies
- `alembic.ini`: Database migration configuration

### Deployment Files
- `deploy.sh`: Deployment script
- `mcp.service`: Systemd service file
- `install.py`: Installation script

## Recent Changes and Updates
1. Fixed database connectivity issues
2. Updated Docker configuration
3. Improved deployment automation
4. Enhanced security measures
5. Added user management features

## Current State
- Application is deployed on remote server (zabbix)
- Running in Docker containers
- PostgreSQL database
- JWT authentication implemented
- Admin and user interfaces functional

## Known Issues
1. Database connection timeouts (resolved)
2. Docker container networking (resolved)
3. Authentication token handling (resolved)

## Development Environment
- Python 3.11
- FastAPI framework
- SQLAlchemy ORM
- PostgreSQL database
- Docker containers
- HTML/JavaScript frontend

## Deployment Environment
- Remote server: zabbix
- Application path: /opt/mcp
- Port: 8000
- Database: PostgreSQL in Docker

## Security Considerations
- JWT tokens for authentication
- Environment variables for secrets
- Input validation
- HTTPS configuration
- Secure password handling

## Future Tasks
1. Implement additional security features
2. Add more monitoring capabilities
3. Enhance error handling
4. Optimize performance
5. Add automated testing

## Important Notes
- Keep sensitive information in .env file
- Use migrations for database changes
- Follow security best practices
- Maintain documentation
- Regular backups required 