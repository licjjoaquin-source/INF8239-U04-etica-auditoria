"""Herramientas operativas del E08 (NumPy, pandas y PyYAML; sin Fairlearn).

Cubren cuatro necesidades del expediente de gobernanza:
  * minimización: k-anonimato de los cuasi-identificadores y generalización de fechas;
  * monitoreo: deriva (PSI), cambio en la proporción de ceros, rendimiento con soporte;
  * decisión operativa: convierte señales en GO / WATCH / REVIEW / STOP con dueño y paso del runbook;
  * preservación de evidencia: manifiesto con hashes SHA-256.

Regla de diseño: la falta de evidencia nunca se reporta como "todo bien". Un grupo sin
soporte suficiente produce SIN_EVIDENCIA, que se trata como WATCH.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .e07_stats import confusion_rates, group_table, wilson_interval

SEVERITY_ORDER = {"GO": 0, "WATCH": 1, "REVIEW": 2, "STOP": 3}


def load_monitoring(path: str | Path = "configs/monitoring.yml") -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- minimización
def k_anonymity(df: pd.DataFrame, columns: list[str], k: int = 5) -> dict:
    """Tamaño del grupo más pequeño que comparten los cuasi-identificadores `columns`.

    min_k = 1 significa que al menos un registro es único con esas columnas.
    """
    sizes = df.groupby(list(columns), observed=True).size()
    below = int(sizes[sizes < k].sum())
    return {
        "columns": list(columns),
        "n_rows": int(len(df)),
        "n_groups": int(len(sizes)),
        "min_k": int(sizes.min()),
        "rows_in_groups_below_k": below,
        "share_rows_below_k": float(below / len(df)) if len(df) else float("nan"),
        "k": int(k),
    }


def generalize_dates(series: pd.Series, freq: str = "M") -> pd.Series:
    """Reduce la precisión de una fecha (por defecto, a mes) para bajar la unicidad."""
    return pd.to_datetime(series).dt.to_period(freq).astype(str)


# ----------------------------------------------------------------------------- deriva
def _shares(counts: np.ndarray, eps: float) -> np.ndarray:
    total = counts.sum()
    shares = counts / total if total else np.zeros_like(counts, dtype=float)
    return np.clip(shares, eps, None)


def psi_numeric(reference, current, bins: int = 5, eps: float = 1e-4) -> float:
    """Population Stability Index con cortes por cuantiles de la referencia."""
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)
    cuts = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1))[1:-1])
    if len(cuts) == 0:  # referencia casi constante: no hay cómo comparar
        return 0.0
    ref_counts = np.bincount(np.searchsorted(cuts, ref, side="right"), minlength=len(cuts) + 1)
    cur_counts = np.bincount(np.searchsorted(cuts, cur, side="right"), minlength=len(cuts) + 1)
    p, q = _shares(ref_counts.astype(float), eps), _shares(cur_counts.astype(float), eps)
    return float(np.sum((q - p) * np.log(q / p)))


def psi_categorical(reference, current, eps: float = 1e-4) -> float:
    ref = pd.Series(reference).astype(str)
    cur = pd.Series(current).astype(str)
    cats = sorted(set(ref) | set(cur))
    p = _shares(np.array([(ref == c).sum() for c in cats], dtype=float), eps)
    q = _shares(np.array([(cur == c).sum() for c in cats], dtype=float), eps)
    return float(np.sum((q - p) * np.log(q / p)))


def psi_status(value: float, watch: float, alert: float) -> str:
    if value >= alert:
        return "ALERT"
    if value >= watch:
        return "WATCH"
    return "OK"


def drift_table(reference: pd.DataFrame, current: pd.DataFrame, numeric: list[str],
                categorical: list[str], watch: float = 0.10, alert: float = 0.25, bins: int = 5) -> pd.DataFrame:
    rows = []
    for col in numeric:
        value = psi_numeric(reference[col], current[col], bins=bins)
        rows.append({"feature": col, "kind": "numeric", "psi": value, "status": psi_status(value, watch, alert)})
    for col in categorical:
        value = psi_categorical(reference[col], current[col])
        rows.append({"feature": col, "kind": "categorical", "psi": value, "status": psi_status(value, watch, alert)})
    return pd.DataFrame(rows)


def share_shift(reference, current, value=0) -> dict:
    """Cambio en la proporción de registros que valen `value` (detecta campos que llegan vacíos o en cero)."""
    ref_share = float((pd.Series(reference) == value).mean())
    cur_share = float((pd.Series(current) == value).mean())
    return {"reference_share": ref_share, "current_share": cur_share, "shift": cur_share - ref_share}


# ----------------------------------------------------------------------------- rendimiento
def performance(y_true, y_pred, groups, group_a: str = "G1", group_b: str = "G2",
                min_n: int = 20, min_positives: int = 10, min_negatives: int = 10) -> dict:
    """Métricas globales y brechas, calculadas solo con grupos que tienen soporte."""
    overall = confusion_rates(y_true, y_pred)
    overall["recall_ci"] = wilson_interval(overall["tp"], overall["positives"]) if overall["positives"] else (float("nan"), float("nan"))
    table = group_table(y_true, y_pred, groups, min_n=min_n, min_positives=min_positives, min_negatives=min_negatives)
    supported = table.set_index("group").support_ok
    both = bool(supported.get(group_a, False) and supported.get(group_b, False))
    out = {"overall": overall, "groups": table, "gap_evidence": "suficiente" if both else "insuficiente",
           "recall_gap": None, "fpr_gap": None}
    if both:
        t = table.set_index("group")
        out["recall_gap"] = float(abs(t.loc[group_b, "recall"] - t.loc[group_a, "recall"]))
        out["fpr_gap"] = float(abs(t.loc[group_b, "fpr"] - t.loc[group_a, "fpr"]))
    return out


def capacity_recall(frame_in_time_order: pd.DataFrame, target_col: str, capacity_fraction: float) -> float:
    """Recall de la línea base manual: se revisan los primeros casos por orden de llegada, sin puntaje."""
    n = len(frame_in_time_order)
    k = int(math.ceil(capacity_fraction * n))
    positives = frame_in_time_order[target_col].sum()
    return float(frame_in_time_order[target_col].iloc[:k].sum() / positives) if positives else float("nan")


# ----------------------------------------------------------------------------- decisión operativa
def _signal(cfg: dict, name: str, value, threshold, status: str, detail: str = "") -> dict:
    return {
        "signal": name,
        "value": None if value is None else (round(float(value), 4) if isinstance(value, (int, float, np.floating)) else value),
        "threshold": threshold,
        "status": status,
        "owner": cfg.get("owner", ""),
        "runbook_step": cfg.get("runbook_step", ""),
        "detail": detail,
    }


def evaluate_signals(monitoring: dict, gates: dict, *, schema_ok: bool, drift: pd.DataFrame,
                     zero_shift: dict, perf: dict, latency_ms: float, model_kb: float) -> list[dict]:
    """Convierte mediciones en señales con estado. Estados: OK, WATCH, REVIEW, STOP, SIN_EVIDENCIA."""
    cfg = monitoring["signals"]
    out: list[dict] = []

    c = cfg["data_contract"]
    out.append(_signal(c, "data_contract", int(not schema_ok), 0, "OK" if schema_ok else c["severity"],
                       "columnas requeridas presentes y sin identificadores directos" if schema_ok else "esquema inválido o identificador directo"))

    c = cfg["drift_psi"]
    for _, row in drift.iterrows():
        status = {"ALERT": c["alert_severity"], "WATCH": "WATCH", "OK": "OK"}[row.status]
        out.append(_signal(c, f"drift_psi:{row.feature}", row.psi, f"watch {c['watch']} / alert {c['alert']}", status))

    c = cfg["zero_share_shift"]
    status = c["alert_severity"] if abs(zero_shift["shift"]) >= c["alert"] else "OK"
    out.append(_signal(c, f"zero_share_shift:{c['feature']}", zero_shift["shift"], f"cambio absoluto < {c['alert']}", status,
                       f"proporción de ceros: referencia {zero_shift['reference_share']:.3f}, ahora {zero_shift['current_share']:.3f}"))

    overall = perf["overall"]
    c = cfg["recall"]
    if overall["positives"] < c["min_positives"]:
        out.append(_signal(c, "recall", overall["recall"], f">= {gates['min_recall']}", "SIN_EVIDENCIA",
                           f"solo {overall['positives']} positivos; mínimo {c['min_positives']}"))
    else:
        lo, hi = overall["recall_ci"]
        out.append(_signal(c, "recall", overall["recall"], f">= {gates['min_recall']}",
                           "OK" if overall["recall"] >= gates["min_recall"] else c["severity"],
                           f"IC 95 % del recall {lo:.2f} a {hi:.2f} con {overall['positives']} positivos; un valor puntual bajo con IC amplio puede ser ruido"))

    for name, gate_key in (("recall_gap", "max_recall_gap"), ("fpr_gap", "max_fpr_gap")):
        c = cfg[name]
        value = perf[name]
        if value is None:
            out.append(_signal(c, name, None, f"<= {gates[gate_key]}", "SIN_EVIDENCIA",
                               "algún grupo no alcanza el soporte mínimo; no se interpreta la brecha"))
        else:
            out.append(_signal(c, name, value, f"<= {gates[gate_key]}", "OK" if value <= gates[gate_key] else c["severity"]))

    c = cfg["latency"]
    out.append(_signal(c, "latency_ms", latency_ms, f"<= {gates['max_latency_ms']}", "OK" if latency_ms <= gates["max_latency_ms"] else c["severity"]))
    c = cfg["model_size"]
    out.append(_signal(c, "model_kb", model_kb, f"<= {gates['max_model_kb']}", "OK" if model_kb <= gates["max_model_kb"] else c["severity"]))
    return out


def overall_status(signals: list[dict]) -> str:
    """STOP > REVIEW > WATCH > GO. SIN_EVIDENCIA cuenta como WATCH: nunca como GO."""
    worst = 0
    for s in signals:
        status = "WATCH" if s["status"] == "SIN_EVIDENCIA" else s["status"]
        worst = max(worst, SEVERITY_ORDER.get(status, 0))
    return next(k for k, v in SEVERITY_ORDER.items() if v == worst)


def triggered(signals: list[dict]) -> list[dict]:
    return [s for s in signals if s["status"] in {"REVIEW", "STOP"}]


# ----------------------------------------------------------------------------- evidencia
TEXT_SUFFIXES = {".csv", ".yml", ".yaml", ".json", ".md", ".txt", ".py"}


def sha256_file(path: str | Path) -> str:
    """SHA-256 del contenido. En archivos de texto los saltos de línea se normalizan a LF para que el
    hash no cambie entre Windows (CRLF) y Linux (LF) al clonar el repositorio."""
    path = Path(path)
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def build_manifest(paths: list[str | Path], root: str | Path = ".") -> dict:
    """Manifiesto {ruta relativa: {sha256, bytes}}. Falla si falta un archivo (no se preserva lo que no existe)."""
    root = Path(root)
    manifest = {}
    for p in paths:
        full = root / p
        if not full.is_file():
            raise FileNotFoundError(f"No existe el archivo a preservar: {p}")
        manifest[str(Path(p).as_posix())] = {"sha256": sha256_file(full), "bytes": full.stat().st_size}
    return manifest


def verify_manifest(manifest: dict, root: str | Path = ".") -> list[str]:
    """Devuelve las rutas cuyo contenido cambió o ya no existe."""
    root = Path(root)
    bad = []
    for rel, info in manifest.items():
        full = root / rel
        if not full.is_file() or sha256_file(full) != info["sha256"]:
            bad.append(rel)
    return bad


def inject_field_loss(df: pd.DataFrame, group_col: str, group: str, column: str, value=0) -> pd.DataFrame:
    """Simula una falla de la fuente: el campo `column` llega con `value` para un subconjunto."""
    out = df.copy()
    out.loc[out[group_col] == group, column] = value
    return out
