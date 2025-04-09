from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.middleware.versioning import VersionData


def test_get_supported_versions(client: TestClient):
    """Test getting supported API versions."""
    response = client.get(f"{settings.API_V1_STR}/versions")
    assert response.status_code == 200
    versions = response.json()
    assert isinstance(versions, list)
    assert len(versions) > 0
    for version in versions:
        assert "version" in version
        assert "status" in version
        assert "deprecated" in version


def test_get_current_version(client: TestClient):
    """Test getting current API version."""
    response = client.get(f"{settings.API_V1_STR}/current-version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == settings.CURRENT_API_VERSION
    assert data["status"] == "active"
    assert data["docs_url"] == settings.API_DOCS_URL
    assert data["openapi_url"] == settings.API_OPENAPI_URL
    assert data["latest_version"] == max(settings.SUPPORTED_API_VERSIONS)


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == settings.API_VERSION
    assert data["api_version"] == settings.CURRENT_API_VERSION
    assert data["environment"] == settings.ENVIRONMENT
    assert "timestamp" in data


def test_api_info(client: TestClient, auth_headers: dict):
    """Test getting API information."""
    response = client.get(f"{settings.API_V1_STR}/info", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == settings.API_TITLE
    assert data["description"] == settings.API_DESCRIPTION
    assert data["version"] == settings.API_VERSION
    assert data["api_version"] == settings.CURRENT_API_VERSION
    assert data["contact"] == settings.API_CONTACT
    assert data["license"] == settings.API_LICENSE
    assert data["terms_of_service"] == settings.API_TERMS_OF_SERVICE
    assert data["docs_url"] == settings.API_DOCS_URL
    assert data["redoc_url"] == settings.API_REDOC_URL
    assert data["openapi_url"] == settings.API_OPENAPI_URL
    assert data["supported_versions"] == settings.SUPPORTED_API_VERSIONS
    assert data["latest_version"] == max(settings.SUPPORTED_API_VERSIONS)
    assert data["environment"] == settings.ENVIRONMENT
    assert "features" in data


def test_api_info_unauthorized(client: TestClient):
    """Test getting API information without authentication."""
    response = client.get(f"{settings.API_V1_STR}/info")
    assert response.status_code == 401


def test_openapi_schema(client: TestClient):
    """Test OpenAPI schema generation."""
    response = client.get(settings.API_OPENAPI_URL)
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == settings.API_TITLE
    assert schema["info"]["version"] == settings.API_VERSION
    assert schema["info"]["description"] == settings.API_DESCRIPTION
    assert schema["info"]["contact"] == settings.API_CONTACT
    assert schema["info"]["license"] == settings.API_LICENSE
    assert schema["info"]["termsOfService"] == settings.API_TERMS_OF_SERVICE
    assert schema["info"]["x-api-version"] == settings.CURRENT_API_VERSION
    assert schema["info"]["x-supported-versions"] == settings.SUPPORTED_API_VERSIONS
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "BearerAuth" in schema["components"]["securitySchemes"]


def test_changelog(client: TestClient, auth_headers: dict):
    """Test getting API changelog."""
    response = client.get(f"{settings.API_V1_STR}/changelog", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "versions" in data
    assert len(data["versions"]) > 0
    for version in data["versions"]:
        assert "version" in version
        assert "release_date" in version
        assert "changes" in version
        assert isinstance(version["changes"], list)


def test_version_deprecation(client: TestClient):
    """Test version deprecation functionality."""
    # Get the versioning middleware
    versioning_middleware = client.app.state.versioning_middleware
    
    # Deprecate v1 with a sunset date
    sunset_date = datetime.utcnow() + timedelta(days=30)
    versioning_middleware.deprecate_version("v1", sunset_date)
    
    # Check version info
    response = client.get(f"{settings.API_V1_STR}/versions")
    assert response.status_code == 200
    versions = response.json()
    
    v1_info = next(v for v in versions if v["version"] == "v1")
    assert v1_info["deprecated"] is True
    assert "sunset_date" in v1_info
    
    # Make a request to a v1 endpoint
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    assert "Warning" in response.headers
    assert "X-API-Version" in response.headers
    assert "X-API-Deprecated" in response.headers
    assert "Sunset" in response.headers 