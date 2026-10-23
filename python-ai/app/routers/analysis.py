import io
import httpx
import numpy as np
import cv2

from fastapi import APIRouter, HTTPException
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, ProcessedImages
from app.services.image_processing import full_pipeline
from app.services.abcde import compute_abcde
from app.services.ai_model import predict, generate_gradcam
from app.core.config import settings
from app.core.security import check_image_url

router = APIRouter(prefix="/analyze", tags=["analysis"])


async def download_image(url: str) -> np.ndarray:
    check_image_url(url)
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar la imagen: {url}")
        arr = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Imagen inválida o corrupta")
        return img


@router.post("", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    # 1. Download image
    image_bgr = await download_image(req.image_url)

    # 2. Preprocessing pipeline
    processed = full_pipeline(image_bgr)

    # 3. ABCDE metrics
    ppm   = req.pixel_per_mm or settings.PIXEL_PER_MM
    abcde = compute_abcde(processed["original"], processed["mask"], pixel_per_mm=ppm)

    # 4. AI prediction
    # El modelo se entrenó con imágenes ORIGINALES (sin quitar vello ni normalizar contraste); si recibe
    # la imagen "limpia" su rendimiento cae (ver python-ai/training/README.md). El preprocesado queda
    # solo para las métricas ABCDE.
    result = predict(processed["original"])

    # 5. Grad-CAM
    gradcam_img = generate_gradcam(processed["original"])

    # 6. (Optional) upload processed images to MinIO — omitted here for brevity
    processed_images = ProcessedImages()

    return AnalyzeResponse(
        prediccion=result["prediccion"],
        probabilidad=result["probabilidad"],
        prob_benigno=result["prob_benigno"],
        prob_sospechoso=result["prob_sospechoso"],
        prob_maligno=result["prob_maligno"],
        model_version=result["model_version"],
        inference_time_ms=result["inference_time_ms"],
        abcde=abcde,
        processed_images=processed_images,
    )
