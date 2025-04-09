# MCP Vulnerability Management System

MCP (Management Control Panel) is a comprehensive vulnerability management system that helps organizations track, manage, and respond to security vulnerabilities effectively.

## Features

- User Authentication and Authorization
- Admin Dashboard
- User Profile Management
- Vulnerability Tracking
- Support Ticket System
- API Key Management
- SSL Certificate Management
- Newsletter Subscription
- Activity Logging

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher
- Docker and Docker Compose (optional)

## Installation

### Option 1: Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp.git
cd mcp
```

2. Create a .env file:
```bash
cp .env.example .env
```
Edit the .env file with your configuration.

3. Build and start the containers:
```bash
docker-compose up -d
```

4. Create the admin user:
```bash
docker-compose exec app python install.py
```

### Option 2: Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp.git
cd mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file:
```bash
cp .env.example .env
```
Edit the .env file with your configuration.

5. Set up the database:
```bash
createdb mcp
```

6. Create the admin user:
```bash
python install.py
```

7. Start the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Usage

1. Access the application at http://localhost:8000
2. Log in with your admin credentials
3. Configure SSL certificates in the admin interface
4. Start managing vulnerabilities and users

## API Documentation

The API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 guidelines. To check your code:

```bash
flake8
```

### Database Migrations

To create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 