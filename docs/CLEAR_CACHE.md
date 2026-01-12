# Como borrar la cache del worker

El worker usa varias caches que puedes limpiar si es necesario:

## 1. Cache de modelos de faster-whisper

faster-whisper guarda los modelos descargados en:
- **Windows**: `C:\Users\<tu_usuario>\.cache\faster-whisper`
- **Linux/Mac**: `~/.cache/faster-whisper`

Para borrarla:
```bash
# Windows (PowerShell)
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\faster-whisper"

# Linux/Mac
rm -rf ~/.cache/faster-whisper
```

## 2. Cache de modelos de sentence-transformers

sentence-transformers guarda modelos en:
- **Windows**: `C:\Users\<tu_usuario>\.cache\huggingface`
- **Linux/Mac**: `~/.cache/huggingface`

Para borrarla:
```bash
# Windows (PowerShell)
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface"

# Linux/Mac
rm -rf ~/.cache/huggingface
```

## 3. Cola de tareas de Celery (Redis)

Para limpiar las tareas pendientes en Redis:

```bash
# Conectarse a Redis CLI
redis-cli

# Limpiar todas las colas (CUIDADO: elimina tareas pendientes)
FLUSHALL

# O limpiar una cola específica
DEL celery
```

O desde Python:
```python
from celery import Celery
celery_app = Celery('worker', broker='redis://localhost:6379/0')
celery_app.control.purge()  # Elimina tareas pendientes
```

## 4. Logs de IA

Los logs de IA se guardan en el directorio `logIA` en la raíz del proyecto.

Para borrarlos:
```bash
# Windows (PowerShell)
Remove-Item -Recurse -Force logIA\*

# Linux/Mac
rm -rf logIA/*
```

## Nota importante

- Borrar la cache de modelos hará que se vuelvan a descargar la próxima vez que se usen
- Limpiar Redis eliminará las tareas pendientes (pueden perderse trabajos en progreso)
- Los logs de IA son solo informativos, borrarlos no afecta el funcionamiento





