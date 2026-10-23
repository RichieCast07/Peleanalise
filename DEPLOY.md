# Despliegue de PeleAnálise

PeleAnálise son tres piezas y **no caben todas en Vercel**:

| Pieza | Dónde va | Por qué |
|---|---|---|
| Frontend + API (Nuxt) | **Vercel** | Es lo que Vercel hospeda bien |
| Base de datos MySQL | MySQL en la nube (TiDB Cloud o Aiven, gratis) | Vercel no ofrece MySQL |
| Servicio de IA (TensorFlow) | **Hugging Face Spaces** (Docker, gratis) | TensorFlow supera el límite de tamaño de las funciones de Vercel |
| Imágenes | **Vercel Blob** | El disco de Vercel no es persistente |

```
Navegador ─► Vercel (Nuxt) ─► MySQL (nube)
                 │  └──────► Vercel Blob (imágenes)
                 └─ X-API-Key ─► Hugging Face Space (FastAPI + TensorFlow + modelo)
```

> ⚠️ **Datos médicos.** Es un proyecto académico. En la nube usa **solo datos ficticios**. Las imágenes en Vercel Blob
> tienen una URL pública (difícil de adivinar, pero sin control de acceso) y la base no está cifrada por la aplicación.
> Para pacientes reales hace falta cumplir la normativa de datos personales (p. ej. LFPDPPP) y otra arquitectura.

## 1. Base de datos MySQL (gratis)

**TiDB Cloud (Starter, sin tarjeta)** — https://tidbcloud.com → crear cluster → *Connect* → *Prisma* → copiar la URL.
La URL debe quedar así (añade los parámetros al final):
```
mysql://USUARIO:CLAVE@gateway01.REGION.prod.aws.tidbcloud.com:4000/peleanalise?sslaccept=strict&connection_limit=1
```
Crea la base `peleanalise` (en el panel *SQL Editor*: `CREATE DATABASE peleanalise;`).

Alternativa con MySQL "de verdad": **Aiven for MySQL** (plan gratis). Si `prisma db push` falla con TiDB por llaves foráneas, usa Aiven.

Crea las tablas y los usuarios iniciales **desde tu PC** (PowerShell o Git Bash, en `frontend/`):
```bash
cd frontend
DATABASE_URL="mysql://...tu-url..." npx prisma db push
DATABASE_URL="mysql://...tu-url..." SEED_ADMIN_PASSWORD="UnaClaveFuerte1!" SEED_DOCTOR_PASSWORD="OtraClave2!" SEED_CAPTURISTA_PASSWORD="Otra3!" npx tsx prisma/seed.ts
```
(En PowerShell: `$env:DATABASE_URL="..."; $env:SEED_ADMIN_PASSWORD="..."; ...; npx prisma db push`.)
**No dejes las contraseñas de ejemplo** (`Admin123!`) en un sitio público.

## 2. Servicio de IA en Hugging Face Spaces (gratis)

1. https://huggingface.co → *New Space* → SDK **Docker** → *Blank* → nombre `peleanalise-ia` (público o privado).
2. Clona el Space y copia dentro el contenido de `python-ai/` **sin** `venv/`, `.venv-train/`, `training/`, `tests/`:
   `app/`, `models/`, `Dockerfile`, `requirements.txt`, `README.md`, `.dockerignore`.
   ```bash
   git clone https://huggingface.co/spaces/TU_USUARIO/peleanalise-ia
   # copia los archivos de arriba dentro de peleanalise-ia/
   cd peleanalise-ia && git add . && git commit -m "Servicio de IA" && git push
   ```
   (Pide usuario y un *token de escritura* de Hugging Face: Settings → Access Tokens.)
   El modelo pesa ~9 MB; si algún día pasa de 10 MB, usa `git lfs track "*.keras"`.
3. En el Space → *Settings* → *Variables and secrets* → **Secrets**:
   | Secret | Valor |
   |---|---|
   | `AI_API_KEY` | una clave larga aleatoria (la misma irá en Vercel) |
   | `ALLOWED_IMAGE_HOSTS` | `blob.vercel-storage.com` |
4. Cuando termine de construir, `https://TU_USUARIO-peleanalise-ia.hf.space/health` debe responder `{"status":"ok","model_loaded":true}`.

Clave aleatoria: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`

## 3. Frontend en Vercel

1. https://vercel.com → *Add New… → Project* → importa el repositorio de GitHub.
2. **No uses "Services" ni importes `python-ai`.** Pulsa **Import single project** en la tarjeta **frontend (Nuxt)**,
   o pon **Root Directory = `frontend`**. Preset: Nuxt (se detecta solo).
3. *Environment Variables*:
   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | la URL de MySQL del paso 1 |
   | `JWT_SECRET` | aleatoria larga |
   | `JWT_REFRESH_SECRET` | aleatoria larga (distinta) |
   | `PYTHON_AI_URL` | `https://TU_USUARIO-peleanalise-ia.hf.space` (sin `/` final) |
   | `AI_API_KEY` | la misma del Space |
4. **Deploy.**
5. Almacenamiento de imágenes: proyecto → pestaña **Storage** → *Create* → **Blob** → conéctalo al proyecto
   (agrega solo `BLOB_READ_WRITE_TOKEN`) y haz **Redeploy**.

## 4. Comprobar
- Entra con el administrador que creaste en el paso 1, crea un paciente y un estudio con una imagen, pulsa **Analizar con IA** y descarga el PDF.
- Si el análisis dice *"No se pudo conectar con el servicio de IA"*: abre `.../health` del Space (puede estar dormido).

## Límites a tener en cuenta
- **Spaces gratuitos se duermen** tras ~48 h sin uso. El primer análisis después de dormir puede tardar más de 60 s
  (cargar TensorFlow) y las funciones de Vercel (plan Hobby) cortan a los 60 s: abre `/health` del Space para despertarlo y reintenta.
- **Vercel Hobby es solo para uso personal/no comercial.**
- Las subidas a Vercel no pueden pasar de 4,5 MB: la aplicación reduce sola las fotos grandes (lado máx. 2000 px) antes de subirlas.
- El modelo es **experimental**: ver `python-ai/models/MODEL_CARD.md`.
