# Entrenamiento del clasificador (Benigno / Sospechoso / Maligno)

Transfer learning con MobileNetV2 sobre HAM10000. Genera `models/melanoma_classifier.keras`,
`models/metrics.json` y `models/MODEL_CARD.md`.

## Requisitos
- Windows con **Python 3.11 o 3.12** (TensorFlow no funciona con 3.13+), `curl.exe` (viene con Windows 10/11).
- **~4 GB libres** en disco (el dataset se procesa por partes y se borra lo descargado) y **8 GB de RAM**.
- Internet (~3,5 GB de descarga; unos 20 minutos con 3 MB/s).

## Pasos (Git Bash, desde la carpeta `python-ai`)
```bash
# 1. Entorno (si ya corriste start.ps1 existe en %USERPROFILE%\.peleanalise\venv)
py -3.12 -m venv .venv-train
.venv-train/Scripts/pip install -r requirements.txt -r training/requirements-train.txt

# 2. Descargar y preparar HAM10000 (se guarda en ~/pele_data/ham10000)
.venv-train/Scripts/python training/prepare_data.py

# 3. Entrenar (en CPU tarda de 40 a 90 minutos)
.venv-train/Scripts/python -u training/train.py
```
Prueba rápida del pipeline (2-3 min, el modelo resultante NO sirve):
`python training/train.py --limit 192 --epochs1 1 --epochs2 1 --out /tmp/prueba.keras`

Al terminar, reinicia el servicio de IA: deja de mostrar "demostración" y usa el modelo.

## Qué esperar (y qué no)
- Ningún modelo es perfecto: léelo en `models/MODEL_CARD.md` (matriz de confusión, sensibilidad
  para melanoma, intervalos de confianza). Hay falsos negativos.
- Los datos se separan **por lesión** (no por imagen) para no inflar las métricas.
- La agrupación de los 7 diagnósticos en 3 clases (`DX_TO_CLASS` en `train.py`) es una decisión
  clínica que debe validar un dermatólogo.
- HAM10000 es piel mayormente clara y dermatoscopia; el desempeño con fotos de celular u otros
  tonos de piel no está medido.
