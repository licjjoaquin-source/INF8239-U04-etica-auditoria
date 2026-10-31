"""Pruebas de los artefactos del E07: que los registros estén completos y sean coherentes con la evidencia."""
import json
import re
from pathlib import Path

import pandas as pd
import yaml

from inf8239_u04.impact import score_risks, validate_impact

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_DECISIONS = ("desplegar", "modificar", "limitar", "no utilizar")
PATH_PATTERN = re.compile(r"(?:reports|docs|src|student_inputs|configs|scripts|tests|data)/[\w./-]+\.\w+")


def _csv(path):
    return pd.read_csv(ROOT / path)


def _has_placeholder(frame):
    return frame.astype(str).apply(lambda s: s.str.contains("REPLACE")).any().any()


def test_risk_register_has_eight_specific_risks_and_no_placeholders():
    risks = _csv("student_inputs/risk_register.csv")
    assert len(risks) >= 8
    assert risks.id.is_unique
    assert not _has_placeholder(risks)
    assert (risks.scenario.str.len() >= 40).all(), "cada escenario debe ser específico, no una etiqueta"
    scored = score_risks(risks)
    assert scored.priority.max() >= 8


def test_critical_risks_have_valid_owner_evidence_and_residual():
    risks = score_risks(_csv("student_inputs/risk_register.csv"))
    raci = _csv("student_inputs/raci.csv")
    roles = set()
    for column in ("R", "A", "C", "I"):
        for cell in raci[column].dropna():
            roles.update(part.strip() for part in re.split(r"\s+and\s+|,", cell) if part.strip())
    roles |= {"Operator", "Institutional owner", "Data team"}
    for _, row in risks.iterrows():
        assert row.owner in roles, f"{row.id}: responsable '{row.owner}' no existe en el RACI"
        assert row.residual in {"low", "medium", "high"}
        if row.priority >= 8:
            assert len(str(row.evidence).strip()) > 20, f"{row.id}: riesgo crítico sin evidencia"


def test_evidence_paths_cited_in_risks_exist():
    risks = _csv("student_inputs/risk_register.csv")
    missing = []
    for text in risks.evidence.astype(str):
        for path in PATH_PATTERN.findall(text):
            if not (ROOT / path).exists():
                missing.append(path)
    assert not missing, f"evidencia citada que no existe: {sorted(set(missing))}"


def test_stakeholders_and_impact_assessment_are_complete():
    stakeholders = _csv("student_inputs/stakeholders.csv")
    assert len(stakeholders) >= 4 and not _has_placeholder(stakeholders)
    impact = yaml.safe_load((ROOT / "student_inputs/lab11_impact.yml").read_text(encoding="utf-8"))
    assert validate_impact(impact) is True
    assert any(word in impact["withdrawal_condition"] for word in ("0.16", "0.68")), "la condición de retiro debe ser medible"


def test_lab12_decision_is_documented_and_uses_allowed_option():
    decision = yaml.safe_load((ROOT / "student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
    for key in ("priority_harm", "primary_metric", "tolerance", "evidence", "limitation", "recommendation"):
        assert str(decision[key]).strip() not in {"", "REPLACE"}, key
    assert decision["recommendation"].lower().startswith(ALLOWED_DECISIONS)


def test_decision_is_consistent_with_the_audit():
    decision = yaml.safe_load((ROOT / "student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
    summary = _csv("reports/e07/variants_summary.csv").set_index("variant")
    row = summary.loc[decision["selected_model"]]
    uncertain = any(row[f"{m}_gap_status"] != "dentro de la tolerancia" for m in ("recall", "fpr"))
    if uncertain or row.gate_decision != "GO":
        assert not decision["recommendation"].lower().startswith("desplegar"), \
            "no se puede 'desplegar' con brechas inciertas o puertas fallidas"
    assert row.recall >= 0.68 or not decision["recommendation"].lower().startswith("desplegar")


def test_audit_reconciles_with_fairlearn_and_flags_support():
    info = json.loads((ROOT / "reports/e07/e07_resumen.json").read_text(encoding="utf-8"))
    assert info["reconciled_with_lab12"] and all(info["reconciled_with_lab12"].values())
    assert info["intersectional_cells_with_support"] < info["intersectional_cells"], \
        "se esperaba que no todas las celdas interseccionales tuvieran soporte"
    inter = _csv("reports/e07/intersectional_support_logistic.csv")
    assert (inter[~inter.support_ok].support_note != "suficiente").all()


def test_decision_record_has_required_sections():
    text = (ROOT / "reports/lab11/DECISION_RECORD.md").read_text(encoding="utf-8")
    assert "REPLACE" not in text
    for section in ("Decisión", "Evidencia", "Incertidumbre", "Condición de retiro", "Apelación", "Responsable"):
        assert section in text, f"falta la sección {section}"


def test_rmf_mapping_covers_four_functions_with_existing_evidence():
    mapping = _csv("docs/rmf_mapping.csv")
    assert set(mapping.function) == {"GOVERN", "MAP", "MEASURE", "MANAGE"}
    assert set(mapping.status) <= {"documentado", "parcial", "pendiente"}
    missing = [p for p, s in zip(mapping.evidence_file, mapping.status) if s != "pendiente" and not (ROOT / p).exists()]
    assert not missing, f"evidencia declarada que no existe: {missing}"


def test_normative_document_separates_the_three_categories():
    text = (ROOT / "docs/MARCO_NORMATIVO.md").read_text(encoding="utf-8")
    for heading in ("Obligación legal", "Marco voluntario", "Recomendación ética"):
        assert heading in text
    assert "172-13" in text


def test_ai_declaration_is_complete():
    text = (ROOT / "docs/AI_USE_DECLARATION.md").read_text(encoding="utf-8")
    assert "REPLACE" not in text
    for section in ("Herramienta", "Prompts", "Verificaciones", "Correcciones"):
        assert section in text
