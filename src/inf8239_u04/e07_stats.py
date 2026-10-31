"""Estadística de apoyo para la auditoría de equidad del E07 (solo NumPy y pandas).

Complementa a `fairness.py` (Fairlearn): añade soporte por grupo, intervalos de
incertidumbre, comparación contra una tolerancia y chequeo de variables proxy.
Las cifras puntuales coinciden con las de Fairlearn; lo nuevo es la incertidumbre.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

METRIC_NAMES = ("selection_rate", "recall", "fpr")


def confusion_rates(y_true, y_pred) -> dict:
    """Conteos y tasas de una predicción binaria. Tasas sin base = NaN (no 0)."""
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    if y_true.shape != y_pred.shape:
        raise ValueError("y_true y y_pred deben tener la misma forma")
    n = int(len(y_true))
    positives = int((y_true == 1).sum())
    negatives = n - positives
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    return {
        "n": n, "positives": positives, "negatives": negatives, "tp": tp, "fp": fp,
        "selected": int((y_pred == 1).sum()),
        "accuracy": float((y_true == y_pred).mean()) if n else float("nan"),
        "selection_rate": float(y_pred.mean()) if n else float("nan"),
        "recall": tp / positives if positives else float("nan"),
        "fpr": fp / negatives if negatives else float("nan"),
    }


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson al 95 % para una proporción k/n."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    denominator = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denominator
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denominator
    return (float(max(0.0, center - half)), float(min(1.0, center + half)))


def group_table(y_true, y_pred, groups, min_n: int = 20, min_positives: int = 10, min_negatives: int = 10) -> pd.DataFrame:
    """Tabla por grupo con conteos, tasas, intervalos de Wilson y bandera de soporte.

    Un grupo tiene soporte suficiente solo si tiene al menos `min_n` casos y también
    `min_positives` positivos y `min_negatives` negativos: el recall se calcula sobre
    los positivos y la FPR sobre los negativos, que son menos que el total.
    """
    frame = pd.DataFrame({"y": np.asarray(y_true).astype(int), "p": np.asarray(y_pred).astype(int),
                          "g": np.asarray(groups).astype(str)})
    rows = []
    for name, part in frame.groupby("g", sort=True):
        r = confusion_rates(part.y, part.p)
        reasons = []
        if r["n"] < min_n:
            reasons.append(f"n<{min_n}")
        if r["positives"] < min_positives:
            reasons.append(f"positivos<{min_positives}")
        if r["negatives"] < min_negatives:
            reasons.append(f"negativos<{min_negatives}")
        rec_lo, rec_hi = wilson_interval(r["tp"], r["positives"])
        fpr_lo, fpr_hi = wilson_interval(r["fp"], r["negatives"])
        sel_lo, sel_hi = wilson_interval(r["selected"], r["n"])
        rows.append({
            "group": name, "n": r["n"], "positives": r["positives"], "negatives": r["negatives"],
            "selection_rate": r["selection_rate"], "selection_lo": sel_lo, "selection_hi": sel_hi,
            "recall": r["recall"], "recall_lo": rec_lo, "recall_hi": rec_hi,
            "fpr": r["fpr"], "fpr_lo": fpr_lo, "fpr_hi": fpr_hi,
            "support_ok": not reasons, "support_note": "; ".join(reasons) if reasons else "suficiente",
        })
    return pd.DataFrame(rows)


def bootstrap_difference(y_true, y_pred, groups, group_a: str, group_b: str, metric: str,
                         n_boot: int = 2000, seed: int = 42) -> dict:
    """Diferencia (b − a) de una métrica con IC al 95 % por bootstrap estratificado por grupo."""
    if metric not in METRIC_NAMES:
        raise ValueError(f"métrica desconocida: {metric}")
    frame = pd.DataFrame({"y": np.asarray(y_true).astype(int), "p": np.asarray(y_pred).astype(int),
                          "g": np.asarray(groups).astype(str)})
    parts = {name: frame[frame.g == name][["y", "p"]].to_numpy() for name in (group_a, group_b)}
    for name, values in parts.items():
        if len(values) == 0:
            raise ValueError(f"grupo sin observaciones: {name}")
    point = confusion_rates(*parts[group_b].T)[metric] - confusion_rates(*parts[group_a].T)[metric]
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        values = []
        for name in (group_a, group_b):
            data = parts[name]
            sample = data[rng.integers(0, len(data), len(data))]
            values.append(confusion_rates(sample[:, 0], sample[:, 1])[metric])
        draws.append(values[1] - values[0])
    draws = np.asarray(draws, dtype=float)
    draws = draws[~np.isnan(draws)]
    if len(draws) == 0:
        return {"metric": metric, "difference": float(point), "lo": float("nan"), "hi": float("nan"), "n_boot": 0}
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"metric": metric, "difference": float(point), "lo": float(lo), "hi": float(hi), "n_boot": int(len(draws))}


def gap_status(difference: float, lo: float, hi: float, tolerance: float) -> str:
    """Compara una brecha con la tolerancia considerando su incertidumbre."""
    if np.isnan(difference) or np.isnan(lo) or np.isnan(hi):
        return "sin dato"
    if abs(difference) > tolerance:
        return "supera la tolerancia"
    if max(abs(lo), abs(hi)) > tolerance:
        return "incierto: el IC cruza la tolerancia"
    return "dentro de la tolerancia"


def threshold_sweep(y_true, scores, groups, group_a: str, group_b: str, thresholds) -> pd.DataFrame:
    """Efecto de mover el umbral de decisión sobre utilidad y brechas (b − a)."""
    y_true = np.asarray(y_true).astype(int)
    scores = np.asarray(scores, dtype=float)
    groups = np.asarray(groups).astype(str)
    rows = []
    for threshold in thresholds:
        pred = (scores >= threshold).astype(int)
        overall = confusion_rates(y_true, pred)
        a = confusion_rates(y_true[groups == group_a], pred[groups == group_a])
        b = confusion_rates(y_true[groups == group_b], pred[groups == group_b])
        rows.append({
            "threshold": float(threshold), "accuracy": overall["accuracy"], "recall": overall["recall"],
            "fpr": overall["fpr"], "selection_rate": overall["selection_rate"],
            "recall_gap": abs(b["recall"] - a["recall"]), "fpr_gap": abs(b["fpr"] - a["fpr"]),
            "selection_gap": abs(b["selection_rate"] - a["selection_rate"]),
        })
    return pd.DataFrame(rows)


def cramers_v(a, b) -> float:
    """Asociación entre dos variables categóricas (0 = ninguna, 1 = total)."""
    table = pd.crosstab(pd.Series(np.asarray(a)), pd.Series(np.asarray(b))).to_numpy().astype(float)
    if min(table.shape) < 2:
        return 0.0
    total = table.sum()
    expected = np.outer(table.sum(axis=1), table.sum(axis=0)) / total
    chi2 = float(((table - expected) ** 2 / expected).sum())
    return float(np.sqrt(chi2 / (total * (min(table.shape) - 1))))
