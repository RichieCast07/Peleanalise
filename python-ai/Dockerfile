FROM python:3.11-slim

# Dependencias del sistema para OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Usuario sin privilegios (lo exige Hugging Face Spaces; buena práctica en cualquier hosting)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    TF_CPP_MIN_LOG_LEVEL=2 \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user app/ ./app/
# Modelo entrenado + su ficha (metrics.json trae la versión y los umbrales de decisión)
COPY --chown=user models/ ./models/

# Hugging Face Spaces usa 7860; Render/Railway/Fly inyectan PORT
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
