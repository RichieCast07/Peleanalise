from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "PeleAnálise AI Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    MODEL_PATH: str = "models/melanoma_classifier.keras"
    MODEL_VERSION: str = "1.0.0"
    IMG_SIZE: int = 224

    # Seguridad (cuando el servicio está publicado en internet)
    AI_API_KEY: str = ""            # si se define, todas las rutas excepto /health exigen X-API-Key
    ALLOWED_IMAGE_HOSTS: str = ""   # p. ej. "blob.vercel-storage.com"; vacío = sin restricción (solo desarrollo)
    CORS_ORIGINS: str = "*"         # orígenes permitidos separados por coma

    # MinIO / S3 (for saving processed images)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "peleanalise"
    MINIO_USE_SSL: bool = False

    # Pixel-to-mm calibration (default: dermoscopy standard)
    PIXEL_PER_MM: float = 25.4

    class Config:
        env_file = ".env"


settings = Settings()
