from celery import Celery

from src.config import settings

celery_app = Celery(
    "api",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
