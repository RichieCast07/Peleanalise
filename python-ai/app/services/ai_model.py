"""
TensorFlow/Keras model loader + Grad-CAM heatmap generator.
"""

import json
import os
import time
import numpy as np
import cv2
import tensorflow as tf
from tensorflow import keras
from app.core.config import settings

_model: keras.Model | None = None
_is_mock = False
_class_names = ["Benigno", "Sospechoso", "Maligno"]

# Versión que se reporta cuando NO hay un modelo entrenado cargado
DEMO_MODEL_VERSION = "demo-sin-entrenar"


def _trained_model_version() -> str:
    """Versión del modelo entrenado: la escribe training/train.py en models/metrics.json."""
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(settings.MODEL_PATH)), "metrics.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)["_info"]["version"]
    except Exception:
        return settings.MODEL_VERSION


_decision_cache: dict | None | bool = False   # False = aún no leído


def _decision_thresholds() -> dict | None:
    """
    Umbrales de la regla de cribado (los calcula training/train.py o calibrate_decision.py y los deja en
    models/metrics.json -> _info.decision). Sin ellos se usa 'gana la clase más probable'.
    """
    global _decision_cache
    if _decision_cache is False:
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(settings.MODEL_PATH)), "metrics.json")
            with open(path, encoding="utf-8") as f:
                d = json.load(f)["_info"]["decision"]
            _decision_cache = {"tm": float(d["tm"]), "tn": float(d["tn"])}
        except Exception:
            _decision_cache = None
    return _decision_cache


def is_mock_model() -> bool:
    get_model()
    return _is_mock


def get_model() -> keras.Model:
    global _model, _is_mock
    if _model is None:
        try:
            _model = keras.models.load_model(settings.MODEL_PATH)
            _is_mock = False
            print(f"[AI] Model loaded from {settings.MODEL_PATH}")
        except Exception as e:
            print(f"[AI] WARNING: Could not load model ({e}). Using mock predictions.")
            _model = _build_mock_model()
            _is_mock = True
    return _model


def _build_mock_model() -> keras.Model:
    """Lightweight mock model for development when .keras file is unavailable."""
    inp = keras.Input(shape=(settings.IMG_SIZE, settings.IMG_SIZE, 3))
    x   = keras.layers.GlobalAveragePooling2D()(inp)
    out = keras.layers.Dense(3, activation="softmax")(x)
    m   = keras.Model(inp, out)
    m.compile(optimizer="adam", loss="categorical_crossentropy")
    return m


def preprocess_for_model(image_bgr: np.ndarray) -> np.ndarray:
    img = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (settings.IMG_SIZE, settings.IMG_SIZE))
    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, 0)


def predict(image_bgr: np.ndarray) -> dict:
    model = get_model()
    tensor = preprocess_for_model(image_bgr)

    start = time.time()
    probs = model.predict(tensor, verbose=0)[0]
    elapsed_ms = int((time.time() - start) * 1000)

    idx = int(np.argmax(probs))
    rule = None if _is_mock else _decision_thresholds()
    if rule:
        # Regla de cribado: favorece detectar malignos (ver training/MODEL_CARD.md)
        if probs[2] >= rule["tm"]:
            idx = 2
        elif probs[1] + probs[2] >= rule["tn"]:
            idx = 1
        else:
            idx = 0
    label      = _class_names[idx]
    probability = float(probs[idx])

    return {
        "prediccion":       label,
        "probabilidad":     probability,
        "prob_benigno":     float(probs[0]),
        "prob_sospechoso":  float(probs[1]),
        "prob_maligno":     float(probs[2]),
        "model_version":    DEMO_MODEL_VERSION if _is_mock else _trained_model_version(),
        "inference_time_ms": elapsed_ms,
    }


# ── Grad-CAM ──────────────────────────────────────────────────────────────────

def generate_gradcam(image_bgr: np.ndarray, last_conv_layer_name: str = "auto") -> np.ndarray:
    """
    Generate Grad-CAM heatmap overlay.
    Returns BGR image with heatmap overlaid.
    """
    model  = get_model()
    tensor = preprocess_for_model(image_bgr)

    # Auto-detect last conv layer
    if last_conv_layer_name == "auto":
        for layer in reversed(model.layers):
            if isinstance(layer, (keras.layers.Conv2D,)):
                last_conv_layer_name = layer.name
                break
        else:
            return _identity_overlay(image_bgr)

    try:
        grad_model = keras.Model(
            inputs=model.inputs,
            outputs=[model.get_layer(last_conv_layer_name).output, model.output],
        )

        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(tensor)
            pred_index = tf.argmax(predictions[0])
            class_channel = predictions[:, pred_index]

        grads       = tape.gradient(class_channel, conv_outputs)
        pooled      = tf.reduce_mean(grads, axis=(0, 1, 2))
        conv_out    = conv_outputs[0]
        cam         = tf.reduce_sum(tf.multiply(pooled, conv_out), axis=-1).numpy()

        # Normalize
        cam = np.maximum(cam, 0)
        if cam.max() > 0:
            cam = cam / cam.max()

        # Resize to original image size
        h, w = image_bgr.shape[:2]
        cam_resized = cv2.resize(cam, (w, h))
        heatmap     = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
        overlay     = cv2.addWeighted(image_bgr, 0.6, heatmap, 0.4, 0)
        return overlay

    except Exception as e:
        print(f"[GradCAM] Error: {e}")
        return _identity_overlay(image_bgr)


def _identity_overlay(image_bgr: np.ndarray) -> np.ndarray:
    return image_bgr.copy()
