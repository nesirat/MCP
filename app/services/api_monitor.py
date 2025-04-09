from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from app.models.api import API
from app.models.alert import Alert
from app.services.analytics import AnalyticsService
from app.services.notification import NotificationService


class APIMonitorService:
    def __init__(self, db: Session):
        self.db = db
        self.analytics_service = AnalyticsService(db)
        self.notification_service = NotificationService(db)

    async def check_api(self, api: API) -> None:
        """Check the status of an API endpoint."""
        start_time = datetime.utcnow()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=api.method,
                    url=api.url,
                    headers=api.headers,
                    json=api.body,
                    timeout=api.timeout,
                )
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Record analytics
                self.analytics_service.record_api_call(
                    api_id=api.id,
                    response_time=response_time,
                    status_code=response.status_code,
                    success=response.status_code < 400,
                    error_count=1 if response.status_code >= 400 else 0,
                )
                
                # Check if response time exceeds threshold
                if response_time > api.response_time_threshold:
                    self._create_alert(
                        api,
                        "Response time exceeded threshold",
                        f"Response time: {response_time}s, Threshold: {api.response_time_threshold}s",
                    )
                
                # Check if status code is in error codes
                if response.status_code in api.error_codes:
                    self._create_alert(
                        api,
                        "Error status code detected",
                        f"Status code: {response.status_code}",
                    )
                
                # Check response body if validation is enabled
                if api.response_validation:
                    if not self._validate_response(response.json(), api.expected_response):
                        self._create_alert(
                            api,
                            "Response validation failed",
                            "Response body did not match expected format",
                        )
        
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Record analytics for failed request
            self.analytics_service.record_api_call(
                api_id=api.id,
                response_time=response_time,
                status_code=0,
                success=False,
                error_count=1,
            )
            
            self._create_alert(api, "API check failed", str(e))

    def _create_alert(self, api: API, title: str, message: str) -> None:
        """Create an alert and send notifications."""
        alert = Alert(
            api_id=api.id,
            title=title,
            message=message,
            severity="high",
        )
        self.db.add(alert)
        self.db.commit()
        
        # Send notifications
        self.notification_service.send_notification(alert)

    def _validate_response(self, response: dict, expected: dict) -> bool:
        """Validate the response body against the expected format."""
        # Simple validation - can be enhanced based on requirements
        for key, value in expected.items():
            if key not in response:
                return False
            if isinstance(value, dict):
                if not isinstance(response[key], dict):
                    return False
                if not self._validate_response(response[key], value):
                    return False
            elif isinstance(value, list):
                if not isinstance(response[key], list):
                    return False
                if value and not all(isinstance(item, type(value[0])) for item in response[key]):
                    return False
            elif not isinstance(response[key], type(value)):
                return False
        return True 