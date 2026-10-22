"""
Entrena el clasificador Benigno / Sospechoso / Maligno con HAM10000 (transfer learning, MobileNetV2).

Requiere haber ejecutado antes training/prepare_data.py.
Uso:  python training/train.py [--data-dir RUTA] [--out models/melanoma_classifier.keras]

El modelo guardado recibe imágenes RGB 224x224 en [0, 1] (como app/services/ai_model.py) y devuelve
3 probabilidades [Benigno, Sospechoso, Maligno] calibradas con temperature scaling.
"""

import argparse
import glob
import json
import os
import time

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from tensorflow import keras

IMG_SIZE    = 224
CLASS_NAMES = ["Benigno", "Sospechoso", "Maligno"]

# Agrupación de los 7 diagnósticos de HAM10000 en las 3 clases de la app.
# ES UNA DECISIÓN CLÍNICA: debe validarla un dermatólogo antes de usar el sistema con pacientes.
DX_TO_CLASS = {
    # Benigno
    "nv": 0, "melanocytic_Nevi": 0,
    "bkl": 0, "benign_keratosis-like_lesions": 0,
    "df": 0, "dermatofibroma": 0,
    "vasc": 0, "vascular_lesions": 0,
    # Sospechoso: lesión precancerosa
    "akiec": 1, "actinic_keratoses": 1,
    # Maligno
    "bcc": 2, "basal_cell_carcinoma": 2,
    "mel": 2, "melanoma": 2,
}
SEED = 42


# ── Datos ────────────────────────────────────────────────────────────────────

def load_data(data_dir: str, dedupe: bool = True):
    """
    Carga los shards. El espejo de Hugging Face repite imágenes idénticas (13.354 filas para 10.015
    imágenes únicas de HAM10000); con dedupe=True se conserva una sola copia de cada image_id.
    (dedupe=False reproduce la partición de modelos entrenados antes de esta corrección.)
    """
    shards = sorted(glob.glob(os.path.join(data_dir, "shards", "shard*_X.npy")))
    if not shards:
        raise SystemExit("No hay datos. Ejecuta primero: python training/prepare_data.py")
    xs, metas, seen = [], [], set()
    for p in shards:
        x = np.load(p)
        m = pd.read_csv(p.replace("_X.npy", "_meta.csv"))
        assert len(m) == len(x), "metadatos e imágenes desalineados"
        if dedupe:
            keep = np.array([iid not in seen for iid in m["image_id"]])
            seen.update(m["image_id"][keep])
            x, m = x[keep], m[keep]
        xs.append(x)
        metas.append(m)
    X = np.concatenate(xs)
    meta = pd.concat(metas, ignore_index=True)
    assert len(meta) == len(X), "metadatos e imágenes desalineados"
    meta["y"] = meta["dx"].map(DX_TO_CLASS)
    assert meta["y"].notna().all(), f"diagnósticos desconocidos: {set(meta['dx']) - set(DX_TO_CLASS)}"
    return X, meta


def split_by_lesion(meta: pd.DataFrame):
    """70/15/15 separando por lesion_id: ninguna lesión aparece en dos particiones."""
    idx = np.arange(len(meta))
    sgkf = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=SEED)
    rest, test = next(sgkf.split(idx, meta["dx"], meta["lesion_id"]))
    sub = meta.iloc[rest]
    sgkf2 = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=SEED)
    tr_i, va_i = next(sgkf2.split(rest, sub["dx"], sub["lesion_id"]))
    train, val = rest[tr_i], rest[va_i]
    assert not set(meta.lesion_id.iloc[train]) & set(meta.lesion_id.iloc[test])
    assert not set(meta.lesion_id.iloc[train]) & set(meta.lesion_id.iloc[val])
    assert not set(meta.lesion_id.iloc[val]) & set(meta.lesion_id.iloc[test])
    return train, val, test


def augment(img):
    img = tf.image.random_flip_left_right(img)
    img = tf.image.random_flip_up_down(img)
    img = tf.image.rot90(img, tf.random.uniform([], 0, 4, tf.int32))
    size = tf.cast(IMG_SIZE * tf.random.uniform([], 0.8, 1.0), tf.int32)
    img = tf.image.random_crop(img, [size, size, 3])
    img = tf.image.resize(img, (IMG_SIZE, IMG_SIZE))
    img = tf.image.random_brightness(img, 0.1)
    img = tf.image.random_contrast(img, 0.9, 1.1)
    img = tf.image.random_saturation(img, 0.9, 1.1)
    img = tf.image.random_hue(img, 0.02)
    return tf.clip_by_value(img, 0.0, 1.0)


def make_dataset(X, y, idx, batch, train, weights=None):
    rng = np.random.default_rng(SEED)

    def gen():
        order = rng.permutation(idx) if train else idx
        for i in order:
            yield (X[i], y[i], weights[y[i]]) if weights is not None else (X[i], y[i])

    sig = (tf.TensorSpec((IMG_SIZE, IMG_SIZE, 3), tf.uint8), tf.TensorSpec((), tf.int32))
    if weights is not None:
        sig += (tf.TensorSpec((), tf.float32),)
    ds = tf.data.Dataset.from_generator(gen, output_signature=sig)

    def prep(img, label, *w):
        img = tf.cast(img, tf.float32) / 255.0
        if train:
            img = augment(img)
        return (img, label) + tuple(w)

    ds = ds.map(prep, num_parallel_calls=tf.data.AUTOTUNE).batch(batch)
    return ds.prefetch(tf.data.AUTOTUNE)


# ── Modelo ───────────────────────────────────────────────────────────────────

def build_model():
    inp = keras.Input((IMG_SIZE, IMG_SIZE, 3), name="imagen_0_1")
    x = keras.layers.Rescaling(2.0, offset=-1.0, name="a_menos1_1")(inp)          # MobileNetV2 espera [-1, 1]
    base = keras.applications.MobileNetV2(input_tensor=x, include_top=False, weights="imagenet")
    h = keras.layers.GlobalAveragePooling2D(name="gap")(base.output)
    h = keras.layers.Dropout(0.3, name="drop")(h)
    logits = keras.layers.Dense(3, name="logits")(h)
    return keras.Model(inp, logits), base


def set_trainable(model, from_layer: str | None):
    """Congela todo salvo la cabeza; si from_layer, descongela desde esa capa (BatchNorm queda congelada)."""
    head = {"gap", "drop", "logits"}
    names = [l.name for l in model.layers]
    start = names.index(from_layer) if from_layer else len(names)
    for i, l in enumerate(model.layers):
        l.trainable = l.name in head or (i >= start and not isinstance(l, keras.layers.BatchNormalization))


def fit_temperature(logits, y):
    best_t, best_nll = 1.0, 1e9
    for t in np.arange(0.4, 5.01, 0.05):
        z = logits / t
        z = z - z.max(1, keepdims=True)
        p = np.exp(z) / np.exp(z).sum(1, keepdims=True)
        nll = -np.log(p[np.arange(len(y)), y] + 1e-9).mean()
        if nll < best_nll:
            best_t, best_nll = float(t), float(nll)
    return best_t


def softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


# ── Evaluación ───────────────────────────────────────────────────────────────

def bootstrap_ci(fn, y, pred, groups, n=1000):
    """IC 95% remuestreando lesiones (no imágenes) para no subestimar la incertidumbre."""
    rng = np.random.default_rng(SEED)
    ug = np.unique(groups)
    by_g = {g: np.where(groups == g)[0] for g in ug}
    vals = []
    for _ in range(n):
        pick = rng.choice(ug, len(ug))
        ii = np.concatenate([by_g[g] for g in pick])
        try:
            vals.append(fn(y[ii], pred[ii]))
        except Exception:
            pass
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def apply_decision(probs, tm, tn):
    """
    Regla de decisión orientada a cribado (misma lógica que app/services/ai_model.py):
      Maligno    si P(Maligno) >= tm
      Sospechoso si P(Sospechoso)+P(Maligno) >= tn
      Benigno    en otro caso
    Equivale a mover el umbral para favorecer la sensibilidad (más falsas alarmas, menos malignos omitidos).
    """
    pred = np.zeros(len(probs), dtype=np.int32)
    pred[(probs[:, 1] + probs[:, 2]) >= tn] = 1
    pred[probs[:, 2] >= tm] = 2
    return pred


def tune_decision(probs, y, target=0.90):
    """
    Busca (tm, tn) en VALIDACIÓN: entre las reglas que dejan pasar como Benigno a lo sumo (1-target) de
    los malignos, elige la que menos benignos marca como alerta. Si ninguna alcanza el objetivo, la de
    mayor sensibilidad.
    """
    grid = np.round(np.arange(0.03, 0.91, 0.02), 2)
    mal, ben = y == 2, y == 0
    best, best_key = None, None
    for tm in grid:
        for tn in grid:
            pred = apply_decision(probs, tm, tn)
            sens = float(((pred > 0) & mal).sum() / max(mal.sum(), 1))
            spec = float(((pred == 0) & ben).sum() / max(ben.sum(), 1))
            key = (1, spec, sens) if sens >= target else (0, sens, spec)
            if best_key is None or key > best_key:
                best_key, best = key, (float(tm), float(tn), sens, spec)
    return {"tm": best[0], "tn": best[1], "sens_no_benigno_val": best[2], "especificidad_val": best[3], "objetivo": target}


def evaluate(probs, y, meta_te, pred=None):
    pred = probs.argmax(1) if pred is None else pred
    cm = confusion_matrix(y, pred, labels=[0, 1, 2])
    rep = classification_report(y, pred, labels=[0, 1, 2], target_names=CLASS_NAMES, output_dict=True, zero_division=0)
    groups = meta_te["lesion_id"].values

    # Sensibilidad para "Maligno" y para "no benigno" (Sospechoso o Maligno): lo que importa al cribar
    def sens_mal(yt, yp):  return float(((yp == 2) & (yt == 2)).sum() / max((yt == 2).sum(), 1))
    def sens_nobenig(yt, yp): return float(((yp > 0) & (yt == 2)).sum() / max((yt == 2).sum(), 1))
    def spec_ben(yt, yp):  return float(((yp == 0) & (yt == 0)).sum() / max((yt == 0).sum(), 1))

    mel = (meta_te["dx"].isin(["mel", "melanoma"])).values
    out = {
        "n_test_imagenes": int(len(y)),
        "n_test_lesiones": int(len(np.unique(groups))),
        "accuracy": float((pred == y).mean()),
        "accuracy_balanceada": float(balanced_accuracy_score(y, pred)),
        "accuracy_balanceada_IC95": bootstrap_ci(balanced_accuracy_score, y, pred, groups),
        "sensibilidad_maligno": sens_mal(y, pred),
        "sensibilidad_maligno_IC95": bootstrap_ci(sens_mal, y, pred, groups),
        "sensibilidad_maligno_o_sospechoso": sens_nobenig(y, pred),
        "especificidad_benigno": spec_ben(y, pred),
        "sensibilidad_melanoma_marcado_no_benigno": float(((pred[mel] > 0).mean()) if mel.any() else 0.0),
        "auc_ovr_macro": float(roc_auc_score(y, probs, multi_class="ovr", average="macro", labels=[0, 1, 2])),
        "matriz_confusion_filas_real_columnas_predicho": cm.tolist(),
        "por_clase": {k: {m: float(v) for m, v in rep[k].items()} for k in CLASS_NAMES},
    }
    return out


def build_report(probs_va, y_va, probs_te, y_te, meta_te, target):
    """Métricas con 'gana la más probable' + regla de cribado ajustada en validación."""
    metrics = evaluate(probs_te, y_te, meta_te)
    decision = tune_decision(probs_va, y_va, target)
    pred = apply_decision(probs_te, decision["tm"], decision["tn"])
    metrics["regla_screening"] = evaluate(probs_te, y_te, meta_te, pred=pred)
    return metrics, decision


def write_card(path, metrics, info):
    m = metrics
    cm = np.array(m["matriz_confusion_filas_real_columnas_predicho"])
    lines = [
        "# Modelo de clasificación PeleAnálise",
        "",
        f"- Versión: `{info['version']}`  ·  Arquitectura: MobileNetV2 (transfer learning, ImageNet)",
        f"- Datos: HAM10000 ({info['n_total']} imágenes, {info['n_lesiones']} lesiones). Partición por **lesión** 70/15/15.",
        f"- Entrada: RGB {IMG_SIZE}x{IMG_SIZE} en [0,1]  ·  Salida: probabilidades [Benigno, Sospechoso, Maligno] (temperature scaling T={info['T']:.2f})",
        "",
        "## Agrupación de diagnósticos (decisión clínica, requiere validación médica)",
        "- Benigno: nevus melanocítico, queratosis benigna, dermatofibroma, lesión vascular",
        "- Sospechoso: queratosis actínica (lesión precancerosa)",
        "- Maligno: melanoma, carcinoma basocelular",
        "",
        f"## Resultados en el conjunto de prueba ({m['n_test_imagenes']} imágenes de {m['n_test_lesiones']} lesiones no vistas)",
        f"- Accuracy: {m['accuracy']:.3f}  ·  Accuracy balanceada: {m['accuracy_balanceada']:.3f} (IC95% {m['accuracy_balanceada_IC95'][0]:.3f}–{m['accuracy_balanceada_IC95'][1]:.3f})",
        f"- Sensibilidad para Maligno: {m['sensibilidad_maligno']:.3f} (IC95% {m['sensibilidad_maligno_IC95'][0]:.3f}–{m['sensibilidad_maligno_IC95'][1]:.3f})",
        f"- Sensibilidad Maligno detectado como Sospechoso o Maligno: {m['sensibilidad_maligno_o_sospechoso']:.3f}",
        f"- Especificidad para Benigno: {m['especificidad_benigno']:.3f}",
        f"- AUC (uno contra resto, promedio): {m['auc_ovr_macro']:.3f}",
        "",
        "Matriz de confusión (filas = real, columnas = predicho):",
        "",
        "| | Benigno | Sospechoso | Maligno |", "|---|---|---|---|",
    ]
    for n, row in zip(CLASS_NAMES, cm):
        lines.append(f"| {n} | " + " | ".join(str(int(v)) for v in row) + " |")
    s = m.get("regla_screening")
    dec = (m.get("_info") or {}).get("decision")
    if s and dec:
        scm = np.array(s["matriz_confusion_filas_real_columnas_predicho"])
        lines += [
            "",
            "## Regla de decisión orientada a cribado (la que usa la aplicación)",
            f"Con \"gana la clase más probable\" se omiten malignos. La aplicación usa umbrales ajustados en validación "
            f"(objetivo: que como máximo {100 * (1 - dec['objetivo']):.0f} % de los malignos se marquen Benigno):",
            f"- Maligno si P(Maligno) ≥ {dec['tm']:.2f}  ·  Sospechoso si P(Sospechoso)+P(Maligno) ≥ {dec['tn']:.2f}  ·  si no, Benigno.",
            f"- Sensibilidad (maligno marcado Sospechoso o Maligno): **{s['sensibilidad_maligno_o_sospechoso']:.3f}**",
            f"- Sensibilidad para Maligno exacto: {s['sensibilidad_maligno']:.3f}  ·  Especificidad Benigno: **{s['especificidad_benigno']:.3f}**  ·  Accuracy balanceada: {s['accuracy_balanceada']:.3f}",
            "- Costo: más benignos marcados como alerta (falsas alarmas). Es el compromiso habitual al cribar.",
            "",
            "Matriz de confusión con esta regla (filas = real, columnas = predicho):",
            "",
            "| | Benigno | Sospechoso | Maligno |", "|---|---|---|---|",
        ]
        for n, row in zip(CLASS_NAMES, scm):
            lines.append(f"| {n} | " + " | ".join(str(int(v)) for v in row) + " |")
    lines += [
        "",
        "## Limitaciones (leer antes de usar)",
        "- **No existe un modelo sin error.** Los falsos negativos (lesiones malignas clasificadas como benignas) son posibles; ver la matriz.",
        "- HAM10000 es dermatoscopia de población mayormente de piel clara (Austria y Australia). El rendimiento en otros tonos de piel, fotos con celular o equipos distintos puede ser **peor** y no está medido.",
        "- Es una herramienta de apoyo. No sustituye el diagnóstico del dermatólogo ni la biopsia.",
        "- Las clases están muy desbalanceadas (≈67 % nevus), por eso se reportan sensibilidad por clase y no solo accuracy.",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.expanduser("~"), "pele_data", "ham10000"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "models", "melanoma_classifier.keras"))
    ap.add_argument("--version", default="ham10000-mobilenetv2-v1")
    ap.add_argument("--epochs1", type=int, default=5)
    ap.add_argument("--epochs2", type=int, default=10)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0, help="usar solo N imágenes de entrenamiento (prueba rápida)")
    ap.add_argument("--keep-duplicates", action="store_true", help="no quitar imágenes repetidas (comportamiento anterior)")
    ap.add_argument("--target-sens", type=float, default=0.90, help="sensibilidad objetivo (maligno marcado no benigno) para la regla de cribado")
    args = ap.parse_args()

    tf.keras.utils.set_random_seed(SEED)
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    t0 = time.time()
    X, meta = load_data(args.data_dir, dedupe=not args.keep_duplicates)
    y = meta["y"].values.astype(np.int32)
    train, val, test = split_by_lesion(meta)
    if args.limit:
        train = np.random.default_rng(SEED).permutation(train)[: args.limit]
    print(f"imágenes: {len(X)} | lesiones: {meta.lesion_id.nunique()} | train {len(train)} val {len(val)} test {len(test)}", flush=True)
    for nm, ii in (("train", train), ("val", val), ("test", test)):
        print(f"  {nm}: " + ", ".join(f"{c}={int((y[ii] == k).sum())}" for k, c in enumerate(CLASS_NAMES)), flush=True)

    counts = np.bincount(y[train], minlength=3).astype(np.float32)
    weights = ((len(train) / (3.0 * counts)) ** 0.5).astype(np.float32)          # balanceo suavizado (raíz)
    print("pesos de clase:", dict(zip(CLASS_NAMES, weights.round(2))), flush=True)

    ds_tr = make_dataset(X, y, train, args.batch, True, weights)
    ds_va = make_dataset(X, y, val, args.batch, False)
    ds_te = make_dataset(X, y, test, args.batch, False)

    model, _ = build_model()
    loss = keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    # Fase 1: solo la cabeza
    set_trainable(model, None)
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss=loss, metrics=["accuracy"])
    print("== Fase 1: entrenando la cabeza ==", flush=True)
    model.fit(ds_tr, validation_data=ds_va, epochs=args.epochs1, verbose=2)

    # Fase 2: ajuste fino de los últimos bloques
    set_trainable(model, "block_13_expand")
    model.compile(optimizer=keras.optimizers.Adam(5e-5), loss=loss, metrics=["accuracy"])
    print("== Fase 2: ajuste fino ==", flush=True)
    cbs = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=1, min_lr=1e-6),
    ]
    model.fit(ds_tr, validation_data=ds_va, epochs=args.epochs2, callbacks=cbs, verbose=2)

    # Calibración (temperature scaling) con validación
    lg_va = model.predict(ds_va, verbose=0)
    T = fit_temperature(lg_va, y[val])
    print(f"temperatura T = {T:.2f}", flush=True)

    # Modelo final: logits -> /T -> softmax
    probs_layer = keras.layers.Softmax(name="probabilidades")(keras.layers.Rescaling(1.0 / T, name="temperatura")(model.output))
    final = keras.Model(model.input, probs_layer)

    # Evaluación sobre lesiones nunca vistas
    lg_te = model.predict(ds_te, verbose=0)
    metrics, decision = build_report(softmax(lg_va / T), y[val], softmax(lg_te / T), y[test], meta.iloc[test], args.target_sens)
    info = {"version": args.version, "T": T, "n_total": int(len(X)), "n_lesiones": int(meta.lesion_id.nunique())}
    metrics["_info"] = {**info, "clases": CLASS_NAMES, "entrenamiento_segundos": int(time.time() - t0), "limit": args.limit,
                        "dedupe": not args.keep_duplicates, "decision": decision}

    final.save(out)
    with open(os.path.join(os.path.dirname(out), "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    write_card(os.path.join(os.path.dirname(out), "MODEL_CARD.md"), metrics, info)

    print("\n== RESULTADOS (prueba) ==", flush=True)
    for k in ("accuracy", "accuracy_balanceada", "sensibilidad_maligno", "sensibilidad_maligno_o_sospechoso", "especificidad_benigno", "auc_ovr_macro"):
        print(f"  {k}: {metrics[k]:.3f}", flush=True)
    print("  matriz de confusión:", metrics["matriz_confusion_filas_real_columnas_predicho"], flush=True)
    s = metrics["regla_screening"]
    print(f"== Regla de cribado (tm={decision['tm']}, tn={decision['tn']}) ==", flush=True)
    for k in ("sensibilidad_maligno_o_sospechoso", "sensibilidad_maligno", "especificidad_benigno", "accuracy_balanceada"):
        print(f"  {k}: {s[k]:.3f}", flush=True)
    print("  matriz de confusión:", s["matriz_confusion_filas_real_columnas_predicho"], flush=True)
    print(f"Modelo guardado en {out}  ({(time.time() - t0) / 60:.1f} min)", flush=True)


if __name__ == "__main__":
    main()
