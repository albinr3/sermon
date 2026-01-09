# Sermon Monorepo

Monorepo con:
- apps/web: Next.js (App Router) + Tailwind
- apps/api: FastAPI + SQLAlchemy + Alembic
- apps/worker: Celery + Redis
- Infra: Postgres, Redis, MinIO

## Requisitos
- Docker + Docker Compose (solo infra)
- Node 20 + pnpm (web local)
- Python 3.11+ (api y worker locales)
- ffmpeg (requerido para transcripcion y renders del worker; debe estar en PATH)

## Configuracion (.env)
Configura el archivo `.env` en la raiz. Variables clave:
- `DATABASE_URL`, `REDIS_URL`
- `S3_ENDPOINT` (API/worker locales), `S3_INTERNAL_ENDPOINT` (solo Docker), `S3_PUBLIC_ENDPOINT`
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION`, `S3_USE_SSL`
- `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- `NEXT_PUBLIC_API_URL`
- `USE_LLM_FOR_CLIP_SUGGESTIONS` (default `false`)
- `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`
- `NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS` (default `false`, solo UI)
- `CELERY_*` (concurrency por queue, retries y prioridades)

## Levantar infra (Docker)

```bash
docker compose up -d
```

Postgres: localhost:5432
Redis: localhost:6379
MinIO: http://localhost:9000
MinIO console: http://localhost:9001

## Levantar servicios locales (sin Docker)

API (FastAPI):

```bash
cd apps/api
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Worker (Celery):

Nota: requiere ffmpeg instalado y accesible en PATH.

```bash
cd apps/worker
pip install -r requirements.txt
celery -A src.celery_app worker --loglevel=info --queues default,transcriptions,suggestions,embeddings,previews,renders -P solo
```

Web (Next.js, desde la raiz del repo):

```bash
pnpm install
pnpm --filter web dev
```

Landing: http://localhost:3000
App: http://localhost:3000/app
API: http://localhost:8000
Flower: http://localhost:5555 (opcional)

## Endpoints principales
- `GET /health`
- `POST /sermons`
- `GET /sermons`
- `GET /sermons/{id}`
- `POST /sermons/{id}/upload-complete`
- `POST /sermons/{id}/suggest` (query opcional `use_llm=true|false`)
- `GET /sermons/{id}/suggestions`
- `POST /sermons/{id}/embed`
- `GET /sermons/{id}/search?q=...&k=...`
- `GET /sermons/{id}/segments`
- `POST /clips`
- `GET /clips`
- `GET /clips/{id}`
- `POST /clips/{id}/render?type=preview|final`

## LLM para sugerencias (Deepseek)
- El worker reordena candidatos con Deepseek cuando `use_llm` es true.
- Si falta config o hay error, cae a heuristica sin romper el flujo.
- Las sugerencias guardan `use_llm` para mostrar un badge IA en la UI.

## Alembic

```bash
cd apps/api
alembic upgrade head
```
En el enfoque hibrido, corre este comando antes de levantar la API.

## Detalle de funcionamiento
Consulta docs/DETALLE.md para ver el flujo completo.

