"""E08 - Estadísticas trazables del dataset, k-anonimato y cobertura del inventario.

Genera:
  reports/e08/dataset_stats.json   cifras que cita docs/DATASET_CARD.md
  reports/e08/minimizacion_kanon.csv   k-anonimato con y sin generalizar la fecha
Falla (código de salida 1) si el inventario no cubre exactamente las columnas del archivo.

Uso:  uv run python scripts/e08_inventario.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from inf8239_u04.data import PROHIBITED, load_data, temporal_split
from inf8239_u04.e08_ops import generalize_dates, k_anonymity, sha256_file

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path("data/territorial_risk_synthetic.csv")
INVENTORY = Path("docs/INVENTARIO_DATOS.csv")
OUT = Path("reports/e08")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_data(str(DATA))
    train, test = temporal_split(df)

    by_group = df.groupby("protected_group").agg(n=("target", "size"), target_rate=("target", "mean"))
    stats = {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "columns": list(pd.read_csv(DATA, nrows=0).columns),
        "date_min": str(df.received_date.min().date()),
        "date_max": str(df.received_date.max().date()),
        "duplicated_case_id": int(df.case_id.duplicated().sum()),
        "missing_cells": int(df.isna().sum().sum()),
        "direct_identifier_columns_found": sorted(PROHIBITED & {c.lower() for c in df.columns}),
        "target_rate": round(float(df.target.mean()), 4),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "test_start": str(test.received_date.min().date()),
        "groups": {g: {"n": int(r.n), "target_rate": round(float(r.target_rate), 4)} for g, r in by_group.iterrows()},
        "data_sha256": sha256_file(DATA),
        "data_sha256_note": "Hash SHA-256 con los saltos de línea normalizados a LF (igual en Windows y Linux).",
    }
    (OUT / "dataset_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")

    quasi = ["zone", "age_band", "protected_group"]
    frame = df.assign(received_month=generalize_dates(df.received_date, "M"), received_quarter=generalize_dates(df.received_date, "Q"),
                      received_year=generalize_dates(df.received_date, "Y"), received_date_exact=df.received_date.astype(str))
    rows = []
    for name, cols in {
        "zona + edad + grupo": quasi,
        "zona + edad + grupo + fecha exacta": quasi + ["received_date_exact"],
        "zona + edad + grupo + mes": quasi + ["received_month"],
        "zona + edad + grupo + trimestre": quasi + ["received_quarter"],
        "zona + edad + grupo + año": quasi + ["received_year"],
    }.items():
        info = k_anonymity(frame, cols)
        rows.append({"cuasi_identificadores": name, "grupos": info["n_groups"], "k_minimo": info["min_k"],
                     "filas_en_grupos_menores_a_5": info["rows_in_groups_below_k"],
                     "porcentaje_filas_menores_a_5": round(100 * info["share_rows_below_k"], 1)})
    kanon = pd.DataFrame(rows)
    kanon.to_csv(OUT / "minimizacion_kanon.csv", index=False, encoding="utf-8")

    print("=== Dataset ===")
    for key in ("n_rows", "date_min", "date_max", "n_train", "n_test", "test_start", "target_rate", "groups", "missing_cells", "duplicated_case_id"):
        print(f"{key}: {stats[key]}")
    print("\n=== k-anonimato (k=5) ===")
    print(kanon.to_string(index=False))

    inventory = pd.read_csv(INVENTORY)
    in_file = set(stats["columns"])
    inventoried = set(inventory.loc[inventory.kind == "column", "asset"])
    missing, extra = sorted(in_file - inventoried), sorted(inventoried - in_file)
    print("\n=== Inventario ===")
    print(f"columnas del archivo: {len(in_file)} | inventariadas: {len(inventoried)}")
    if missing or extra:
        print(f"FALTAN en el inventario: {missing} | SOBRAN: {extra}")
        return 1
    print("El inventario cubre exactamente las columnas del archivo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
