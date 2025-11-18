"""
Celery Application Configuration

Provides async task queue for long-running operations like:
- Project execution
- Task execution by agents
- Periodic analytics and cleanup
- Email notifications
"""

import logging
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange

from app.config import settings

logger = logging.getLogger(__name__)


# Initialize Celery app
celery_app = Celery(
    "ai_agency",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.project_tasks",
        "app.tasks.agent_tasks",
        "app.tasks.analytics_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task result settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={"master_name": "mymaster"},

    # Task routing
    task_routes={
        "app.tasks.project_tasks.*": {"queue": "projects"},
        "app.tasks.agent_tasks.*": {"queue": "agents"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
    },

    # Task execution settings
    task_acks_late=True,  # Task acknowledged after completion
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    task_track_started=True,  # Track when task starts

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    worker_disable_rate_limits=False,

    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Beat schedule for periodic tasks
    beat_schedule={
        # Cleanup old executions daily at 3 AM
        "cleanup-old-executions": {
            "task": "app.tasks.analytics_tasks.cleanup_old_executions",
            "schedule": crontab(hour=3, minute=0),
        },

        # Update agent performance metrics hourly
        "update-agent-metrics": {
            "task": "app.tasks.analytics_tasks.update_agent_metrics",
            "schedule": crontab(minute=0),  # Every hour
        },

        # Check stalled projects every 15 minutes
        "check-stalled-projects": {
            "task": "app.tasks.project_tasks.check_stalled_projects",
            "schedule": crontab(minute="*/15"),
        },
    },
)

# Define queues
celery_app.conf.task_queues = (
    Queue("projects", Exchange("projects"), routing_key="projects"),
    Queue("agents", Exchange("agents"), routing_key="agents"),
    Queue("analytics", Exchange("analytics"), routing_key="analytics"),
    Queue("default", Exchange("default"), routing_key="default"),
)

# Default queue
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok", "message": "Celery is working!"}


# Celery signals for logging
@celery_app.task(bind=True)
def test_celery():
    """Test task to verify Celery is working."""
    return {"status": "success", "message": "Celery is configured correctly!"}


# Configure Celery logging
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks after Celery configuration."""
    logger.info("Periodic tasks configured")


logger.info("Celery app initialized")
