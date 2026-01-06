# Detalle de funcionamiento

## Resumen
La web permite subir sermones en video, transcribirlos automaticamente y crear clips verticales con subtitulos. Los archivos se almacenan en MinIO y la base de datos guarda el estado, progreso y segmentos de transcripcion para monitorear el avance y construir clips descargables.

Este documento describe como funciona la web de Sermon de punta a punta: flujo de subida, transcripcion, clips y servicios involucrados.

## Arquitectura
- Web: Next.js (App Router) + Tailwind en `apps/web`
- API: FastAPI + SQLAlchemy en `apps/api`
- Worker: Celery en `apps/worker`
- Infra: Postgres, Redis, MinIO (S3 compatible)

Servicios principales (Docker Compose):
- `web` expone la UI en http://localhost:3000
- `api` expone la API en http://localhost:8000
- `minio` expone S3 en http://localhost:9000 y consola en http://localhost:9001
- `postgres` en 5432
- `redis` en 6379

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

## Clips (worker)
Flujo para crear un clip:
1) La UI envia `POST /clips` con `sermon_id`, `start_ms`, `end_ms`.
2) La API valida la duracion (10s a 120s) y encola `worker.render_clip`.
3) El worker:
   - Descarga el video original.
   - Construye un archivo SRT con los segmentos del rango.
   - Renderiza con ffmpeg (1080x1920) y subtitulos.
   - Sube el MP4 generado a MinIO.
   - Guarda `output_url` y marca `status = done`.
4) La API expone `download_url` (presigned GET) para descargar desde la UI.

## Estados y progreso
Sermon (`SermonStatus`):
- `pending` -> `uploaded` -> `processing` -> `transcribed`
- `error` si falla la tarea

Clip (`ClipStatus`):
- `pending` -> `processing` -> `done`
- `error` si falla la tarea

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
- `POST /clips`
- `GET /clips`
- `GET /clips/{id}`
- `PATCH /clips/{id}`
- `DELETE /clips/{id}`

## Almacenamiento (MinIO)
- Bucket: `sermon`
- Objetos de video original: `sermons/{sermon_id}/{uuid}-{filename}`
- Clips renderizados: `clips/{clip_id}/{uuid}.mp4`
- La API genera URLs firmadas para subir y descargar.

## Configuracion (.env)
Variables clave:
- `DATABASE_URL`, `REDIS_URL`
- `S3_ENDPOINT` (endpoint interno para containers)
- `S3_PUBLIC_ENDPOINT` (endpoint accesible desde el navegador)
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION`, `S3_USE_SSL`
- `NEXT_PUBLIC_API_URL`

## Notas de UX
- La web hace polling cada 3s cuando un sermon o clip esta en estado activo.
- El progreso se muestra en el dashboard y en la vista de detalle.
