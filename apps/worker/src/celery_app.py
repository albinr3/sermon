from celery import Celery
from kombu import Queue

from src.config import settings

celery_app = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

default_queue = "default"
celery_app.conf.update(
    task_default_queue=default_queue,
    task_default_exchange=default_queue,
    task_default_routing_key=default_queue,
    task_queues=(
        Queue(default_queue, routing_key=default_queue),
        Queue("transcriptions", routing_key="transcriptions"),
        Queue("suggestions", routing_key="suggestions"),
        Queue("embeddings", routing_key="embeddings"),
        Queue("previews", routing_key="previews"),
        Queue("renders", routing_key="renders"),
    ),
    task_routes={
        "worker.transcribe_sermon": {"queue": "transcriptions", "routing_key": "transcriptions"},
        "worker.suggest_clips": {"queue": "suggestions", "routing_key": "suggestions"},
        "worker.generate_embeddings": {"queue": "embeddings", "routing_key": "embeddings"},
    },
    task_default_priority=settings.celery_default_priority,
    task_inherit_parent_priority=True,
    broker_transport_options={
        "priority_steps": list(range(10)),
        "sep": ":",
        "queue_order_strategy": "priority",
    },
)

celery_app.autodiscover_tasks(["src.tasks"])
