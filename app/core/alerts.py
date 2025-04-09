from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.api_usage import APIUsage
from app.models.api_key import APIKey
from app.core.config import settings
from app.core.logging import logger

class AlertService:
    def __init__(self, db: Session):
        self.db = db
        self.alert_thresholds = {
            "response_time": {
                "warning": 1.0,  # seconds
                "critical": 2.0  # seconds
            },
            "error_rate": {
                "warning": 0.05,  # 5%
                "critical": 0.10  # 10%
            },
            "usage_spike": {
                "warning": 2.0,  # 2x normal usage
                "critical": 3.0  # 3x normal usage
            }
        }

    async def check_response_time(self, response_time: float, endpoint: str) -> Optional[Dict]:
        """Check if response time exceeds thresholds."""
        if response_time > self.alert_thresholds["response_time"]["critical"]:
            return {
                "level": "critical",
                "type": "response_time",
                "message": f"Critical response time for {endpoint}: {response_time:.2f}s",
                "value": response_time,
                "threshold": self.alert_thresholds["response_time"]["critical"]
            }
        elif response_time > self.alert_thresholds["response_time"]["warning"]:
            return {
                "level": "warning",
                "type": "response_time",
                "message": f"Warning: High response time for {endpoint}: {response_time:.2f}s",
                "value": response_time,
                "threshold": self.alert_thresholds["response_time"]["warning"]
            }
        return None

    async def check_error_rate(self, api_key_id: int) -> Optional[Dict]:
        """Check if error rate exceeds thresholds."""
        # Get error rate for the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        total_requests = self.db.query(func.count(APIUsage.id)).filter(
            APIUsage.api_key_id == api_key_id,
            APIUsage.created_at >= one_hour_ago
        ).scalar()
        
        if total_requests == 0:
            return None
            
        error_requests = self.db.query(func.count(APIUsage.id)).filter(
            APIUsage.api_key_id == api_key_id,
            APIUsage.created_at >= one_hour_ago,
            APIUsage.status_code >= 400
        ).scalar()
        
        error_rate = error_requests / total_requests
        
        if error_rate > self.alert_thresholds["error_rate"]["critical"]:
            return {
                "level": "critical",
                "type": "error_rate",
                "message": f"Critical error rate for API key {api_key_id}: {error_rate:.2%}",
                "value": error_rate,
                "threshold": self.alert_thresholds["error_rate"]["critical"]
            }
        elif error_rate > self.alert_thresholds["error_rate"]["warning"]:
            return {
                "level": "warning",
                "type": "error_rate",
                "message": f"Warning: High error rate for API key {api_key_id}: {error_rate:.2%}",
                "value": error_rate,
                "threshold": self.alert_thresholds["error_rate"]["warning"]
            }
        return None

    async def check_usage_spike(self, api_key_id: int) -> Optional[Dict]:
        """Check if usage has spiked compared to historical average."""
        # Get average usage for the last 7 days (excluding today)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        today = datetime.utcnow().date()
        
        historical_avg = self.db.query(
            func.count(APIUsage.id) / 7.0  # Average per day
        ).filter(
            APIUsage.api_key_id == api_key_id,
            APIUsage.created_at >= seven_days_ago,
            func.date(APIUsage.created_at) < today
        ).scalar() or 0
        
        if historical_avg == 0:
            return None
            
        # Get today's usage
        today_usage = self.db.query(func.count(APIUsage.id)).filter(
            APIUsage.api_key_id == api_key_id,
            func.date(APIUsage.created_at) == today
        ).scalar()
        
        usage_ratio = today_usage / historical_avg if historical_avg > 0 else 0
        
        if usage_ratio > self.alert_thresholds["usage_spike"]["critical"]:
            return {
                "level": "critical",
                "type": "usage_spike",
                "message": f"Critical usage spike for API key {api_key_id}: {usage_ratio:.2f}x normal",
                "value": usage_ratio,
                "threshold": self.alert_thresholds["usage_spike"]["critical"]
            }
        elif usage_ratio > self.alert_thresholds["usage_spike"]["warning"]:
            return {
                "level": "warning",
                "type": "usage_spike",
                "message": f"Warning: Usage spike for API key {api_key_id}: {usage_ratio:.2f}x normal",
                "value": usage_ratio,
                "threshold": self.alert_thresholds["usage_spike"]["warning"]
            }
        return None

    async def check_unauthorized_access(self, api_key_id: int) -> Optional[Dict]:
        """Check for patterns of unauthorized access attempts."""
        # Get failed authentication attempts in the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        failed_auth = self.db.query(func.count(APIUsage.id)).filter(
            APIUsage.api_key_id == api_key_id,
            APIUsage.created_at >= one_hour_ago,
            APIUsage.status_code == 401
        ).scalar()
        
        if failed_auth >= 5:  # More than 5 failed attempts in an hour
            return {
                "level": "critical",
                "type": "unauthorized_access",
                "message": f"Multiple unauthorized access attempts for API key {api_key_id}",
                "value": failed_auth,
                "threshold": 5
            }
        return None

    async def process_alert(self, alert: Dict) -> None:
        """Process and log the alert."""
        if alert["level"] == "critical":
            logger.critical(alert["message"])
            # TODO: Implement critical alert notification (email, Slack, etc.)
        else:
            logger.warning(alert["message"])
            # TODO: Implement warning alert notification

    async def check_all_alerts(self, api_key_id: int, response_time: float, endpoint: str) -> None:
        """Check all alert conditions."""
        alerts = []
        
        # Check response time
        if alert := await self.check_response_time(response_time, endpoint):
            alerts.append(alert)
            
        # Check error rate
        if alert := await self.check_error_rate(api_key_id):
            alerts.append(alert)
            
        # Check usage spike
        if alert := await self.check_usage_spike(api_key_id):
            alerts.append(alert)
            
        # Check unauthorized access
        if alert := await self.check_unauthorized_access(api_key_id):
            alerts.append(alert)
            
        # Process all alerts
        for alert in alerts:
            await self.process_alert(alert) 