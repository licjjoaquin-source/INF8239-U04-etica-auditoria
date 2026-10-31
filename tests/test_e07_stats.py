import numpy as np
import pytest

from inf8239_u04.e07_stats import (
    bootstrap_difference,
    confusion_rates,
    cramers_v,
    gap_status,
    group_table,
    threshold_sweep,
    wilson_interval,
)


def test_confusion_rates_known_values():
    r = confusion_rates([1, 1, 0, 0, 0], [1, 0, 1, 0, 0])
    assert r["recall"] == 0.5 and abs(r["fpr"] - 1 / 3) < 1e-12 and r["selection_rate"] == 0.4
    assert r["positives"] == 2 and r["negatives"] == 3


def test_rates_without_base_are_nan_not_zero():
    r = confusion_rates([0, 0], [1, 0])
    assert np.isnan(r["recall"])


def test_wilson_interval_contains_proportion_and_is_bounded():
    lo, hi = wilson_interval(8, 10)
    assert 0 <= lo < 0.8 < hi <= 1
    assert np.isnan(wilson_interval(0, 0)[0])


def test_group_table_flags_small_groups():
    y = np.array([1, 0] * 30 + [1, 0, 1])
    p = np.array([1, 0] * 30 + [1, 1, 0])
    g = np.array(["A"] * 60 + ["B"] * 3)
    table = group_table(y, p, g, min_n=20).set_index("group")
    assert bool(table.loc["A", "support_ok"]) is True
    assert bool(table.loc["B", "support_ok"]) is False
    assert "n<20" in table.loc["B", "support_note"]


def test_group_table_requires_positives_and_negatives_not_only_n():
    y = np.array([1] * 30)  # 30 casos, pero ningún negativo: la FPR no existe
    table = group_table(y, y, np.array(["A"] * 30), min_n=20)
    assert bool(table.loc[0, "support_ok"]) is False
    assert "negativos" in table.loc[0, "support_note"]


def test_bootstrap_difference_is_reproducible_and_brackets_point():
    rng = np.random.default_rng(0)
    g = np.array(["A"] * 100 + ["B"] * 80)
    y = rng.integers(0, 2, 180)
    p = np.where(rng.random(180) < 0.8, y, 1 - y)
    first = bootstrap_difference(y, p, g, "A", "B", "recall", n_boot=300, seed=1)
    second = bootstrap_difference(y, p, g, "A", "B", "recall", n_boot=300, seed=1)
    assert first == second
    assert first["lo"] <= first["difference"] <= first["hi"]


def test_bootstrap_rejects_unknown_metric_and_missing_group():
    with pytest.raises(ValueError):
        bootstrap_difference([1, 0], [1, 0], ["A", "B"], "A", "B", "magia")
    with pytest.raises(ValueError):
        bootstrap_difference([1, 0], [1, 0], ["A", "B"], "A", "Z", "recall")


def test_gap_status_three_outcomes():
    assert gap_status(0.20, 0.05, 0.35, 0.16) == "supera la tolerancia"
    assert gap_status(0.10, -0.05, 0.25, 0.16).startswith("incierto")
    assert gap_status(0.05, -0.02, 0.10, 0.16) == "dentro de la tolerancia"


def test_threshold_sweep_monotone_selection():
    rng = np.random.default_rng(3)
    scores = rng.random(200)
    y = (scores + rng.normal(0, 0.2, 200) > 0.5).astype(int)
    g = np.array(["A", "B"] * 100)
    table = threshold_sweep(y, scores, g, "A", "B", [0.3, 0.5, 0.7])
    assert list(table.threshold) == [0.3, 0.5, 0.7]
    assert table.selection_rate.is_monotonic_decreasing


def test_cramers_v_bounds():
    same = np.array(["a", "b"] * 50)
    assert abs(cramers_v(same, same) - 1.0) < 1e-9
    rng = np.random.default_rng(5)
    assert cramers_v(rng.choice(["x", "y", "z"], 400), rng.choice(["u", "v"], 400)) < 0.2
    assert cramers_v(["a"] * 10, ["u"] * 10) == 0.0
