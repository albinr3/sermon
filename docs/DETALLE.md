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
2) La API crea el registro en base de datos y genera una URL firmada (presigned PUT) a MinIO.
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

## Sugerencias de clips (worker)
Flujo de sugerencias:
1) La UI llama `POST /sermons/{id}/suggest?use_llm=true|false`.
2) La API encola `worker.suggest_clips(sermon_id, use_llm)`.
3) Heuristica: combina segmentos para clips de 30s a 120s, prioriza inicios y finales limpios (silencios/puntuacion) y descarta texto vacio.
4) Si `use_llm` es true y Deepseek esta configurado, re-scorea candidatos y puede sugerir recortes (`trim_suggestion`). Score final: 0.3 heuristica + 0.7 LLM.
5) Si Deepseek falla o no esta configurado, se hace fallback a heuristica.
6) Se deduplica por solapamiento (>60%).
7) Se guardan en `clips` con `source=auto`, `score`, `rationale` y `use_llm`.

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
4) La API expone `download_url` (presigned GET) para descargar desde la UI.

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
Rutas principales:
- `GET /health`
- `POST /sermons`
- `GET /sermons`
- `GET /sermons/{id}`
- `PATCH /sermons/{id}`
- `DELETE /sermons/{id}`
- `POST /sermons/{id}/upload-complete`
- `GET /sermons/{id}/segments`
- `POST /sermons/{id}/suggest` (query opcional `use_llm=true|false`)
- `GET /sermons/{id}/suggestions`
- `POST /sermons/{id}/embed`
- `GET /sermons/{id}/search?q=...&k=...`
- `POST /clips`
- `GET /clips`
- `GET /clips/{id}`
- `PATCH /clips/{id}`
- `DELETE /clips/{id}`
- `POST /clips/{id}/render?type=preview|final`

## Almacenamiento (MinIO)
- Bucket: `sermon`
- Objetos de video original: `sermons/{sermon_id}/{uuid}-{filename}`
- Clips renderizados: `clips/{clip_id}/{uuid}.mp4`
- La API genera URLs firmadas para subir y descargar.

## Configuracion (.env)
Variables clave:
- `DATABASE_URL`, `REDIS_URL`
- `S3_ENDPOINT` (API/worker locales)
- `S3_INTERNAL_ENDPOINT` (solo Docker, usado por minio-init)
- `S3_PUBLIC_ENDPOINT` (endpoint accesible desde el navegador)
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION`, `S3_USE_SSL`
- `NEXT_PUBLIC_API_URL`
- `USE_LLM_FOR_CLIP_SUGGESTIONS` (default `false`)
- `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`
- `NEXT_PUBLIC_DEFAULT_USE_LLM_FOR_CLIPS` (default `false`)

## Notas de UX
- La web hace polling cada 3s cuando un sermon o clip esta en estado activo.
- El progreso se muestra en el dashboard y en la vista de detalle.
- En sugerencias, el usuario puede activar "Usar IA para sugerir clips".
- Las sugerencias con IA muestran un badge "IA".
- Al generar sugerencias, la UI muestra estado de "Generando sugerencias...".
- El preview de una sugerencia dispara el render y descarga automaticamente al finalizar.
- La lista de clips muestra solo clips manuales (se ocultan los `source=auto`).
