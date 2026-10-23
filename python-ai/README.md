---
title: PeleAnalise IA
emoji: 🩺
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Servicio de IA de PeleAnálise

API FastAPI (TensorFlow + OpenCV): `/analyze` (clasificación + ABCDE + Grad-CAM), `/report/generate` (PDF) y `/health`.

El bloque de arriba (entre `---`) solo lo usa Hugging Face Spaces; en GitHub se ignora.

## Variables de entorno (configurar como *Secrets* del hosting)
| Variable | Qué hace |
|---|---|
| `AI_API_KEY` | Clave que la aplicación web envía en `X-API-Key`. **Obligatoria si el servicio es público.** |
| `ALLOWED_IMAGE_HOSTS` | Hosts desde los que se pueden descargar imágenes, p. ej. `blob.vercel-storage.com`. |
| `CORS_ORIGINS` | Orígenes permitidos (coma). La app web llama desde el servidor, normalmente no hace falta. |

El modelo (`models/melanoma_classifier.keras`) y su ficha (`models/metrics.json`, `models/MODEL_CARD.md`) van en la imagen.
Ver `../DEPLOY.md` para el despliegue completo.
