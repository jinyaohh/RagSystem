"""
Celery application configuration.

Configures Celery for async task processing with Redis broker.
"""

import logging
from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Celery App Configuration
# ============================================================================

celery_app = Celery(
    "financial_rag_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.document_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,

    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster"
    },

    # Broker settings
    broker_connection_retry_on_startup=True,
)

# ============================================================================
# Celery Events
# ============================================================================

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Set up periodic tasks (cron-like).

    Currently no periodic tasks, but this is where they would go.
    """
    # Example: Clean up old jobs every day
    # sender.add_periodic_task(
    #     crontab(hour=2, minute=0),
    #     cleanup_old_jobs.s(),
    # )
    pass


logger.info("Celery app configured")
