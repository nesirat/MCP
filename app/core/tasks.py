from celery import Celery
from celery.schedules import crontab
from typing import Any, Callable, Optional
from datetime import timedelta

from app.core.config import settings


# Initialize Celery
celery = Celery(
    "mcp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER
)

# Configure periodic tasks
celery.conf.beat_schedule = {
    "cleanup-old-data": {
        "task": "app.tasks.cleanup.cleanup_old_data",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
    "update-cache": {
        "task": "app.tasks.cache.update_cache",
        "schedule": timedelta(minutes=5),
    },
    "send-notifications": {
        "task": "app.tasks.notifications.send_notifications",
        "schedule": timedelta(minutes=1),
    },
}


class TaskManager:
    def __init__(self, celery_app: Celery):
        self.celery = celery_app

    async def run_task(
        self,
        task_name: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        countdown: Optional[int] = None,
        eta: Optional[Any] = None,
        expires: Optional[int] = None,
        priority: Optional[int] = None,
        queue: Optional[str] = None,
    ) -> str:
        """Run a task asynchronously."""
        task = self.celery.send_task(
            task_name,
            args=args,
            kwargs=kwargs,
            countdown=countdown,
            eta=eta,
            expires=expires,
            priority=priority,
            queue=queue,
        )
        return task.id

    async def get_task_status(self, task_id: str) -> dict:
        """Get the status of a task."""
        task = self.celery.AsyncResult(task_id)
        return {
            "id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None,
            "error": str(task.traceback) if task.failed() else None,
        }

    async def revoke_task(self, task_id: str) -> bool:
        """Revoke a running task."""
        self.celery.control.revoke(task_id, terminate=True)
        return True

    async def get_active_tasks(self) -> list:
        """Get list of active tasks."""
        inspector = self.celery.control.inspect()
        active = inspector.active() or {}
        return [
            {
                "id": task["id"],
                "name": task["name"],
                "args": task["args"],
                "kwargs": task["kwargs"],
                "started": task["time_start"],
            }
            for worker_tasks in active.values()
            for task in worker_tasks
        ]


# Initialize task manager
task_manager = TaskManager(celery)


@celery.task(bind=True)
def process_vulnerability_scan(self, target: str, scan_type: str):
    """Process vulnerability scan in background"""
    # Simulate long-running task
    import time
    time.sleep(5)
    return {
        "target": target,
        "scan_type": scan_type,
        "status": "completed",
        "results": {
            "vulnerabilities": [],
            "warnings": [],
            "info": []
        }
    }


@celery.task(bind=True)
def send_notification(self, user_id: int, message: str, notification_type: str):
    """Send notification in background"""
    # Simulate notification sending
    import time
    time.sleep(2)
    return {
        "user_id": user_id,
        "message": message,
        "notification_type": notification_type,
        "status": "sent"
    }


@celery.task(bind=True)
def generate_report(self, report_type: str, start_date: str, end_date: str):
    """Generate report in background"""
    # Simulate report generation
    import time
    time.sleep(10)
    return {
        "report_type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        "status": "completed",
        "report_url": f"/reports/{report_type}_{start_date}_{end_date}.pdf"
    } 