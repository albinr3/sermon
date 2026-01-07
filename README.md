# Sermon Monorepo

Monorepo con:
- apps/web: Next.js (App Router) + Tailwind
- apps/api: FastAPI + SQLAlchemy + Alembic
- apps/worker: Celery + Redis
- Infra: Postgres, Redis, MinIO

## Requisitos
- Docker + Docker Compose
- Node 20 + pnpm (solo si corres la web fuera de Docker)

## Configuracion (.env)
Configura el archivo `.env` en la raiz. Variables clave:
- `DATABASE_URL`, `REDIS_URL`
- `S3_ENDPOINT`, `S3_PUBLIC_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION`, `S3_USE_SSL`
- `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- `NEXT_PUBLIC_API_URL`
- `USE_LLM_FOR_CLIP_SUGGESTIONS` (default `false`)
- `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`
- `NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS` (default `false`, solo UI)

## Levantar todo (Docker)

```bash
docker compose up --build
```

UI: http://localhost:3000
API: http://localhost:8000
MinIO console: http://localhost:9001

Si corres la web fuera de Docker:

```bash
pnpm install
pnpm --filter web dev
```

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

## Detalle de funcionamiento
Consulta docs/DETALLE.md para ver el flujo completo.

