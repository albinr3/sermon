import logging
from time import perf_counter

import redis
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text

from src.config import settings
from src.db import SessionLocal
from src.db import engine
from src.logging_config import setup_logging
from src.models import Template
from src.routers import clips, sermons
from src.storage import ensure_bucket_exists, get_s3_client

setup_logging()
logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default]
    if settings.rate_limit_enabled
    else [],
)

app = FastAPI(title="Sermon API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
if settings.rate_limit_enabled:
    app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    ensure_bucket_exists()
    seed_templates()


def seed_templates() -> None:
    templates = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Bold Center",
            "config_json": {
                "font": "Arial",
                "font_size": 64,
                "y_pos": 1500,
                "max_words_per_line": 4,
                "highlight_mode": "none",
                "safe_margins": {"top": 120, "bottom": 120, "left": 120, "right": 120},
            },
        },
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "name": "Lower Third",
            "config_json": {
                "font": "Arial",
                "font_size": 56,
                "y_pos": 1650,
                "max_words_per_line": 5,
                "highlight_mode": "none",
                "safe_margins": {"top": 120, "bottom": 120, "left": 120, "right": 120},
            },
        },
    ]
    session = SessionLocal()
    try:
        for template in templates:
            if session.get(Template, template["id"]):
                continue
            session.add(
                Template(
                    id=template["id"],
                    name=template["name"],
                    config_json=template["config_json"],
                )
            )
        session.commit()
    finally:
        session.close()


def _format_error(exc: Exception) -> str:
    return str(exc)[:200]


def _check_db() -> dict:
    start = perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "latency_ms": int((perf_counter() - start) * 1000)}
    except Exception as exc:
        logger.warning("Health check: DB unavailable: %s", exc)
        return {
            "ok": False,
            "latency_ms": int((perf_counter() - start) * 1000),
            "error": _format_error(exc),
        }


def _check_redis() -> dict:
    start = perf_counter()
    timeout = max(0.1, float(settings.healthcheck_timeout_sec))
    try:
        client = redis.Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        client.ping()
        return {"ok": True, "latency_ms": int((perf_counter() - start) * 1000)}
    except Exception as exc:
        logger.warning("Health check: Redis unavailable: %s", exc)
        return {
            "ok": False,
            "latency_ms": int((perf_counter() - start) * 1000),
            "error": _format_error(exc),
        }


def _check_minio() -> dict:
    start = perf_counter()
    try:
        client = get_s3_client()
        client.head_bucket(Bucket=settings.s3_bucket)
        return {"ok": True, "latency_ms": int((perf_counter() - start) * 1000)}
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Health check: MinIO unavailable: %s", exc)
        return {
            "ok": False,
            "latency_ms": int((perf_counter() - start) * 1000),
            "error": _format_error(exc),
        }


@app.get("/health")
@limiter.exempt
def health(response: Response) -> dict:
    checks = {
        "db": _check_db(),
        "redis": _check_redis(),
        "minio": _check_minio(),
    }
    ok = all(check["ok"] for check in checks.values())
    response.status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ok else "degraded", "checks": checks}


app.include_router(sermons.router, prefix="/sermons", tags=["sermons"])
app.include_router(clips.router, prefix="/clips", tags=["clips"])
