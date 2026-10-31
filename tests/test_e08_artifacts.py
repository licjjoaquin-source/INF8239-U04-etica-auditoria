"""Pruebas de los artefactos del E08: inventario, RACI, traspasos, monitoreo, runbook, cards y simulacro."""
import json
import re
from pathlib import Path

import pandas as pd
import yaml

from inf8239_u04.e08_ops import load_monitoring, verify_manifest
from inf8239_u04.governance import validate_raci

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ACTIVITIES = {"Data quality", "Model validation", "Deployment", "Incident response", "Monitoring",
                       "Data inventory and minimization", "Retention and deletion", "Rollback to safe baseline",
                       "Communication to affected parties", "Appeal handling"}


def _csv(path):
    return pd.read_csv(ROOT / path)


def _text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def _yaml(path):
    return yaml.safe_load(_text(path))


def _roles():
    raci = _csv("student_inputs/raci.csv")
    roles = set()
    for column in ("R", "A", "C", "I"):
        for cell in raci[column].dropna():
            roles.update(part.strip() for part in re.split(r"\s+and\s+|,", cell) if part.strip())
    return roles


def _claims(text):
    """Filas `| clave | número | fuente |` de una tabla de trazabilidad."""
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*`?([A-Za-z0-9_]+)`?\s*\|\s*(-?\d+(?:\.\d+)?)\s*\|\s*([^|]+?)\s*\|\s*$", line)
        if m:
            rows.append((m.group(1), m.group(2), m.group(3)))
    return rows


def _decimals(text):
    return len(text.split(".")[1]) if "." in text else 0


# --------------------------------------------------------------------------- inventario y minimización
def test_inventory_covers_every_column():
    header = list(pd.read_csv(ROOT / "data/territorial_risk_synthetic.csv", nrows=0).columns)
    inventory = _csv("docs/INVENTARIO_DATOS.csv")
    in_inventory = set(inventory.loc[inventory.kind == "column", "asset"])
    assert in_inventory == set(header), f"faltan {set(header) - in_inventory}, sobran {in_inventory - set(header)}"


def test_inventory_flags_sensitive_and_direct_identifiers():
    inventory = _csv("docs/INVENTARIO_DATOS.csv")
    assert not inventory.drop(columns=["notes"]).isna().any().any(), "cada activo necesita finalidad, minimización, retención y rol"
    assert not inventory.astype(str).apply(lambda s: s.str.contains("REPLACE")).any().any()
    governance = _yaml("configs/governance.yml")
    by_asset = inventory.set_index("asset")
    for feature in governance["sensitive_features"]:
        assert by_asset.loc[feature, "category"] == "sensitive"
        assert by_asset.loc[feature, "used_in_model"] == "no", f"{feature} es sensible y no debe ser predictor"
    for identifier in governance["direct_identifiers"]:
        assert by_asset.loc[identifier, "kind"] == "not_collected"
    selected = _yaml("student_inputs/lab12_decision.yml")["selected_model"]
    assert selected == "logistic_sin_age" or by_asset.loc["age_band", "used_in_model"] == "no"


def test_retention_policy_separates_three_categories_and_marks_periods_as_proposals():
    text = _text("docs/RETENCION.md")
    for heading in ("Obligación legal", "Marco voluntario", "Recomendación ética"):
        assert heading in text
    assert "ninguno es un plazo legal" in text.lower() and "propuesta" in text.lower()
    assert "172-13" in text and "REPLACE" not in text


# --------------------------------------------------------------------------- RACI y traspasos
def test_raci_has_exactly_one_accountable():
    raci = _csv("student_inputs/raci.csv")
    assert validate_raci(raci) is True
    assert REQUIRED_ACTIVITIES <= set(raci.activity)
    for _, row in raci.iterrows():
        assert " and " not in row.A and "," not in row.A, f"{row.activity}: debe haber un solo Accountable"
        assert row.R.strip(), f"{row.activity}: falta Responsible"


def test_handoffs_use_raci_roles_and_existing_evidence():
    handoffs = _csv("docs/HANDOFFS.csv")
    roles = _roles()
    assert len(handoffs) >= 6 and handoffs.id.is_unique
    assert not handoffs.isna().any().any()
    for _, row in handoffs.iterrows():
        assert row.from_role in roles, f"{row.id}: {row.from_role} no está en el RACI"
        assert row.to_role in roles, f"{row.id}: {row.to_role} no está en el RACI"
        assert row.from_role != row.to_role
        assert len(row.acceptance_criterion) > 30, f"{row.id}: criterio de aceptación demasiado vago"
        assert (ROOT / row.evidence_path).exists(), f"{row.id}: no existe {row.evidence_path} (¿ejecutó los scripts?)"
        assert (ROOT / row.verification.split("::")[0]).exists(), f"{row.id}: no existe la prueba citada"


# --------------------------------------------------------------------------- monitoreo y runbook
def test_monitoring_signals_have_owner_and_runbook_step():
    mon = load_monitoring(ROOT / "configs/monitoring.yml")
    roles = _roles()
    needed = {"data_contract", "drift_psi", "zero_share_shift", "recall", "recall_gap", "fpr_gap", "latency", "model_size"}
    assert needed <= set(mon["signals"])
    for name, cfg in {**mon["signals"], **mon["manual_checks"]}.items():
        assert cfg["owner"] in roles, f"{name}: dueño {cfg['owner']} no está en el RACI"
        assert 1 <= int(cfg["runbook_step"]) <= 6, f"{name}: paso de runbook inválido"
        assert cfg.get("severity") or cfg.get("alert_severity")
    assert "prohibited_use" in mon["manual_checks"]
    assert mon["selected_model"] == _yaml("student_inputs/lab12_decision.yml")["selected_model"]
    assert mon["support"]["min_positives"] >= 10, "el soporte mínimo no puede ser más laxo que el de la auditoría"
    governance_gates = _yaml("configs/governance.yml")["gates"]
    assert "min_recall" not in json.dumps(mon), "los umbrales de rendimiento se leen de governance.yml, no se duplican"
    assert governance_gates["min_recall"] > 0


def test_runbook_has_six_complete_sections():
    text = _text("docs/RUNBOOK.md")
    assert "REPLACE" not in text
    names = ["Detección", "Autoridad de contención", "Preservación de evidencia", "Comunicación", "Reversión", "Postmortem"]
    for i, name in enumerate(names, start=1):
        m = re.search(rf"^## {i}\. .*{name}.*$", text, flags=re.M)
        assert m, f"falta la sección {i} ({name})"
        body = text[m.end():].split("\n## ", 1)[0]
        assert len([ln for ln in body.splitlines() if ln.strip()]) >= 3, f"la sección {i} está vacía"
    assert "Institutional Owner" in text and "Operator" in text


# --------------------------------------------------------------------------- Datasheet y Model Card
def test_datasheet_numbers_match_data():
    text = _text("docs/DATASET_CARD.md")
    assert "REPLACE" not in text
    for heading in ("Motivación", "Composición", "Proceso de recolección", "Preprocesamiento", "Usos", "Distribución", "Mantenimiento"):
        assert heading in text, f"falta la sección {heading}"
    stats = json.loads(_text("reports/e08/dataset_stats.json"))
    base = _csv("reports/e07/base_rates.csv")
    claims = _claims(text)
    assert len(claims) >= 6
    for key, value, source in claims:
        if source.endswith("dataset_stats.json"):
            actual = stats[key]
        else:
            m = re.match(r"(G\d)(_test)?_(n|target_rate)$", key)
            row = base[(base.protected_group == m.group(1)) & (base.split == ("test" if m.group(2) else "todo"))].iloc[0]
            actual = row["n"] if m.group(3) == "n" else row.target_rate
        assert abs(float(value) - float(actual)) <= 0.5 * 10 ** -_decimals(value) + 1e-9, f"{key}: documento {value}, evidencia {actual}"


def test_model_card_numbers_match_audit():
    text = _text("docs/MODEL_CARD.md")
    assert "REPLACE" not in text
    for heading in ("Intended use", "Out-of-scope use", "Data and split", "Global and subgroup evaluation", "Green AI evidence",
                    "Limitations, human oversight and appeal", "Owner and review date"):
        assert f"## {heading}" in text, f"falta la sección {heading}"
    summary = _csv("reports/e07/variants_summary.csv").set_index("variant")
    selected = _yaml("student_inputs/lab12_decision.yml")["selected_model"]
    claims = _claims(text)
    assert len(claims) >= 8
    for key, value, _ in claims:
        actual = float(summary.loc[selected, key])
        assert abs(float(value) - actual) <= 0.5 * 10 ** -_decimals(value) + 1e-9, f"{key}: documento {value}, evidencia {actual}"
    green = text.split("## Green AI evidence", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\|\s*(logistic|tree|logistic_sin_age)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+) KB\s*\|\s*(GO|REVIEW)\s*\|", green, flags=re.M)
    assert {r[0] for r in rows} == {"logistic", "tree", "logistic_sin_age"}
    for name, acc, rec, kb, gate in rows:
        s = summary.loc[name]
        assert abs(float(acc) - s.accuracy) <= 0.0005 + 1e-9 and abs(float(rec) - s.recall) <= 0.0005 + 1e-9
        assert abs(float(kb) - s.model_kb) <= 0.05 + 1e-9 and gate == s.gate_decision


def test_decision_is_consistent_with_lab13_gates():
    decision = json.loads(_text("reports/lab13/deployment_decision.json"))
    selected = _yaml("student_inputs/lab12_decision.yml")["selected_model"]
    assert decision["selected_model"] == selected
    status = decision["decision"]["status"]
    assert status in {"GO", "REVIEW"}
    assert (status == "GO") == (not decision["decision"]["failed"]), "una puerta fallida no puede ocultarse"
    recommendation = _yaml("student_inputs/lab12_decision.yml")["recommendation"].lower()
    assert recommendation.startswith(("limitar", "modificar", "no utilizar")) or status == "GO"


# --------------------------------------------------------------------------- simulacro y postmortem
def test_simulacro_detects_injected_fault():
    result = json.loads(_text("reports/lab13/simulacro/resultado.json"))
    assert result["fault"]["injected"] is True
    assert result["fault_detected"] is True, "el monitoreo debe detectar la pérdida total de un campo"
    assert result["status_by_scenario"]["C_con_falla"] in {"REVIEW", "STOP"}
    assert result["false_alarm_in_control"] is False, "el control sin falla (acumulado) no debe activar REVIEW o STOP"
    assert result["reconciliation"]["coincide"] is True
    if "coincide_con_e07" in result["reconciliation"]:
        assert result["reconciliation"]["coincide_con_e07"] is True, "el recall del simulacro debe coincidir con la auditoría del E07"
    assert result["manifest_verified"] is True
    safe = json.loads(_text("reports/lab13/simulacro/safe_mode.json"))
    assert safe["status"] in {"REVIEW", "STOP"} and safe["lifted_by_role_required"] == "Institutional Owner"


def test_simulacro_outputs_are_complete():
    folder = ROOT / "reports/lab13/simulacro"
    for name in ("monitor_resumen.csv", "monitor_estados.csv", "evidence_manifest.json", "comunicaciones.md", "linea_de_tiempo.csv", "safe_mode.json", "monitor_grupos.csv"):
        assert (folder / name).exists(), f"falta {name}"
    manifest = json.loads((folder / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) >= 8 and verify_manifest(manifest, ROOT) == [], "la evidencia preservada cambió desde el simulacro"
    comms = (folder / "comunicaciones.md").read_text(encoding="utf-8")
    assert "aprobación" in comms.lower() and "Institutional Owner" in comms
    timeline = _csv("reports/lab13/simulacro/linea_de_tiempo.csv")
    assert {"1 detección", "2 contención", "3 evidencia", "4 comunicación"} <= set(timeline.step)
    summary = _csv("reports/lab13/simulacro/monitor_resumen.csv")
    assert {"A_operacion_normal", "B_sin_falla", "C_con_falla"} == set(summary.scenario)
    assert summary.owner.notna().all() and (summary.owner.str.len() > 0).all()


def test_postmortem_has_owners_and_dates():
    text = _text("reports/lab13/INCIDENT_POSTMORTEM.md")
    assert "REPLACE" not in text
    for section in ("Resumen", "Señales activadas", "Impacto estimado", "Lectura por grupo", "Línea de tiempo", "Causa raíz", "Acciones correctivas", "Condición para levantar"):
        assert section in text, f"falta {section}"
    roles = _roles()
    actions = re.findall(r"^\|\s*([^|]+?)\s*\|\s*([A-Za-z ]+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*$", text.split("## Acciones correctivas", 1)[1], flags=re.M)
    actions = [a for a in actions if a[0] not in {"Acción"}]
    assert len(actions) >= 3
    for action, owner, date in actions:
        assert owner in roles, f"'{action}': {owner} no está en el RACI"
        pd.Timestamp(date)
    assert "Institutional Owner" in text.split("## Condición para levantar", 1)[1]


# --------------------------------------------------------------------------- documentación
def test_ai_declaration_e08_is_complete():
    text = _text("docs/AI_USE_DECLARATION_E08.md")
    assert "REPLACE" not in text
    for section in ("Herramienta", "Fragmentos afectados", "Prompts", "Verificaciones", "Correcciones"):
        assert section in text, f"falta {section}"


def test_normative_document_covers_retention_and_monitoring():
    text = _text("docs/MARCO_NORMATIVO.md")
    assert "172-13" in text and "Conservación" in text and "Monitoreo" in text
    assert "no proviene de ninguna ley" not in text, "el plazo de 10 días hábiles coincide con el art. 8; la afirmación del E07 se corrigió"
