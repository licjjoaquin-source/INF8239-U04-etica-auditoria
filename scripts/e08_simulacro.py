"""E08 - Simulacro de incidente: falla de una fuente de datos detectada por el monitoreo.

Escenario (inyectado a propósito, no es un hallazgo sobre datos reales):
  la fuente de un grupo deja de enviar `previous_incidents` y el campo llega en 0.
  Se comparan tres evaluaciones con los mismos umbrales de configs/monitoring.yml:
    A  operación normal         (primera mitad del periodo de prueba, sin falla)
    B  segunda mitad sin falla  (control: ¿el monitoreo da falsas alarmas?)
    C  segunda mitad con falla  (¿el monitoreo la detecta?)
  Si C activa REVIEW o STOP se ejecuta la respuesta: contención, preservación de evidencia,
  comunicación (borrador), reversión a la línea base manual, recuperación y postmortem.

Uso:  uv run --with matplotlib python scripts/e08_simulacro.py
Salidas en reports/lab13/simulacro/ y reports/lab13/INCIDENT_POSTMORTEM.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml

from inf8239_u04.data import features, load_data, temporal_split, validate_schema
from inf8239_u04.e08_ops import (
    build_manifest,
    capacity_recall,
    drift_table,
    evaluate_signals,
    inject_field_loss,
    load_monitoring,
    overall_status,
    performance,
    share_shift,
    triggered,
    verify_manifest,
)
from inf8239_u04.governance import load_config
from inf8239_u04.model import build_model

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VARIANTS = {"logistic": ("logistic", ()), "tree": ("tree", ()), "logistic_sin_age": ("logistic", ("age_band",))}
OUT = Path("reports/lab13/simulacro")
POSTMORTEM = Path("reports/lab13/INCIDENT_POSTMORTEM.md")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fault-group", default="G2")
    parser.add_argument("--fault-column", default="previous_incidents")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    timeline: list[dict] = []
    t_start = time.perf_counter()

    def log(step: str, role: str, detail: str, automated: bool = True) -> None:
        timeline.append({"utc": now(), "elapsed_s": round(time.perf_counter() - t_start, 2), "step": step,
                         "role": role, "automated": automated, "detail": detail})

    gates = load_config()["gates"]
    monitoring = load_monitoring()
    decision = yaml.safe_load(Path("student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
    selected = str(decision.get("selected_model", "logistic"))
    kind, drop = VARIANTS[selected]
    support = monitoring["support"]
    zcfg = monitoring["signals"]["zero_share_shift"]

    df = load_data()
    train, test = temporal_split(df)
    half = len(test) // 2
    window_a, window_b = test.iloc[:half].copy(), test.iloc[half:].copy()
    window_b_fault = inject_field_loss(window_b, "protected_group", args.fault_group, args.fault_column, 0)

    model = build_model(kind, drop).fit(features(train, drop), train.target)
    snapshot = OUT / "model_snapshot.joblib"
    joblib.dump(model, snapshot)
    model_kb = snapshot.stat().st_size / 1024
    t0 = time.perf_counter()
    model.predict(features(test, drop))
    latency_ms = (time.perf_counter() - t0) * 1000 / len(test)
    log("0 línea base", "ML Engineer", f"modelo {selected} entrenado con {len(train)} casos; ventanas A={len(window_a)}, B={len(window_b)}")

    def evaluate(name: str, window: pd.DataFrame, cumulative: pd.DataFrame) -> dict:
        schema_ok = True
        try:
            validate_schema(window)
        except ValueError:
            schema_ok = False
        dcfg = monitoring["signals"]["drift_psi"]
        drift = drift_table(train, window, dcfg["numeric"], dcfg["categorical"], dcfg["watch"], dcfg["alert"], dcfg["bins"])
        shift = share_shift(train[zcfg["feature"]], window[zcfg["feature"]], 0)
        pred = model.predict(features(cumulative, drop))
        perf = performance(cumulative.target, pred, cumulative.protected_group, min_n=support["min_n"],
                           min_positives=support["min_positives"], min_negatives=support["min_negatives"])
        signals = evaluate_signals(monitoring, gates, schema_ok=schema_ok, drift=drift, zero_shift=shift, perf=perf,
                                   latency_ms=latency_ms, model_kb=model_kb)
        return {"name": name, "signals": signals, "status": overall_status(signals), "drift": drift, "shift": shift,
                "perf": perf, "n_window": len(window), "n_cumulative": len(cumulative)}

    scen_a = evaluate("A_operacion_normal", window_a, window_a)
    scen_b = evaluate("B_sin_falla", window_b, pd.concat([window_a, window_b]))
    scen_c = evaluate("C_con_falla", window_b_fault, pd.concat([window_a, window_b_fault]))
    scenarios = [scen_a, scen_b, scen_c]

    rows = []
    for sc in scenarios:
        for s in sc["signals"]:
            rows.append({"scenario": sc["name"], **s})
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "monitor_resumen.csv", index=False, encoding="utf-8")
    group_rows = []
    for sc in scenarios:
        for _, g in sc["perf"]["groups"].iterrows():
            group_rows.append({"scenario": sc["name"], "group": g["group"], "n": g["n"], "positives": g["positives"],
                               "negatives": g["negatives"], "selection_rate": g["selection_rate"], "recall": g["recall"],
                               "fpr": g["fpr"], "support_ok": g["support_ok"]})
    groups_df = pd.DataFrame(group_rows)
    groups_df.to_csv(OUT / "monitor_grupos.csv", index=False, encoding="utf-8")
    states = pd.DataFrame([{"scenario": sc["name"], "status": sc["status"], "n_window": sc["n_window"],
                            "n_cumulative": sc["n_cumulative"], "signals_review_or_stop": len(triggered(sc["signals"])),
                            "signals_sin_evidencia": sum(s["status"] == "SIN_EVIDENCIA" for s in sc["signals"])} for sc in scenarios])
    states.to_csv(OUT / "monitor_estados.csv", index=False, encoding="utf-8")

    # --- conciliación: el acumulado sin falla es todo el periodo de prueba, igual que la auditoría del E07
    full_pred = model.predict(features(test, drop))
    check = performance(test.target, full_pred, test.protected_group)
    reconcile = {"recall_acumulado_B": scen_b["perf"]["overall"]["recall"], "recall_conjunto_de_prueba": check["overall"]["recall"]}
    reconcile["coincide"] = bool(np.isclose(reconcile["recall_acumulado_B"], reconcile["recall_conjunto_de_prueba"]))
    e07_path = Path("reports/e07/variants_summary.csv")
    if e07_path.exists():
        e07 = pd.read_csv(e07_path).set_index("variant")
        if selected in e07.index:
            reconcile["recall_e07"] = float(e07.loc[selected, "recall"])
            reconcile["coincide_con_e07"] = bool(np.isclose(reconcile["recall_e07"], reconcile["recall_conjunto_de_prueba"], atol=1e-6))

    print("=== Estados ===")
    print(states.to_string(index=False))
    print("\n=== Recall y FPR por grupo (acumulado de cada escenario) ===")
    print(groups_df[["scenario", "group", "n", "recall", "fpr", "support_ok"]].round(3).to_string(index=False))
    for sc in scenarios:
        bad = [s for s in sc["signals"] if s["status"] not in {"OK"}]
        print(f"\n--- {sc['name']}: {sc['status']} ---")
        for s in bad:
            print(f"  {s['status']:<14} {s['signal']:<34} valor={s['value']} umbral={s['threshold']} dueño={s['owner']}")

    detected = scen_c["status"] in {"REVIEW", "STOP"}
    result: dict = {"selected_model": selected, "fault": {"group": args.fault_group, "column": args.fault_column, "value": 0, "injected": True},
                    "status_by_scenario": {sc["name"]: sc["status"] for sc in scenarios}, "fault_detected": bool(detected),
                    "false_alarm_in_control": scen_b["status"] in {"REVIEW", "STOP"}, "reconciliation": reconcile}

    if not detected:
        result["note"] = "El monitoreo NO detectó la falla inyectada: revisar umbrales antes de confiar en él."
        (OUT / "resultado.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\nATENCIÓN: la falla no fue detectada.")
        return 1

    first = triggered(scen_c["signals"])
    log("1 detección", "ML Engineer", f"monitoreo en {scen_c['name']}: {len(first)} señal(es) REVIEW/STOP; la primera ventana con falla ya dispara la alerta")
    data_signals = [s["signal"] for s in first if s["signal"].split(":")[0] in {"data_contract", "drift_psi", "zero_share_shift"}]
    first_signal = ", ".join(data_signals) if data_signals else first[0]["signal"]

    # --- contención: modo seguro
    fifo_capacity = scen_b["perf"]["overall"]["selection_rate"]
    test_sorted = test.sort_values("received_date")
    model_recall = check["overall"]["recall"]
    fifo_recall = capacity_recall(test_sorted, "target", fifo_capacity)
    safe = {"status": scen_c["status"], "mode": "baseline_manual_fifo", "model_disabled": selected, "set_at_utc": now(),
            "set_by_role": "ML Engineer", "lifted_by_role_required": "Institutional Owner",
            "baseline": "Revisión humana por orden de llegada, sin puntaje", "review_capacity_fraction": round(float(fifo_capacity), 4),
            "expected_recall_model": round(float(model_recall), 4), "expected_recall_fifo_same_capacity": round(float(fifo_recall), 4)}
    (OUT / "safe_mode.json").write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
    log("2 contención", "ML Engineer", f"modelo deshabilitado; modo {safe['mode']}; el Institutional Owner debe autorizar la reanudación")

    # --- preservación de evidencia (antes de tocar nada más)
    window_b_fault.assign(fault_injected="yes").to_csv(OUT / "ventana_con_falla.csv", index=False, encoding="utf-8")
    scen_c["drift"].to_csv(OUT / "deriva_con_falla.csv", index=False, encoding="utf-8")
    preserve = ["data/territorial_risk_synthetic.csv", "configs/governance.yml", "configs/monitoring.yml",
                "student_inputs/lab12_decision.yml", "student_inputs/raci.csv", "reports/lab13/simulacro/model_snapshot.joblib",
                "reports/lab13/simulacro/monitor_resumen.csv", "reports/lab13/simulacro/monitor_estados.csv",
                "reports/lab13/simulacro/ventana_con_falla.csv", "reports/lab13/simulacro/deriva_con_falla.csv",
                "reports/lab13/simulacro/safe_mode.json"]
    manifest = build_manifest(preserve)
    (OUT / "evidence_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    altered = verify_manifest(manifest)
    log("3 evidencia", "Operator", f"{len(manifest)} archivos con SHA-256; verificación inmediata sin cambios: {not altered}")

    # --- comunicación (borrador; lo aprueba el Institutional Owner)
    shift = scen_c["shift"]
    comms = f"""# Borradores de comunicación del incidente simulado

> Borradores para aprobación del **Institutional Owner**. No se envían sin esa aprobación. Sin datos personales ni culpas individuales.

## 1. Interna (equipo y operadores)

Asunto: DSS en modo seguro por posible falla de datos

El monitoreo detectó que el campo `{args.fault_column}` llega en cero para el grupo `{args.fault_group}` ({shift['reference_share']:.0%} de ceros en la referencia frente a {shift['current_share']:.0%} ahora). Hasta nuevo aviso el sistema funciona en revisión manual por orden de llegada, sin puntaje. No tome decisiones con puntajes generados desde el último lote. La causa aún no está confirmada. Responsable de la respuesta: ML Engineer; autoridad para reanudar: Institutional Owner.

## 2. A representantes de las personas afectadas (Product Owner redacta, Legal revisa)

Asunto: Aviso sobre una falla en una herramienta de apoyo a la revisión

Detectamos una falla en los datos que alimentan una herramienta que ayuda a ordenar la revisión de casos. Mientras la corregimos, los casos se revisan en orden de llegada y siempre por una persona. Los casos del periodo afectado se volverán a revisar. Puede solicitar la revisión de un caso por el mecanismo de apelación. Le informaremos cuando se resuelva.
"""
    (OUT / "comunicaciones.md").write_text(comms, encoding="utf-8")
    log("4 comunicación", "Product Owner", "borradores interno y externo preparados; pendientes de aprobación humana", automated=False)

    # --- impacto del periodo afectado
    clean_pred_b = model.predict(features(window_b, drop))
    fault_pred_b = model.predict(features(window_b_fault, drop))
    affected = window_b_fault.protected_group == args.fault_group
    changed = int((clean_pred_b != fault_pred_b).sum())
    pos_affected = window_b.loc[affected & (window_b.target == 1)]
    missed = int(((fault_pred_b == 0) & (window_b.target.to_numpy() == 1) & affected.to_numpy()).sum())
    missed_clean = int(((clean_pred_b == 0) & (window_b.target.to_numpy() == 1) & affected.to_numpy()).sum())
    impact = {"cases_in_window": int(len(window_b)), "cases_from_faulty_source": int(affected.sum()),
              "predictions_changed_by_fault": changed, "positives_in_faulty_source": int(len(pos_affected)),
              "positives_not_prioritized_with_fault": missed, "positives_not_prioritized_without_fault": missed_clean}
    log("5 impacto", "Data Scientist", f"{changed} predicciones cambiaron por la falla; positivos no priorizados en la fuente afectada: {missed} (sin falla: {missed_clean})")

    # --- reversión y recuperación
    log("6 reversión", "ML Engineer", f"línea base manual: recall esperado {fifo_recall:.3f} con la misma capacidad frente a {model_recall:.3f} del modelo")
    recovery = scen_b  # misma ventana B pero con la fuente corregida
    recovered = recovery["status"] not in {"REVIEW", "STOP"}
    log("7 recuperación", "Data Engineer", f"ventana B con la fuente corregida: estado {recovery['status']}; falta una segunda evaluación limpia y la firma del Institutional Owner")

    # --- postmortem
    base = datetime.now(timezone.utc).date()
    due = lambda days: (base + timedelta(days=days)).isoformat()
    sig_lines = "\n".join(f"| {s['signal']} | {s['value']} | {s['threshold']} | {s['status']} | {s['owner']} |" for s in first)
    gap_c = scen_c["perf"]
    gap_b = scen_b["perf"]
    fmt = lambda v: "sin evidencia suficiente" if v is None else f"{v:.3f}"
    gb, gc = gap_b["groups"].set_index("group"), gap_c["groups"].set_index("group")
    if {"G1", "G2"} <= set(gb.index) and {"G1", "G2"} <= set(gc.index):
        sb = gb.loc["G2", "recall"] - gb.loc["G1", "recall"]
        sc_ = gc.loc["G2", "recall"] - gc.loc["G1", "recall"]
        fb = gb.loc["G2", "fpr"] - gb.loc["G1", "fpr"]
        fc = gc.loc["G2", "fpr"] - gc.loc["G1", "fpr"]
        group_reading = f"""
## Lectura por grupo (el valor absoluto de la brecha esconde el sentido)

| | Sin falla (B) | Con falla (C) |
|---|---|---|
| Recall G1 | {gb.loc['G1', 'recall']:.3f} | {gc.loc['G1', 'recall']:.3f} |
| Recall G2 | {gb.loc['G2', 'recall']:.3f} | {gc.loc['G2', 'recall']:.3f} |
| Brecha de recall (G2 − G1) | {sb:+.3f} | {sc_:+.3f} |
| FPR G1 | {gb.loc['G1', 'fpr']:.3f} | {gc.loc['G1', 'fpr']:.3f} |
| FPR G2 | {gb.loc['G2', 'fpr']:.3f} | {gc.loc['G2', 'fpr']:.3f} |
| Brecha de FPR (G2 − G1) | {fb:+.3f} | {fc:+.3f} |

{'La brecha de recall cambia de sentido' if sb * sc_ < 0 else 'La brecha de recall mantiene su sentido'} (de {sb:+.3f} a {sc_:+.3f}); su tamaño absoluto pasa de {abs(sb):.3f} a {abs(sc_):.3f}. La FPR de G2 {'baja' if gc.loc['G2', 'fpr'] < gb.loc['G2', 'fpr'] else 'sube'} de {gb.loc['G2', 'fpr']:.3f} a {gc.loc['G2', 'fpr']:.3f}: una FPR menor no es una mejora si el modelo dejó de marcar casos que sí requerían revisión.

Riesgo de "nivelar hacia abajo": una brecha puede cerrarse porque el grupo desfavorecido empeora y no porque mejore el otro. Por eso el monitoreo no se apoya solo en brechas: el recall global y las señales de datos también activan REVIEW.
"""
    else:
        group_reading = ""
    timeline_rows = "\n".join(f"| {t['utc']} | {t['step']} | {t['role']} | {'sí' if t['automated'] else 'no (humano)'} | {t['detail']} |" for t in timeline)
    text = f"""# Postmortem del incidente simulado (sin culpas)

> Simulacro. La falla fue **inyectada** con `scripts/e08_simulacro.py` en datos sintéticos; no hubo personas ni decisiones reales afectadas. Fechas y responsables de las acciones son una propuesta de la autora.

## Resumen

Un cambio en la fuente hace que `{args.fault_column}` llegue en 0 para `{args.fault_group}`. El monitoreo de datos lo detectó en la **primera ventana** con falla, sin esperar etiquetas. Señales de datos activadas al llegar el lote: `{first_signal}` (se evalúan a la vez; no hay una "primera"). Cambio en la proporción de ceros: {shift['shift']:+.3f} con umbral {zcfg['alert']}. Las señales de rendimiento se confirman después, con las etiquetas acumuladas de la revisión humana. Estado del sistema: **{scen_c['status']}**; modo seguro: revisión manual por orden de llegada.

## Señales activadas

| Señal | Valor | Umbral | Estado | Dueño |
|---|---|---|---|---|
{sig_lines}

Controles sin falla: escenario A (primeros {len(window_a)} casos) estado **{scen_a['status']}**; escenario B (acumulado de {len(test)} casos) estado **{scen_b['status']}**. Falsa alarma de REVIEW/STOP en B: {'sí' if result['false_alarm_in_control'] else 'no'}. Un REVIEW en el control pequeño (A) puede ser ruido de un recall puntual con pocos casos; REVIEW significa que una persona investiga, no que el sistema se apague.

## Impacto estimado en la ventana afectada

- Casos en la ventana: {impact['cases_in_window']}; de la fuente afectada: {impact['cases_from_faulty_source']}.
- Predicciones que cambian por la falla: {impact['predictions_changed_by_fault']}.
- Positivos de la fuente afectada no priorizados: **{impact['positives_not_prioritized_with_fault']}** con la falla frente a {impact['positives_not_prioritized_without_fault']} sin ella (de {impact['positives_in_faulty_source']} positivos).
- Brecha de recall acumulada: con falla {fmt(gap_c['recall_gap'])}; sin falla {fmt(gap_b['recall_gap'])}. Brecha de FPR: con falla {fmt(gap_c['fpr_gap'])}; sin falla {fmt(gap_b['fpr_gap'])}.
- Las brechas se reportan en valor absoluto; el sentido (qué grupo queda por encima) se ve en `reports/lab13/simulacro/monitor_grupos.csv`. Una brecha puede cambiar de sentido casi sin cambiar de tamaño.

{group_reading}
## Línea de tiempo

| UTC | Paso | Rol | Automático | Detalle |
|---|---|---|---|---|
{timeline_rows}

## Qué funcionó y qué no

- Funcionó: la señal de datos (proporción de ceros y PSI) se evalúa al llegar el lote, sin esperar etiquetas; las de rendimiento dependen de la revisión humana y llegan con retraso.
- Limitación: con ventanas pequeñas las brechas por grupo no tienen soporte y se reportan como SIN_EVIDENCIA, nunca como OK.
- Limitación: los umbrales de PSI son una regla práctica; una señal puede quedar apenas por encima del umbral (véase el valor de `drift_psi` en la tabla) y debe recalibrarse con datos reales.
- Limitación: el recall puntual de una ventana pequeña es ruidoso y puede dar REVIEW sin falla real (véase el escenario A).
- Limitación: el escenario es una falla total y obvia del campo. Fallas parciales o sutiles pueden no activar estos umbrales.
- Costo de la reversión: la revisión por orden de llegada con la misma capacidad tiene recall esperado {fifo_recall:.3f} frente a {model_recall:.3f} del modelo.

## Evidencia preservada

`reports/lab13/simulacro/evidence_manifest.json` registra SHA-256 de {len(manifest)} archivos (datos, configuración, modelo, señales y ventana con falla). Verificación inmediata sin cambios: {not altered}.

## Causa raíz

Inyectada por diseño: pérdida del campo `{args.fault_column}` en la fuente de `{args.fault_group}`. En un incidente real la causa se confirmaría con el sistema de origen antes de cerrar.

## Acciones correctivas (propuestas)

| Acción | Responsable | Fecha límite |
|---|---|---|
| Añadir al contrato de datos una prueba que rechace lotes con un campo requerido constante | Data Engineer | {due(7)} |
| Documentar con el sistema de origen quién avisa cambios de esquema | Product Owner | {due(10)} |
| Recalibrar umbrales de PSI y de ceros con datos reales antes de operar | ML Engineer | {due(14)} |
| Revisar de nuevo los casos del periodo afectado | Operator | {due(7)} |
| Probar el simulacro con una falla parcial y repetirlo | Data Scientist | {due(21)} |

## Condición para levantar el REVIEW

Dos evaluaciones consecutivas sin señales REVIEW o STOP y autorización escrita del **Institutional Owner**. Estado del simulacro: 1 de 2 evaluaciones limpias (ventana B sin falla: {recovery['status']}); falta la segunda evaluación y la firma. Reanudar no se decide por script.
"""
    POSTMORTEM.write_text(text, encoding="utf-8")
    pd.DataFrame(timeline).to_csv(OUT / "linea_de_tiempo.csv", index=False, encoding="utf-8")
    result.update({"first_signal": first_signal, "impact": impact, "safe_mode": safe, "evidence_files": len(manifest),
                   "manifest_verified": not altered, "recovered_window_status": recovery["status"], "recovered": bool(recovered),
                   "n_signals_review_or_stop_with_fault": len(first)})
    (OUT / "resultado.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=float), encoding="utf-8")

    # --- figura (opcional)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
        feats = scen_c["drift"].feature.tolist()
        x = np.arange(len(feats))
        for i, sc in enumerate(scenarios):
            axes[0].bar(x + (i - 1) * 0.27, sc["drift"].psi, 0.27, label=sc["name"])
        dcfg = monitoring["signals"]["drift_psi"]
        axes[0].axhline(dcfg["alert"], color="red", ls="--", lw=1)
        axes[0].axhline(dcfg["watch"], color="orange", ls=":", lw=1)
        axes[0].set_xticks(x, feats, rotation=20, ha="right")
        axes[0].set_ylabel("PSI vs entrenamiento")
        axes[0].set_title("Deriva por variable (rojo: alerta, naranja: vigilar)", fontsize=9)
        axes[0].legend(fontsize=7)
        shifts = [sc["shift"]["shift"] for sc in scenarios]
        axes[1].bar([sc["name"] for sc in scenarios], shifts, color=["#4c78a8", "#4c78a8", "#e45756"])
        axes[1].axhline(zcfg["alert"], color="red", ls="--", lw=1)
        axes[1].axhline(-zcfg["alert"], color="red", ls="--", lw=1)
        axes[1].set_ylabel(f"cambio en la proporción de ceros de {zcfg['feature']}")
        axes[1].set_title("Proporción de ceros (líneas rojas: umbral)", fontsize=9)
        plt.setp(axes[1].get_xticklabels(), rotation=15, ha="right")
        fig.tight_layout()
        fig.savefig(OUT / "e08_simulacro.png", dpi=150)
        print("figura:", OUT / "e08_simulacro.png")
    except ImportError:
        print("matplotlib no está instalado: se omite la figura (use `uv run --with matplotlib ...`).")

    print(f"\nFalla detectada: sí | señales de datos activadas: {first_signal} | falsa alarma en el control: {'sí' if result['false_alarm_in_control'] else 'no'}")
    print(f"Postmortem: {POSTMORTEM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
