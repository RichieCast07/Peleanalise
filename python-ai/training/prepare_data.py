"""
Descarga HAM10000 (espejo de Hugging Face: marmal88/skin_cancer) y lo deja listo para entrenar.

Cada archivo parquet se descarga, se reduce a 224x224 RGB (igual que el preprocesado de
app/services/ai_model.py), se guarda en un shard .npy y el parquet original se BORRA.
Así el disco necesario es ~1.5 GB en lugar de ~3.5 GB.

Uso:  python training/prepare_data.py [--data-dir RUTA]
"""

import argparse
import io
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from PIL import Image

IMG_SIZE = 224
BASE_URL = "https://huggingface.co/datasets/marmal88/skin_cancer/resolve/main/data/"
FILES = [
    "test-00000-of-00001-61e7cf54bf274ae2.parquet",
    "validation-00000-of-00002-9cc6b2a1db12d1a6.parquet",
    "validation-00001-of-00002-900252bc4d7798ec.parquet",
    "train-00000-of-00005-7eed077f2f8e6d15.parquet",
    "train-00001-of-00005-50ba64fd20294ba8.parquet",
    "train-00002-of-00005-36c02a25cbdd5481.parquet",
    "train-00003-of-00005-27da80cf1cb2598d.parquet",
    "train-00004-of-00005-264fb0c337457a9b.parquet",
]


def download(url: str, dest: str) -> None:
    for attempt in range(1, 6):
        r = subprocess.run(["curl.exe", "-sSL", "-C", "-", "--retry", "5", "-o", dest, url])
        if r.returncode == 0 and os.path.exists(dest):
            return
        print(f"  reintento {attempt}/5 ...", flush=True)
        time.sleep(5)
    sys.exit(f"No se pudo descargar {url}")


def process(parquet_path: str, out_prefix: str) -> int:
    pf = pq.ParquetFile(parquet_path)
    n = pf.metadata.num_rows
    X = np.zeros((n, IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    rows, i = [], 0
    for batch in pf.iter_batches(batch_size=128):
        for r in batch.to_pylist():
            img = Image.open(io.BytesIO(r["image"]["bytes"])).convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
            X[i] = np.asarray(img)
            rows.append({"image_id": r["image_id"], "lesion_id": r["lesion_id"], "dx": r["dx"]})
            i += 1
    np.save(out_prefix + "_X.npy", X[:i])
    pd.DataFrame(rows).to_csv(out_prefix + "_meta.csv", index=False)
    return i


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.expanduser("~"), "pele_data", "ham10000"))
    args = ap.parse_args()

    shards = os.path.join(args.data_dir, "shards")
    os.makedirs(shards, exist_ok=True)

    total = 0
    for k, name in enumerate(FILES):
        prefix = os.path.join(shards, f"shard{k}")
        if os.path.exists(prefix + "_X.npy") and os.path.exists(prefix + "_meta.csv"):
            print(f"[{k + 1}/{len(FILES)}] {name}: ya procesado", flush=True)
            continue
        tmp = os.path.join(args.data_dir, "tmp.parquet")
        print(f"[{k + 1}/{len(FILES)}] descargando {name} ...", flush=True)
        download(BASE_URL + name, tmp)
        print("  procesando imagenes ...", flush=True)
        n = process(tmp, prefix)
        os.remove(tmp)
        total += n
        print(f"  listo: {n} imagenes", flush=True)

    print("Preparacion terminada.", flush=True)


if __name__ == "__main__":
    main()
