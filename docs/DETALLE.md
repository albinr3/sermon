# Detalle de funcionamiento

## Resumen
La web permite subir sermones en video, transcribirlos automaticamente, generar sugerencias de clips (heuristica o IA opcional), crear clips verticales con subtitulos y buscar segmentos por significado. Los archivos se almacenan en MinIO y la base de datos guarda el estado, progreso y segmentos de transcripcion para monitorear el avance y construir clips descargables.

Este documento describe como funciona la web de Sermon de punta a punta: flujo de subida, transcripcion, clips y servicios involucrados.

## Arquitectura
- Web: Next.js (App Router) + Tailwind en `apps/web`
- API: FastAPI + SQLAlchemy en `apps/api`
- Worker: Celery en `apps/worker`
- Infra: Postgres, Redis, MinIO (S3 compatible)

Servicios principales (enfoque hibrido, Docker solo para infra):
- Web local en http://localhost:3000
- API local en http://localhost:8000
- Worker local ejecutando colas de Celery
- `minio` en Docker expone S3 en http://localhost:9000 y consola en http://localhost:9001
- `postgres` en Docker en 5432
- `redis` en Docker en 6379

## Flujo de subida de sermon
1) La UI crea un sermon con `POST /sermons` enviando el nombre del archivo.
2) La API crea el registro en base de datos y genera una URL firmada (presigned PUT) a MinIO (expira en 3600s / 1h).
3) El navegador sube el archivo directamente a MinIO usando esa URL.
4) La UI confirma el fin de subida con `POST /sermons/{id}/upload-complete`.
5) La API marca el sermon en estado `uploaded` y encola la transcripcion en Celery.

## Transcripcion (worker)
El worker ejecuta la tarea `worker.transcribe_sermon`:
- Descarga el video desde MinIO.
- Convierte a WAV mono 16 kHz con ffmpeg.
- Transcribe con `faster-whisper` (modelo `small`, CPU, `int8`).
- Inserta segmentos en `transcript_segments`.
- Actualiza `progress` (5% inicial, 5-95% durante la transcripcion, 100% al finalizar).
- Cambia el estado a `transcribed`.
- Si falla, guarda `error_message` y estado `error`.

## Segmentos de transcripcion
Los segmentos guardan:
- `start_ms`, `end_ms`, `text`, `sermon_id`

La UI los muestra para seleccionar rangos de clip.

## Notas de base de datos
- Soft delete: las tablas principales guardan `deleted_at` y las consultas filtran solo registros activos.
- Auditoria: se registra `created_at`, `updated_at` y `deleted_at` en entidades clave.
- Particionado: si `transcript_segments` crece mucho, considerar particionar por `sermon_id` o rango de fechas para mantener queries y indices livianos.

## Sugerencias de clips (worker)
Flujo de sugerencias con 4 métodos LLM:

### Métodos disponibles

#### 1. Scoring (default)
1) La UI llama `POST /sermons/{id}/suggest?use_llm=true&llm_method=scoring&llm_provider=deepseek|openai`.
2) La API encola `worker.suggest_clips(sermon_id, use_llm=True, llm_method="scoring", llm_provider="deepseek")`.
3) **Heurística**: combina segmentos para clips de 30s a 120s, prioriza:
   - Inicios y finales limpios (silencios/puntuación)
   - Hooks avanzados (preguntas, imperativos, estadísticas)
   - Duración óptima y variedad
   - Clasificación semántica por tipo (story, teaching, call-to-action, etc.)
4) **LLM Re-scoring**: el proveedor seleccionado (Deepseek o OpenAI) evalúa cada candidato y asigna scores.
5) **Score final**: 0.3 heurística + 0.7 LLM.
6) **Dedupe**: solapamiento (>60%) y semántico (si hay embeddings).
7) Se guardan en `clips` con `source=auto`, `score`, `rationale`, `use_llm`, `llm_method`, `llm_provider`.

#### 2. Selection
1) Similar a scoring pero el LLM **selecciona** los mejores clips en lugar de solo scorear.
2) Usa **ventanas deslizantes** para analizar contexto limitado (3000 palabras por ventana).
3) Puede sugerir **recortes** (`trim_suggestion`): start_offset_sec, end_offset_sec.
4) **Backfill**: si el LLM no genera suficientes clips, completa con heurísticas.
5) Balance entre calidad y costo de tokens.

#### 3. Generation
1) El LLM **genera clips desde cero** usando la transcripción completa.
2) **No depende de heurísticas**, máxima libertad creativa.
3) Puede crear clips más originales basados en comprensión profunda del contenido.
4) Usa más tokens que selection debido a análisis completo.
5) También puede sugerir recortes y proporciona rationale detallado.

#### 4. Full-context
1) El LLM analiza **toda la transcripción en una sola llamada**.
2) **Máxima comprensión contextual**, mejores decisiones holísticas.
3) Ideal para sermones complejos con temas interrelacionados.
4) **Más costoso** en tokens pero mejor calidad.
5) Genera clips con coherencia temática superior.

### Características comunes
- **Fallback automático**: si el LLM falla o no está configurado, usa heurísticas.
- **Tracking de tokens**: prompt_tokens, completion_tokens, total_tokens, cache_hit_tokens, cache_miss_tokens.
- **Estimación de costos**: calcula costo en USD por método.
- **Dedupe inteligente**: por solapamiento (>60%) y semántico (embeddings).
- **Clasificación semántica**: story, teaching, call-to-action, testimony, prayer.
- **Logs detallados**: IA log con prompts, respuestas y métricas.
- **Estadísticas comparativas**: endpoint `/sermons/{id}/token-stats` compara métodos.

## Clips (worker)
Flujo para crear un clip:
1) La UI envia `POST /clips` con `sermon_id`, `start_ms`, `end_ms`.
2) La API valida la duracion (10s a 120s) y encola `worker.render_clip`.
3) El worker:
   - Descarga el video original.
   - Construye un archivo SRT con los segmentos del rango.
   - Renderiza con ffmpeg (preview 540x960 o final 1080x1920) y subtitulos.
   - Sube el MP4 generado a MinIO.
   - Guarda `output_url` y marca `status = done`.
4) La API expone `download_url` (presigned GET, expira en 3600s / 1h) para descargar desde la UI.

## Busqueda semantica (embeddings)
- La UI puede llamar `POST /sermons/{id}/embed` para generar embeddings.
- El worker ejecuta `worker.generate_embeddings` con SentenceTransformers (modelo `paraphrase-multilingual-MiniLM-L12-v2`, 384 dims) y guarda en `transcript_embeddings`.
- `GET /sermons/{id}/search?q=...&k=...` busca segmentos por similitud (pgvector).
- Si no hay embeddings, la UI dispara el job y muestra un estado de "generando".

## Estados y progreso
Sermon (`SermonStatus`):
- `pending` -> `uploaded` -> `processing` -> `transcribed`
- `suggested` cuando se generan sugerencias
- `embedded` cuando se generan embeddings
- `error` si falla la tarea

Clip (`ClipStatus`):
- `pending` -> `processing` -> `done`
- `error` si falla la tarea

Clip (`ClipSource`):
- `manual` (creado por el usuario)
- `auto` (sugerencias)
- `use_llm` indica si el clip sugerido fue re-scoreado por IA

## API principal

### Endpoints de Sermons
- `GET /health` - Health check completo (DB, Redis, MinIO)
- `POST /sermons` - Crea sermon y retorna presigned PUT URL
- `GET /sermons` - Lista sermones con filtros:
  - `status`: filtrar por SermonStatus
  - `q`: búsqueda en título, descripción, predicador, serie
  - `tag`: filtrar por tag específico
  - `limit`, `offset`: paginación
- `GET /sermons/{id}` - Detalle de sermon con presigned GET URL
- `PATCH /sermons/{id}` - Actualiza metadatos (título, descripción, tags, etc.)
- `DELETE /sermons/{id}` - Soft delete en cascada:
  - Marca sermon como eliminado
  - Elimina clips asociados
  - Elimina segmentos de transcripción
  - Elimina embeddings
  - Elimina feedback de clips
- `POST /sermons/{id}/upload-complete` - Completa subida y encola transcripción
- `POST /sermons/{id}/retry-transcription` - Reintenta transcripción fallida:
  - Elimina segmentos y embeddings previos
  - Resetea status y progress
  - Re-encola transcripción
- `GET /sermons/{id}/segments` - Lista segmentos con paginación
- `GET /sermons/{id}/transcript-stats` - Estadísticas:
  - `word_count`: total de palabras
  - `char_count`: total de caracteres
- `POST /sermons/{id}/suggest` - Genera sugerencias con params:
  - `use_llm`: true/false (default: config)
  - `llm_method`: scoring|selection|generation|full-context
  - `llm_provider`: deepseek|openai
- `GET /sermons/{id}/suggestions` - Lista clips sugeridos ordenados por score
- `DELETE /sermons/{id}/suggestions` - Elimina todas las sugerencias y su feedback
- `GET /sermons/{id}/token-stats` - Estadísticas de uso LLM:
  - Por método: clips, tokens (prompt/completion/total), costos, cache
  - Comparaciones entre métodos (delta de tokens/costos, % incremento)
- `POST /sermons/{id}/embed` - Encola generación de embeddings
- `GET /sermons/{id}/search` - Búsqueda semántica:
  - `q`: query de búsqueda
  - `k`: número de resultados (default 10, max 50)
  - Usa pgvector para similitud L2

### Endpoints de Clips
- `POST /clips` - Crea clip manual con validación de duración (10s-120s)
- `GET /clips` - Lista todos los clips (incluye presigned URLs)
- `GET /clips/{id}` - Detalle de clip con presigned GET URL
- `PATCH /clips/{id}` - Actualiza clip (timestamps, template, etc.)
- `DELETE /clips/{id}` - Soft delete del clip y su feedback
- `POST /clips/{id}/accept` - Acepta sugerencia:
  - Crea clip manual con mismos parámetros
  - Registra feedback positivo
  - Retorna nuevo clip creado
- `POST /clips/{id}/feedback` - Registra feedback (accepted: true/false)
- `POST /clips/{id}/apply-trim` - Aplica recorte sugerido por LLM:
  - Lee `llm_trim` (start_offset_sec, end_offset_sec)
  - Ajusta timestamps a límites de segmentos
  - Valida duración resultante
  - Marca `trim_applied = true`
- `POST /clips/{id}/render?type=preview|final` - Renderiza clip:
  - `preview`: 540x960, queue "previews", alta prioridad
  - `final`: 1080x1920, queue "renders", prioridad normal
  - Retorna status "queued"

## Almacenamiento (MinIO)
- Bucket: `sermon`
- Objetos de video original: `sermons/{sermon_id}/{uuid}-{filename}`
- Clips renderizados: `clips/{clip_id}/{uuid}.mp4`
- La API genera URLs firmadas para subir y descargar (expiran en 3600s / 1h).

## Templates de estilo para clips
El sistema soporta templates personalizables para el estilo visual de clips:

### Estructura de Template
```json
{
  "font_family": "Arial",
  "font_size": 48,
  "font_color": "#FFFFFF",
  "bg_color": "#000000",
  "outline_width": 2,
  "outline_color": "#000000",
  "position": "bottom",
  "margin": 40
}
```

### Características
- **Seed automático**: en startup, la API crea templates por defecto si no existen
- **Templates disponibles**:
  - `default`: texto blanco con outline negro, bottom
  - `bold`: texto amarillo con outline negro, bottom
  - `minimal`: texto blanco sin outline, bottom
  - `top`: texto blanco con outline, top
- **Configuración por clip**: cada clip puede referenciar un `template_id`
- **Fallback**: si no se especifica template, usa valores default hardcoded
- **Soft delete**: templates soportan eliminación suave

### Posiciones disponibles
- `bottom`: subtítulos en parte inferior (más común)
- `center`: subtítulos centrados verticalmente
- `top`: subtítulos en parte superior

## Mejoras técnicas recientes

### Sistema de dedupe inteligente
- **Dedupe por solapamiento**: elimina candidatos que se solapan >60%
- **Dedupe semántico**: si hay embeddings, elimina clips con contenido similar usando similitud coseno
- **Clasificación de segmentos**: identifica automáticamente tipos (story, teaching, call-to-action, testimony, prayer)
- **Puntuación por tipo**: prioriza testimonios y llamados a la acción

### Heurísticas avanzadas
- **Detección de hooks**: identifica preguntas, imperativos, estadísticas al inicio
- **Análisis de gaps**: evalúa silencios entre segmentos para cortes limpios
- **Normalización de texto**: limpia puntuación y espacios para análisis consistente
- **Scoring multi-factor**: considera duración, variedad, limpieza, hooks y tipo de segmento

### LLM con caché y optimización
- **Prompt caching**: los proveedores cachean contexto común para reducir costos
- **Token tracking granular**: 
  - `llm_prompt_tokens`: tokens del prompt
  - `llm_completion_tokens` / `llm_output_tokens`: tokens de respuesta
  - `llm_cache_hit_tokens`: tokens que fueron recuperados de caché
  - `llm_cache_miss_tokens`: tokens que no estaban en caché
  - `llm_total_tokens`: suma total
  - `llm_estimated_cost`: costo estimado en USD
- **Logs estructurados**: archivo `logIA` captura prompts, respuestas y métricas para análisis
- **Gestión de errores**: retry con backoff exponencial, fallback a heurísticas

### Arquitectura de colas Celery
- **Colas especializadas**:
  - `transcriptions`: transcripción de audio (CPU intensivo)
  - `suggestions`: generación de sugerencias con/sin LLM
  - `embeddings`: cálculo de embeddings semánticos
  - `previews`: renders rápidos de preview (540p)
  - `renders`: renders finales de alta calidad (1080p)
  - `default`: tareas misceláneas
- **Prioridades configurables**: cada tipo de tarea tiene prioridad ajustable (0-9)
- **Concurrencia por cola**: workers dedicados por tipo de carga
- **Retry automático**: hasta 3 reintentos con backoff exponencial

### Base de datos
- **Soft delete universal**: todas las entidades principales soportan eliminación suave
- **Delete en cascada**: eliminar sermon borra automáticamente clips, segmentos, embeddings y feedback
- **Auditoría completa**: `created_at`, `updated_at`, `deleted_at` en todas las tablas
- **Índices optimizados**: índices en claves foráneas, timestamps y campos de búsqueda
- **Pgvector**: extensión para búsqueda semántica con similitud L2
- **Migraciones Alembic**: versionado de schema con 16 migraciones

## Configuracion (.env)
Variables clave:

### Base de datos y almacenamiento
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `S3_ENDPOINT`: endpoint S3 para API/worker (ej: http://localhost:9000)
- `S3_INTERNAL_ENDPOINT`: endpoint interno Docker (ej: http://minio:9000)
- `S3_PUBLIC_ENDPOINT`: endpoint público para navegador (ej: http://localhost:9000)
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`: credenciales MinIO
- `S3_BUCKET`: nombre del bucket (default: sermon)
- `S3_REGION`: región S3 (default: us-east-1)
- `S3_USE_SSL`: usar HTTPS (default: false)

### LLM y IA
- `USE_LLM_FOR_CLIP_SUGGESTIONS`: habilitar LLM por default (default: false)
- `DEEPSEEK_API_KEY`: API key de Deepseek
- `DEEPSEEK_MODEL`: modelo de Deepseek (ej: deepseek-chat)
- `DEEPSEEK_BASE_URL`: endpoint de Deepseek
- `OPENAI_API_KEY`: API key de OpenAI
- `OPENAI_MODEL`: modelo de OpenAI (ej: gpt-5-mini)
- `OPENAI_BASE_URL`: endpoint de OpenAI (ej: https://api.openai.com/v1)

### Frontend (Next.js)
- `NEXT_PUBLIC_API_URL`: URL de la API (ej: http://localhost:8000)
- `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB`: tamaño máximo de archivo (default: 2048)
- `NEXT_PUBLIC_POLL_INTERVAL_MS`: intervalo de polling (default: 5000)
- `NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS`: checkbox LLM por default en UI (default: false)

### Celery (Worker)
- `CELERY_CONCURRENCY_TRANSCRIPTIONS`: workers para transcripciones (default: 1)
- `CELERY_CONCURRENCY_SUGGESTIONS`: workers para sugerencias (default: 1)
- `CELERY_CONCURRENCY_EMBEDDINGS`: workers para embeddings (default: 1)
- `CELERY_CONCURRENCY_PREVIEWS`: workers para previews (default: 2)
- `CELERY_CONCURRENCY_RENDERS`: workers para renders finales (default: 1)
- `CELERY_MAX_RETRIES`: reintentos máximos por tarea (default: 3)
- `CELERY_PRIORITY_*`: prioridades por tipo de tarea (0-9, default: 5)

## Notas de UX
- **Polling**: la web hace polling cada 5s cuando un sermon o clip está en estado activo (configurable con `NEXT_PUBLIC_POLL_INTERVAL_MS`).
- **Progreso**: se muestra en dashboard y vista de detalle con barra de progreso (0-100%).
- **Sugerencias IA**: 
  - Checkbox "Usar IA para sugerir clips"
  - Selector de método: Scoring, Selection, Generation, Full-context
  - Selector de proveedor: Deepseek, OpenAI
  - Badge "IA" en sugerencias generadas con LLM
  - Muestra método usado (ej: "Full-context")
- **Estados visuales**:
  - "Subiendo..." durante upload
  - "Transcribiendo..." con % de progreso
  - "Generando sugerencias..." al crear sugerencias
  - "Renderizando..." durante render de clips
- **Acciones sobre sugerencias**:
  - Botón "Aceptar" crea clip manual
  - Botón "Aplicar recorte" usa trim_suggestion del LLM
  - Preview automático al hacer clic
  - Feedback positivo/negativo
- **Validaciones**:
  - Tamaño máximo de archivo: `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB`
  - Duración de clip: 10s a 120s
  - URLs firmadas expiran en 1 hora
- **Filtros y búsqueda**:
  - Buscar sermones por título, predicador, serie
  - Filtrar por status y tags
  - Búsqueda semántica en transcripciones
- **Estadísticas**:
  - Ver uso de tokens por método
  - Comparar costos entre métodos
  - Estadísticas de transcripción (palabras, caracteres)
