"""Tablero del DSS territorial sintético (LAB13 / E08).

Muestra el modelo que decidió la gobernanza (student_inputs/lab12_decision.yml), no el modelo por defecto.
Es un apoyo a la revisión humana: no decide y no autoriza decisiones automáticas.
"""
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from inf8239_u04.data import load_data
from inf8239_u04.e07_stats import group_table
from inf8239_u04.governance import load_config
from inf8239_u04.pipeline import run

VARIANTS = {"logistic": ("logistic", ()), "tree": ("tree", ()), "logistic_sin_age": ("logistic", ("age_band",))}
SIMULACRO = Path("reports/lab13/simulacro")

st.set_page_config(page_title="Governed Green DSS", layout="wide")
st.title("DSS territorial sintético · Gobernanza y Green AI")
st.warning("Demostración educativa con datos sintéticos. No autoriza decisiones automáticas ni representa estadísticas reales.")

cfg = load_config()
decision_doc = yaml.safe_load(Path("student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
impact = yaml.safe_load(Path("student_inputs/lab11_impact.yml").read_text(encoding="utf-8"))
selected = str(decision_doc.get("selected_model", "logistic"))
kind, drop = VARIANTS[selected]
result = run(load_data(), cfg["gates"], kind=kind, drop=drop, output=f"models/{selected}.joblib")

st.subheader("Propósito y autoridad")
st.write(cfg["purpose"])
st.write("Usos prohibidos: " + ", ".join(cfg["prohibited_uses"]))

st.subheader("Modelo en uso y decisión de gobernanza")
excluded = ", ".join(drop) if drop else "ninguno"
st.write(f"Modelo: `{selected}` · predictores excluidos: `{excluded}` · `protected_group` se usa solo para auditar.")
st.write("Recomendación vigente: " + str(decision_doc["recommendation"]))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Accuracy", f"{result['metrics']['accuracy']:.3f}")
c2.metric("Recall", f"{result['metrics']['recall']:.3f}")
c3.metric("Brecha de recall", f"{result['gaps']['recall_gap']:.3f}")
c4.metric("Brecha de FPR", f"{result['gaps']['fpr_gap']:.3f}")
c5.metric("Decisión", result["decision"]["status"])

st.subheader("Métricas por grupo")
st.dataframe(result["by_group"], use_container_width=True)

st.subheader("Soporte e incertidumbre por grupo")
support = group_table(result["test"].target, result["pred"], result["test"].protected_group)
st.dataframe(support, use_container_width=True)
st.caption("Un grupo sin soporte suficiente (casos, positivos y negativos) no se interpreta. Que las puertas den GO no demuestra equidad: los intervalos pueden cruzar la tolerancia.")

st.subheader("Puertas de calidad")
st.json(result["decision"])

states = SIMULACRO / "monitor_estados.csv"
if states.exists():
    st.subheader("Estado del monitoreo (simulacro)")
    st.dataframe(pd.read_csv(states), use_container_width=True)
    st.caption("A: operación normal; B: control sin falla; C: falla inyectada. REVIEW significa que una persona investiga.")

st.subheader("Supervisión humana, apelación y retiro")
st.info("Acción humana: revisar evidencia, documentar la decisión y activar apelación o rollback cuando corresponda.")
st.write("Apelación: " + str(impact["appeal_mechanism"]))
st.write("Condición de retiro: " + str(impact["withdrawal_condition"]))
