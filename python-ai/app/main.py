from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import require_api_key
from app.routers import analysis, reports

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    # allow_credentials=True es incompatible con origen "*"
    allow_credentials=_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Con AI_API_KEY definida, las rutas de análisis y reportes exigen la clave
app.include_router(analysis.router, dependencies=[Depends(require_api_key)])
app.include_router(reports.router,  dependencies=[Depends(require_api_key)])


@app.get("/health")
def health():
    from app.services.ai_model import is_mock_model
    return {"status": "ok", "version": settings.APP_VERSION, "model_loaded": not is_mock_model()}


@app.on_event("startup")
async def startup():
    from app.services.ai_model import get_model
    get_model()  # Pre-load model at startup
    print(f"[Startup] {settings.APP_NAME} ready")
