from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db import SessionLocal
from src.models import Template
from src.routers import clips, sermons
from src.storage import ensure_bucket_exists

app = FastAPI(title="Sermon API")
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(sermons.router, prefix="/sermons", tags=["sermons"])
app.include_router(clips.router, prefix="/clips", tags=["clips"])
