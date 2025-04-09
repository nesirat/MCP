import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.notification import NotificationConfig, NotificationLog
from app.models.alert import Alert
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    async def send_notification(self, alert: Alert, config: NotificationConfig) -> bool:
        try:
            if not config.enabled:
                return False

            success = False
            error_message = None

            if config.type == "email":
                success = await self._send_email(alert, config.config)
            elif config.type == "webhook":
                success = await self._send_webhook(alert, config.config)
            elif config.type == "slack":
                success = await self._send_slack(alert, config.config)
            elif config.type == "teams":
                success = await self._send_teams(alert, config.config)

            # Log the notification attempt
            self._log_notification(config.id, alert.id, success, error_message)
            return success

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error sending notification: {error_message}")
            self._log_notification(config.id, alert.id, False, error_message)
            return False

    async def _send_email(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM
            msg["To"] = ", ".join(config["recipients"])
            msg["Subject"] = f"Alert: {alert.type} - {alert.level}"

            # Use template if provided, otherwise use default
            template = config.get("template") or self._get_default_email_template()
            body = template.format(
                alert_type=alert.type,
                alert_level=alert.level,
                message=alert.message,
                value=alert.value,
                threshold=alert.threshold,
                created_at=alert.created_at
            )

            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    async def _send_webhook(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            headers = config.get("headers", {})
            data = {
                "alert_id": alert.id,
                "type": alert.type,
                "level": alert.level,
                "message": alert.message,
                "value": alert.value,
                "threshold": alert.threshold,
                "created_at": alert.created_at.isoformat()
            }

            response = requests.request(
                method=config.get("method", "POST"),
                url=config["url"],
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Error sending webhook: {str(e)}")
            return False

    async def _send_slack(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            message = {
                "text": f"*{alert.type.upper()} Alert*\nLevel: {alert.level}\nMessage: {alert.message}",
                "channel": config["channel"]
            }

            if config.get("username"):
                message["username"] = config["username"]
            if config.get("icon_emoji"):
                message["icon_emoji"] = config["icon_emoji"]

            response = requests.post(
                config["webhook_url"],
                json=message,
                timeout=10
            )
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return False

    async def _send_teams(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            message = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "type": "AdaptiveCard",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "size": "Large",
                                    "weight": "Bolder",
                                    "text": f"{alert.type.upper()} Alert"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": f"Level: {alert.level}"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": f"Message: {alert.message}"
                                }
                            ]
                        }
                    }
                ]
            }

            if config.get("title"):
                message["title"] = config["title"]
            if config.get("theme_color"):
                message["themeColor"] = config["theme_color"]

            response = requests.post(
                config["webhook_url"],
                json=message,
                timeout=10
            )
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Error sending Teams message: {str(e)}")
            return False

    def _log_notification(self, config_id: int, alert_id: int, success: bool, error_message: str = None):
        log = NotificationLog(
            notification_config_id=config_id,
            alert_id=alert_id,
            status="success" if success else "failed",
            error_message=error_message
        )
        self.db.add(log)
        self.db.commit()

    def _get_default_email_template(self) -> str:
        return """
        <html>
            <body>
                <h2>Alert Notification</h2>
                <p><strong>Type:</strong> {alert_type}</p>
                <p><strong>Level:</strong> {alert_level}</p>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Value:</strong> {value}</p>
                <p><strong>Threshold:</strong> {threshold}</p>
                <p><strong>Time:</strong> {created_at}</p>
            </body>
        </html>
        """ 