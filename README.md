# Sermon Monorepo

Monorepo con:
- apps/web: Next.js (App Router) + Tailwind
- apps/api: FastAPI + SQLAlchemy + Alembic
- apps/worker: Celery + Redis
- Infra: Postgres, Redis, MinIO

## Requisitos
- Docker + Docker Compose
- Node 20 + pnpm

## Variables

```bash
cp .env.example .env
```

## Levantar todo

```bash
docker compose up --build
```

En otra terminal:

```bash
pnpm install
pnpm --filter web dev
```

API: http://localhost:8000
MinIO console: http://localhost:9001

## Endpoints basicos
- GET /health
- POST /jobs
- POST /uploads/presign

## Alembic

```bash
cd apps/api
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Detalle de funcionamiento
Consulta docs/DETALLE.md para ver el flujo completo.

