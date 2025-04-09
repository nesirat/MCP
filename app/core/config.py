from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Server Configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = False

    # Database Configuration
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "mcp"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SSL Configuration
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # Data Limits
    MAX_DATA_STORAGE_GB: int = 100
    MAX_CONCURRENT_USERS: int = 50

    # BSI Configuration
    BSI_API_KEY: Optional[str] = None
    BSI_API_URL: str = "https://www.bsi.bund.de/DE/Themen/ITGrundschutz/ITGrundschutzKataloge/Inhalt/_content/m/m01/m01001.html"

    # NVD Configuration
    NVD_API_KEY: Optional[str] = None
    NVD_API_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    # MCP Configuration
    MCP_VERSION: str = "1.0.0"
    MCP_ENDPOINTS: list = ["/vulnerabilities", "/collect", "/health"]
    MCP_AUTH_REQUIRED: bool = True

    # API Versioning
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    CURRENT_API_VERSION: str = "v1"
    SUPPORTED_API_VERSIONS: List[str] = ["v1"]
    API_TITLE: str = "MCP API"
    API_DESCRIPTION: str = "MCP API for vulnerability management and monitoring"
    API_VERSION: str = "1.0.0"
    API_CONTACT: dict = {
        "name": "MCP Support",
        "email": "support@mcp.example.com",
        "url": "https://mcp.example.com/support"
    }
    API_LICENSE: dict = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    API_TERMS_OF_SERVICE: str = "https://mcp.example.com/terms"
    API_DOCS_URL: Optional[str] = "/docs"
    API_REDOC_URL: Optional[str] = "/redoc"
    API_OPENAPI_URL: Optional[str] = "/openapi.json"

    # Cache Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes in seconds
    CACHE_ENABLED: bool = True
    CACHE_EXCLUDED_PATHS: List[str] = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/health",
    ]

    # Task Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1

    # Database Connection Pool
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30

    # Compression
    COMPRESSION_ENABLED: bool = True
    COMPRESSION_MIN_SIZE: int = 1000  # 1KB
    COMPRESSION_LEVEL: int = 6

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 