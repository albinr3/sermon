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
- `S3_ENDPOINT` (API/worker locales), `S3_INTERNAL_ENDPOINT` (solo Docker), `S3_PUBLIC_ENDPOINT` (para AssemblyAI con ngrok)
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION`, `S3_USE_SSL`
- `ASSEMBLYAI_API` (API key de AssemblyAI)
- `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB` (default `2048`)
- `NEXT_PUBLIC_POLL_INTERVAL_MS` (default `5000`)
- `USE_LLM_FOR_CLIP_SUGGESTIONS` (default `false`)
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` (requerido para sugerencias IA, ej: `OPENAI_BASE_URL=https://api.openai.com/v1`, `OPENAI_MODEL=gpt-5-mini`)
- `NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS` (default `false`, solo UI)
- `CELERY_*` (concurrency por queue, retries y prioridades)

### AssemblyAI (desarrollo local)

AssemblyAI funciona con archivos locales, no requiere configuración adicional. Solo necesitas:

1. Agregar en `.env`:
   ```
   ASSEMBLYAI_API=tu_api_key_de_assemblyai
   ```
2. Reiniciar el worker de Celery

El sistema descarga el archivo desde MinIO localmente y lo envía directamente a AssemblyAI, sin necesidad de URLs públicas.

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

celery -A src.celery_app worker --loglevel=info --queues default,transcriptions,suggestions,embeddings,previews,renders -P threads --concurrency=4
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
- `POST /sermons/{id}/suggest` - Genera sugerencias de clips (query params: `use_llm`, `full_context_prompt_version`)
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

## LLM para sugerencias
El sistema usa **Full-context** con **OpenAI** para generar sugerencias de clips con IA:

### Método: Full-context
- El LLM analiza **toda la transcripción en una sola llamada**
- **Máxima comprensión contextual**, mejores decisiones holísticas
- Ideal para sermones complejos con temas interrelacionados
- Genera clips con coherencia temática superior
- **Más costoso** en tokens (~60K tokens, ~$0.012 por sermon) pero mejor calidad

### Proveedor: OpenAI
- Usa **OpenAI** (GPT-5 mini) como proveedor exclusivo
- Configuración requerida: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`

### Versiones de prompt
- **v1**: Clips de 30-120 segundos (default)
- **v2**: Clips de 30-50 segundos, optimizado para TikTok/Reels/Shorts

### Características
- Tracking de uso de tokens: prompt, completion, cache hits/misses
- Estimación de costos por sugerencia
- Estadísticas disponibles en `/sermons/{id}/token-stats`
- Fallback automático a heurísticas si falla LLM
- Dedupe por solapamiento (>60%) y semántico (si hay embeddings)
- Las sugerencias muestran badge "IA" en la UI
- La UI permite seleccionar versión de prompt (v1/v2) cuando se activa IA

## Actualizaciones recientes
- **Método único LLM**: Full-context con OpenAI (simplificación de UI)
- **Tracking de tokens**: uso, cache, costos estimados
- **Versiones de prompt**: v1 (30-120s) y v2 (30-50s optimizado para redes sociales)
- **Retry de transcripción**: reintentar transcripciones fallidas
- **Estadísticas detalladas**: tokens y costos por sugerencia
- **Sugerencias mejoradas**: dedupe semántico, clasificación por tipo de segmento
- **Acciones sobre sugerencias**: aceptar, feedback, aplicar trim sugerido
- **Soft delete en cascada**: eliminar sermon borra clips, segmentos y embeddings
- **Templates**: plantillas de estilo para clips (fuentes, colores, posición)

## Alembic

### Aplicar migraciones

```bash
cd apps/api
alembic upgrade head
```
En el enfoque hibrido, corre este comando antes de levantar la API.

### Resetear base de datos completamente

Para borrar **toda** la base de datos (tablas, tipos ENUM, historial de Alembic) y empezar desde cero:

**Opción 1: Script Python (recomendado)**

```bash
cd apps/api
python reset_db.py
alembic upgrade head
```


Luego ejecutar las migraciones:

```bash
cd apps/api
alembic upgrade head
```

## Detalle de funcionamiento
Consulta docs/DETALLE.md para ver el flujo completo.

