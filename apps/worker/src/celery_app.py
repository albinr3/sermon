from celery import Celery

from src.config import settings

celery_app = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["src.tasks"])
