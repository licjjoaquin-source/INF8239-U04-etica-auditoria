"""Pruebas de las herramientas operativas del E08 (monitoreo, minimización, evidencia)."""
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from inf8239_u04.data import features, load_data, temporal_split
from inf8239_u04.e08_ops import (
    build_manifest,
    capacity_recall,
    drift_table,
    evaluate_signals,
    inject_field_loss,
    k_anonymity,
    load_monitoring,
    overall_status,
    performance,
    psi_categorical,
    psi_numeric,
    share_shift,
    triggered,
    verify_manifest,
)
from inf8239_u04.governance import load_config
from inf8239_u04.model import build_model

GATES = load_config()["gates"]
MON = load_monitoring()


def _perf(n_per_group=40):
    rng = np.random.default_rng(0)
    groups = np.array(["G1"] * n_per_group + ["G2"] * n_per_group)
    y = np.tile([1, 0], n_per_group)
    pred = np.where(rng.random(len(y)) < 0.5, y, 1 - y)
    return performance(y, pred, groups)


def _signals(perf, schema_ok=True, shift=0.0, latency=1.0, kb=5.0):
    ref = pd.DataFrame({"previous_incidents": [1, 2, 3, 4] * 10, "infrastructure_score": np.linspace(0, 1, 40),
                        "exposure": np.linspace(0, 1, 40), "zone": ["Sur", "Norte"] * 20})
    d = MON["signals"]["drift_psi"]
    drift = drift_table(ref, ref, d["numeric"], d["categorical"], d["watch"], d["alert"], d["bins"])
    zero = {"reference_share": 0.05, "current_share": 0.05 + shift, "shift": shift}
    return evaluate_signals(MON, GATES, schema_ok=schema_ok, drift=drift, zero_shift=zero, perf=perf, latency_ms=latency, model_kb=kb)


def test_psi_is_zero_for_identical_and_large_for_shifted_distributions():
    x = np.random.default_rng(1).normal(size=400)
    assert psi_numeric(x, x) < 1e-9
    assert psi_numeric(x, x + 2.0) > 0.25
    assert psi_categorical(["a"] * 50 + ["b"] * 50, ["a"] * 50 + ["b"] * 50) < 1e-9
    assert psi_categorical(["a"] * 90 + ["b"] * 10, ["a"] * 10 + ["b"] * 90) > 0.25


def test_psi_handles_constant_reference_without_failing():
    assert psi_numeric([1, 1, 1, 1], [1, 2, 3, 4]) == 0.0


def test_share_shift_detects_field_that_arrives_empty():
    ref = pd.Series([1, 2, 3, 0, 4, 5, 2, 3, 1, 2])
    cur = ref.copy()
    cur[:] = 0
    shift = share_shift(ref, cur, 0)
    assert abs(shift["shift"] - 0.9) < 1e-9


def test_k_anonymity_counts_the_smallest_group():
    df = pd.DataFrame({"a": ["x", "x", "x", "y", "y", "z"], "b": [1, 1, 1, 1, 1, 1]})
    info = k_anonymity(df, ["a", "b"], k=2)
    assert info["min_k"] == 1 and info["n_groups"] == 3
    assert info["rows_in_groups_below_k"] == 1


def test_gap_without_support_is_reported_as_missing_evidence_not_ok():
    y = np.array([1] * 12 + [0] * 12 + [1] * 3 + [0] * 3)
    groups = np.array(["G1"] * 24 + ["G2"] * 6)
    perf = performance(y, y, groups)  # G2 no alcanza el soporte mínimo
    assert perf["gap_evidence"] == "insuficiente" and perf["recall_gap"] is None
    signals = _signals(perf)
    gap_signals = [s for s in signals if s["signal"] in {"recall_gap", "fpr_gap"}]
    assert {s["status"] for s in gap_signals} == {"SIN_EVIDENCIA"}
    assert overall_status(signals) == "WATCH", "la falta de evidencia nunca puede resumirse como GO"


def test_supported_gap_above_tolerance_triggers_review():
    n = 30
    y = np.array([1, 0] * n + [1, 0] * n)
    groups = np.array(["G1"] * (2 * n) + ["G2"] * (2 * n))
    pred = np.concatenate([y[: 2 * n], np.zeros(2 * n, dtype=int)])  # G2 nunca se prioriza
    perf = performance(y, pred, groups)
    assert perf["gap_evidence"] == "suficiente" and perf["recall_gap"] > GATES["max_recall_gap"]
    signals = _signals(perf)
    assert overall_status(signals) == "REVIEW"
    assert any(s["signal"] == "recall_gap" for s in triggered(signals))


def test_schema_violation_stops_the_system():
    perf = performance(np.array([1, 0] * 30), np.array([1, 0] * 30), np.array(["G1", "G2"] * 30))
    assert overall_status(_signals(perf, schema_ok=False)) == "STOP"


def test_zero_share_shift_triggers_review():
    perf = performance(np.array([1, 0] * 30), np.array([1, 0] * 30), np.array(["G1", "G2"] * 30))
    signals = _signals(perf, shift=0.4)
    assert any(s["signal"].startswith("zero_share_shift") and s["status"] == "REVIEW" for s in signals)


def test_every_signal_has_owner_threshold_and_runbook_step():
    perf = _perf()
    for s in _signals(perf):
        assert s["owner"] and s["threshold"] != "" and s["runbook_step"] != ""


def test_manifest_detects_changes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("uno", encoding="utf-8")
        (root / "b.txt").write_text("dos", encoding="utf-8")
        manifest = build_manifest(["a.txt", "b.txt"], root)
        assert verify_manifest(manifest, root) == []
        (root / "b.txt").write_text("dos modificado", encoding="utf-8")
        assert verify_manifest(manifest, root) == ["b.txt"]
        with pytest.raises(FileNotFoundError):
            build_manifest(["no_existe.txt"], root)
        json.dumps(manifest)  # serializable


def test_inject_field_loss_changes_only_the_target_group():
    df = pd.DataFrame({"protected_group": ["G1", "G2", "G2"], "previous_incidents": [3, 4, 5]})
    out = inject_field_loss(df, "protected_group", "G2", "previous_incidents", 0)
    assert out.previous_incidents.tolist() == [3, 0, 0]
    assert df.previous_incidents.tolist() == [3, 4, 5], "no debe modificar el original"


def test_capacity_recall_uses_arrival_order():
    df = pd.DataFrame({"target": [1, 0, 1, 0, 0, 1]})
    assert abs(capacity_recall(df, "target", 0.5) - 2 / 3) < 1e-9


def test_model_without_age_band_trains_and_ignores_it():
    train, test = temporal_split(load_data())
    X = features(train, ("age_band",))
    assert "age_band" not in X.columns
    model = build_model("logistic", ("age_band",)).fit(X, train.target)
    changed = test.assign(age_band="60+")
    assert (model.predict(features(test, ("age_band",))) == model.predict(features(changed, ("age_band",)))).all()
    with pytest.raises(ValueError):
        features(train, ("no_existe",))


def test_default_model_is_unchanged_by_the_drop_option():
    train, test = temporal_split(load_data())
    base = build_model("logistic").fit(features(train), train.target)
    same = build_model("logistic", ()).fit(features(train, ()), train.target)
    assert (base.predict(features(test)) == same.predict(features(test, ()))).all()
