"""
Async tasks for Financial RAG System.

Provides Celery tasks for background processing.
"""

from app.tasks.celery_app import celery_app
from app.tasks.document_tasks import process_document_async

__all__ = [
    "celery_app",
    "process_document_async",
]
