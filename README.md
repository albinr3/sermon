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
- `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB` (default `2048`)
- `NEXT_PUBLIC_POLL_INTERVAL_MS` (default `5000`)
- `USE_LLM_FOR_CLIP_SUGGESTIONS` (default `false`)
- `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` (ej: `OPENAI_BASE_URL=https://api.openai.com/v1`, `OPENAI_MODEL=gpt-5-mini`)
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

### Sermons
- `GET /health` - Verifica salud del sistema (DB, Redis, MinIO)
- `POST /sermons` - Crea un sermon y retorna URL de carga
- `GET /sermons` - Lista sermones con filtros (status, tag, búsqueda)
- `GET /sermons/{id}` - Obtiene detalle de un sermon
- `PATCH /sermons/{id}` - Actualiza metadatos de un sermon
- `DELETE /sermons/{id}` - Soft delete de un sermon (y clips/segmentos asociados)
- `POST /sermons/{id}/upload-complete` - Marca subida completa y encola transcripción
- `POST /sermons/{id}/retry-transcription` - Reintenta transcripción fallida
- `GET /sermons/{id}/segments` - Lista segmentos de transcripción
- `GET /sermons/{id}/transcript-stats` - Estadísticas de transcripción (palabras, caracteres)
- `POST /sermons/{id}/suggest` - Genera sugerencias de clips (query params: `use_llm`, `llm_method`, `llm_provider`)
- `GET /sermons/{id}/suggestions` - Lista clips sugeridos con scores
- `DELETE /sermons/{id}/suggestions` - Elimina todas las sugerencias de un sermon
- `GET /sermons/{id}/token-stats` - Estadísticas de uso de tokens LLM por método
- `POST /sermons/{id}/embed` - Genera embeddings semánticos
- `GET /sermons/{id}/search?q=...&k=...` - Búsqueda semántica en transcripción

### Clips
- `POST /clips` - Crea un clip manual
- `GET /clips` - Lista todos los clips (manuales y sugerencias)
- `GET /clips/{id}` - Obtiene detalle de un clip
- `PATCH /clips/{id}` - Actualiza un clip
- `DELETE /clips/{id}` - Soft delete de un clip
- `POST /clips/{id}/accept` - Acepta una sugerencia y crea clip manual
- `POST /clips/{id}/feedback` - Envía feedback sobre una sugerencia
- `POST /clips/{id}/apply-trim` - Aplica recorte sugerido por LLM
- `POST /clips/{id}/render?type=preview|final` - Renderiza un clip (preview 540p o final 1080p)

## Notas
- Las URLs firmadas (presigned PUT/GET) de MinIO expiran a los 3600s (1h).
- La UI valida el tamano maximo de archivo con `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB`.

## LLM para sugerencias (4 métodos disponibles)
El sistema ofrece múltiples métodos para generar sugerencias de clips con IA:

### 1. **Scoring** (default)
- Genera candidatos con heurísticas y los re-scorea con LLM
- Combina score heurístico (0.3) + score LLM (0.7)
- Más eficiente en tokens, ideal para refinamiento rápido

### 2. **Selection**
- El LLM selecciona los mejores clips desde candidatos heurísticos
- Usa ventanas deslizantes para analizar contexto limitado
- Puede sugerir recortes (`trim_suggestion`)
- Balance entre calidad y costo

### 3. **Generation**
- El LLM genera clips desde cero usando la transcripción completa
- No depende de heurísticas, máxima libertad creativa
- Puede crear clips más originales pero usa más tokens

### 4. **Full-context**
- El LLM analiza la transcripción completa en una sola llamada
- Máxima comprensión contextual, mejores decisiones
- Más costoso en tokens pero mejor calidad
- Ideal para sermones complejos o cuando la calidad es prioritaria

### Características comunes
- Soporta **Deepseek** y **OpenAI** (GPT-5 mini) como proveedores
- Tracking de uso de tokens: prompt, completion, cache hits/misses
- Estimación de costos por método
- Estadísticas comparativas disponibles en `/sermons/{id}/token-stats`
- Fallback automático a heurísticas si falla LLM
- Dedupe por solapamiento (>60%) y semántico (si hay embeddings)
- Las sugerencias muestran badge "IA" en la UI

## Actualizaciones recientes
- **4 métodos LLM**: scoring, selection, generation, full-context
- **Tracking de tokens**: uso, cache, costos estimados por método
- **Retry de transcripción**: reintentar transcripciones fallidas
- **Estadísticas detalladas**: tokens, costos y comparativas entre métodos
- **Sugerencias mejoradas**: dedupe semántico, clasificación por tipo de segmento
- **Acciones sobre sugerencias**: aceptar, feedback, aplicar trim sugerido
- **Soft delete en cascada**: eliminar sermon borra clips, segmentos y embeddings
- **Templates**: plantillas de estilo para clips (fuentes, colores, posición)

## Alembic

```bash
cd apps/api
alembic upgrade head
```
En el enfoque hibrido, corre este comando antes de levantar la API.

## Detalle de funcionamiento
Consulta docs/DETALLE.md para ver el flujo completo.

