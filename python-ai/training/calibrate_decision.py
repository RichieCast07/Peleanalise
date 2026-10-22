"""
Ajusta la regla de decisión (cribado) de un modelo YA entrenado, sin reentrenar.

Carga models/melanoma_classifier.keras, calcula probabilidades en validación y prueba con la MISMA
partición con la que se entrenó (se lee de metrics.json si se quitaron duplicados o no), busca los
umbrales en validación, evalúa en prueba y actualiza metrics.json y MODEL_CARD.md.

Uso (sin -I, necesita importar train.py):
    python training/calibrate_decision.py [--data-dir RUTA] [--model models/melanoma_classifier.keras] [--target-sens 0.90]
"""

import argparse
import json
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
from tensorflow import keras

import train  # mismo directorio


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.expanduser("~"), "pele_data", "ham10000"))
    ap.add_argument("--model", default=os.path.join(here, "..", "models", "melanoma_classifier.keras"))
    ap.add_argument("--target-sens", type=float, default=0.90)
    ap.add_argument("--batch", type=int, default=64)
    args = ap.parse_args()

    model_path = os.path.abspath(args.model)
    metrics_path = os.path.join(os.path.dirname(model_path), "metrics.json")
    with open(metrics_path, encoding="utf-8") as f:
        old = json.load(f)
    info = old.get("_info", {})
    # Los modelos entrenados antes de la corrección usaron los datos CON duplicados
    dedupe = bool(info.get("dedupe", False))
    print(f"partición: {'sin' if dedupe else 'con'} duplicados (según metrics.json)", flush=True)

    X, meta = train.load_data(args.data_dir, dedupe=dedupe)
    y = meta["y"].values.astype(np.int32)
    tr, va, te = train.split_by_lesion(meta)
    for nm, ii in (("train", tr), ("val", va), ("test", te)):
        print(f"  {nm}: " + ", ".join(f"{c}={int((y[ii] == k).sum())}" for k, c in enumerate(train.CLASS_NAMES)), flush=True)

    model = keras.models.load_model(model_path)
    p_va = model.predict(train.make_dataset(X, y, va, args.batch, False), verbose=0)
    p_te = model.predict(train.make_dataset(X, y, te, args.batch, False), verbose=0)

    metrics, decision = train.build_report(p_va, y[va], p_te, y[te], meta.iloc[te], args.target_sens)
    metrics["_info"] = {**info, "dedupe": dedupe, "decision": decision}
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    train.write_card(os.path.join(os.path.dirname(model_path), "MODEL_CARD.md"), metrics,
                     {"version": info.get("version", "?"), "T": info.get("T", 1.0),
                      "n_total": info.get("n_total", len(X)), "n_lesiones": info.get("n_lesiones", meta.lesion_id.nunique())})

    s, d = metrics["regla_screening"], decision
    print(f"\nUmbrales: tm={d['tm']}  tn={d['tn']}  (validación: sens={d['sens_no_benigno_val']:.3f}, esp={d['especificidad_val']:.3f})")
    print("PRUEBA, 'gana la más probable':", {k: round(metrics[k], 3) for k in ("sensibilidad_maligno_o_sospechoso", "especificidad_benigno", "accuracy_balanceada")})
    print("PRUEBA, regla de cribado      :", {k: round(s[k], 3) for k in ("sensibilidad_maligno_o_sospechoso", "especificidad_benigno", "accuracy_balanceada")})
    print("matriz (cribado):", s["matriz_confusion_filas_real_columnas_predicho"])


if __name__ == "__main__":
    main()
