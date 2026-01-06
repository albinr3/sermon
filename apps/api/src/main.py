from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db import create_db_and_tables
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
    create_db_and_tables()
    ensure_bucket_exists()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(sermons.router, prefix="/sermons", tags=["sermons"])
app.include_router(clips.router, prefix="/clips", tags=["clips"])
