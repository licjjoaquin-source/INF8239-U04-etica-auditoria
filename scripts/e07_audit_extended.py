"""E07 - Auditoría de equidad ampliada sobre el caso sintético del LAB12.

Qué añade al LAB12:
  * tres variantes: logistic (baseline), tree y logistic_sin_age (sin la edad como predictor);
  * soporte por grupo (casos, positivos, negativos) e intervalos de incertidumbre;
  * brechas con IC por bootstrap y comparación con las tolerancias de configs/governance.yml;
  * chequeo de variables proxy (zona y edad frente a protected_group);
  * barrido de umbral para ver el costo de reducir una brecha.

Uso (desde la carpeta del proyecto):
  uv run --with matplotlib python scripts/e07_audit_extended.py
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from inf8239_u04.data import features, load_data, temporal_split
from inf8239_u04.e07_stats import (
    bootstrap_difference,
    confusion_rates,
    cramers_v,
    gap_status,
    group_table,
    threshold_sweep,
)
from inf8239_u04.governance import deployment_decision, load_config

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = Path("reports/e07")
VARIANTS = {  # nombre: (tipo de modelo, columnas que se quitan de los predictores)
    "logistic": ("logistic", ()),
    "tree": ("tree", ()),
    "logistic_sin_age": ("logistic", ("age_band",)),
}


def build(kind: str, X: pd.DataFrame):
    """Mismo preprocesamiento e hiperparámetros que src/inf8239_u04/model.py."""
    categorical = [c for c in ("zone", "age_band") if c in X.columns]
    numeric = [c for c in X.columns if c not in categorical]
    prep = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
                              ("num", StandardScaler(), numeric)])
    if kind == "logistic":
        estimator = LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42)
    else:
        estimator = DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=42)
    return make_pipeline(prep, estimator)


def say(*parts) -> None:
    print(*parts, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-n", type=int, default=20, help="mínimo de casos por grupo para interpretar")
    parser.add_argument("--min-positives", type=int, default=10)
    parser.add_argument("--min-negatives", type=int, default=10)
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    config = load_config()
    gates = config["gates"]
    df = load_data()
    train, test = temporal_split(df)
    groups = sorted(test.protected_group.astype(str).unique())
    if len(groups) != 2:
        raise SystemExit(f"Se esperaban 2 grupos y hay {groups}")
    group_a, group_b = groups
    y_test = test.target.to_numpy()
    sensitive_used = sorted(set(config.get("sensitive_features", [])) & set(features(train).columns))
    say(f"Grupos comparados: {group_a} (referencia) y {group_b}. Diferencia = {group_b} − {group_a}.")
    say(f"Atributos sensibles declarados que SÍ entran como predictores: {sensitive_used or 'ninguno'}")

    summary_rows, models = [], {}
    for name, (kind, drop) in VARIANTS.items():
        X_train = features(train).drop(columns=list(drop))
        X_test = features(test).drop(columns=list(drop))
        model = build(kind, X_train)
        start = time.perf_counter()
        model.fit(X_train, train.target)
        seconds = time.perf_counter() - start
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.joblib"
            joblib.dump(model, path)
            size_kb = path.stat().st_size / 1024
        start = time.perf_counter()
        pred = model.predict(X_test)
        latency_ms = (time.perf_counter() - start) * 1000 / len(test)
        scores = model.predict_proba(X_test)[:, 1]
        models[name] = (model, X_test, scores)

        overall = confusion_rates(y_test, pred)
        table = group_table(y_test, pred, test.protected_group, args.min_n, args.min_positives, args.min_negatives)
        table.to_csv(OUT / f"group_support_{name}.csv", index=False)
        row = {"variant": name, "dropped_features": ",".join(drop) or "-", "n_test": overall["n"],
               "accuracy": overall["accuracy"], "recall": overall["recall"], "fpr": overall["fpr"],
               "selection_rate": overall["selection_rate"],
               "training_seconds": seconds, "model_kb": size_kb, "latency_ms": latency_ms}
        gaps = {}
        for metric in ("recall", "fpr", "selection_rate"):
            result = bootstrap_difference(y_test, pred, test.protected_group, group_a, group_b, metric,
                                          n_boot=args.n_boot, seed=args.seed)
            row[f"{metric}_diff"] = result["difference"]
            row[f"{metric}_ci_lo"], row[f"{metric}_ci_hi"] = result["lo"], result["hi"]
            gaps[metric] = abs(result["difference"])
            tolerance = {"recall": gates["max_recall_gap"], "fpr": gates["max_fpr_gap"]}.get(metric)
            row[f"{metric}_gap_status"] = (gap_status(result["difference"], result["lo"], result["hi"], tolerance)
                                           if tolerance is not None else "sin puerta definida")
        decision = deployment_decision({"recall": overall["recall"]},
                                       {"recall_gap": gaps["recall"], "fpr_gap": gaps["fpr"]},
                                       {"latency_ms": latency_ms, "model_kb": size_kb}, gates)
        row["gate_decision"] = decision["status"]
        row["gates_failed"] = ",".join(decision["failed"]) or "-"
        summary_rows.append(row)

        inter = group_table(y_test, pred, test.protected_group.astype(str) + " | " + test.age_band.astype(str),
                            args.min_n, args.min_positives, args.min_negatives)
        inter.to_csv(OUT / f"intersectional_support_{name}.csv", index=False)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "variants_summary.csv", index=False)

    # Soporte interseccional (baseline) y tasas base
    inter = pd.read_csv(OUT / "intersectional_support_logistic.csv")
    base = pd.concat([
        df.groupby("protected_group").target.agg(["count", "mean"]).assign(split="todo"),
        train.groupby("protected_group").target.agg(["count", "mean"]).assign(split="train"),
        test.groupby("protected_group").target.agg(["count", "mean"]).assign(split="test"),
    ]).reset_index().rename(columns={"mean": "target_rate", "count": "n"})
    base.to_csv(OUT / "base_rates.csv", index=False)

    # Chequeo de proxies: zona y edad frente al grupo protegido
    full = features(df)
    proxy = [{"check": "Cramer V: zone ~ protected_group", "value": cramers_v(df.zone, df.protected_group)},
             {"check": "Cramer V: age_band ~ protected_group", "value": cramers_v(df.age_band, df.protected_group)}]
    majority = float(df.protected_group.value_counts(normalize=True).max())
    cv = StratifiedKFold(5, shuffle=True, random_state=args.seed)
    predictive = float(cross_val_score(build("logistic", full), full, df.protected_group, cv=cv, scoring="accuracy").mean())
    proxy += [{"check": "Exactitud (CV 5) al predecir protected_group con los predictores", "value": predictive},
              {"check": "Exactitud de referencia (clase mayoritaria)", "value": majority}]
    pd.DataFrame(proxy).to_csv(OUT / "proxy_check.csv", index=False)

    # Barrido de umbral (baseline)
    thresholds = np.round(np.arange(0.30, 0.701, 0.05), 2)
    sweep = threshold_sweep(y_test, models["logistic"][2], test.protected_group, group_a, group_b, thresholds)
    sweep.to_csv(OUT / "threshold_sweep_logistic.csv", index=False)

    # Conciliación con los reportes del LAB12 (Fairlearn)
    reconciled = {}
    for name in ("logistic", "tree"):
        reference = Path(f"reports/lab12/{name}/fairness_by_group.csv")
        if reference.exists():
            ref = pd.read_csv(reference).set_index("protected_group")
            mine = pd.read_csv(OUT / f"group_support_{name}.csv").set_index("group")
            ok = all(abs(ref.loc[g, a] - mine.loc[g, b]) < 1e-9
                     for g in ref.index for a, b in (("recall", "recall"), ("fpr", "fpr"), ("selection_rate", "selection_rate")))
            reconciled[name] = bool(ok)
    figures = make_figures(summary, sweep, gates)

    info = {"groups": {"reference": group_a, "compared": group_b}, "gates": gates, "min_n": args.min_n,
            "min_positives": args.min_positives, "min_negatives": args.min_negatives, "n_boot": args.n_boot,
            "seed": args.seed, "sensitive_features_used_as_predictors": sensitive_used,
            "reconciled_with_lab12": reconciled, "figures": figures,
            "intersectional_cells": int(len(inter)), "intersectional_cells_with_support": int(inter.support_ok.sum()),
            "python": platform.python_version(), "scikit_learn": sklearn.__version__}
    (OUT / "e07_resumen.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    say("\n== Resumen por variante")
    say(summary[["variant", "accuracy", "recall", "fpr", "selection_rate", "recall_diff", "fpr_diff",
                 "selection_rate_diff", "gate_decision", "gates_failed", "model_kb"]].round(3).to_string(index=False))
    say("\n== Brechas con IC 95 % (baseline logistic)")
    first = summary[summary.variant == "logistic"].iloc[0]
    for metric in ("recall", "fpr", "selection_rate"):
        say(f"{metric:15s} {first[f'{metric}_diff']:+.3f}  IC [{first[f'{metric}_ci_lo']:+.3f}, {first[f'{metric}_ci_hi']:+.3f}]  -> {first[f'{metric}_gap_status']}")
    say("\n== Soporte interseccional (baseline)")
    say(inter[["group", "n", "positives", "negatives", "support_ok", "support_note"]].to_string(index=False))
    say("\n== Proxies")
    say(pd.DataFrame(proxy).round(3).to_string(index=False))
    say("\n== Conciliación con LAB12:", reconciled or "sin reportes LAB12 para comparar")
    say(f"\nArchivos en {OUT}/")


def make_figures(summary: pd.DataFrame, sweep: pd.DataFrame, gates: dict) -> list[str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no está instalado: se omiten las figuras (use: uv run --with matplotlib ...)")
        return []
    names = []
    # 1) Brechas con intervalos
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), sharey=True)
    labels = list(summary.variant)
    for axis, metric, tolerance, title in zip(
            axes, ("recall", "fpr", "selection_rate"),
            (gates["max_recall_gap"], gates["max_fpr_gap"], None),
            ("Brecha de recall", "Brecha de FPR", "Brecha de tasa de selección")):
        for position, (_, row) in enumerate(summary.iterrows()):
            point, lo, hi = row[f"{metric}_diff"], row[f"{metric}_ci_lo"], row[f"{metric}_ci_hi"]
            axis.errorbar(point, position, xerr=[[point - lo], [hi - point]], fmt="o", color="#1f4e79", capsize=3)
        axis.axvline(0, color="gray", linewidth=0.8)
        if tolerance is not None:
            for sign in (-1, 1):
                axis.axvline(sign * tolerance, color="#c0392b", linestyle="--", linewidth=1)
        axis.set_yticks(range(len(labels)))
        axis.set_yticklabels(labels, fontsize=8)
        axis.set_title(title + " (G2 − G1)", fontsize=9)
    fig.suptitle("Brechas con IC 95 % por bootstrap; línea roja = tolerancia de governance.yml", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "e07_brechas_ic.png", dpi=150)
    plt.close(fig)
    names.append("e07_brechas_ic.png")
    # 2) Utilidad frente a brecha
    fig, axis = plt.subplots(figsize=(6, 4))
    axis.plot(sweep.recall_gap, sweep.recall, "-o", color="#9aa5b1", label="logistic, umbral 0.30–0.70")
    for _, row in sweep.iterrows():
        axis.annotate(f"{row.threshold:.2f}", (row.recall_gap, row.recall), fontsize=6, xytext=(3, 3), textcoords="offset points")
    axis.scatter(summary.recall_diff.abs(), summary.recall, color="#1f4e79", zorder=3, label="variantes (umbral 0.5)")
    for _, row in summary.iterrows():
        axis.annotate(row.variant, (abs(row.recall_diff), row.recall), fontsize=7, xytext=(4, -9), textcoords="offset points")
    axis.axvline(gates["max_recall_gap"], color="#c0392b", linestyle="--", linewidth=1)
    axis.axhline(gates["min_recall"], color="#c0392b", linestyle=":", linewidth=1)
    axis.set_xlabel("Brecha de recall (valor absoluto)")
    axis.set_ylabel("Recall global")
    axis.set_title("Utilidad frente a brecha; rojo = puertas", fontsize=9)
    axis.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "e07_utilidad_vs_brecha.png", dpi=150)
    plt.close(fig)
    names.append("e07_utilidad_vs_brecha.png")
    return names


if __name__ == "__main__":
    main()
