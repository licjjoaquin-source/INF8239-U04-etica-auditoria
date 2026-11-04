"""Los plazos de retención deben ser valores únicos con fecha de inicio, y el inventario debe coincidir con la política."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERVALOS = [r"\d+\s+a\s+\d+\s+meses", r"\bo\s+hasta\b", r"\beliminan\s+o\b", r"\bo\s+se\s+agregan\b", r"\bo\s+agregan\b", r"mientras\s+exista"]


def _plazos_politica() -> list[tuple[str, str]]:
    texto = (ROOT / "docs/RETENCION.md").read_text(encoding="utf-8")
    seccion = texto.split("## Plazos propuestos")[1].split("\n## ")[0]
    filas = []
    for linea in seccion.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if linea.startswith("|") and len(celdas) >= 3 and set(celdas[0]) - set("-: ") and celdas[0] != "Activo":
            filas.append((celdas[0], celdas[1]))
    return filas


def _inventario() -> list[dict]:
    with (ROOT / "docs/INVENTARIO_DATOS.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_retention_periods_are_single_values_with_a_start_date():
    plazos = _plazos_politica()
    assert len(plazos) >= 6
    for activo, plazo in plazos:
        assert "desde" in plazo, f"{activo}: el plazo debe decir desde cuándo cuenta"
        for patron in INTERVALOS:
            assert not re.search(patron, plazo, flags=re.IGNORECASE), f"{activo}: plazo ambiguo -> {plazo}"
    for fila in _inventario():
        if fila["kind"] == "not_collected":
            continue
        valor = fila["retention_proposal"]
        assert "desde" in valor, f"{fila['asset']}: falta la fecha de inicio -> {valor}"
        for patron in INTERVALOS:
            assert not re.search(patron, valor, flags=re.IGNORECASE), f"{fila['asset']}: plazo ambiguo -> {valor}"


def test_inventory_retention_matches_the_policy():
    esperado = {
        "models/logistic_sin_age.joblib": "12 meses",
        "reports/lab12 y reports/e07": "24 meses",
        "reports/lab13/deployment_decision.json": "24 meses",
        "reports/lab13/simulacro/ventana_con_falla.csv": "36 meses",
        "reports/lab13/simulacro/evidence_manifest.json": "36 meses",
        "registro de revisión del operador": "12 meses",
        "registro de apelaciones": "24 meses",
    }
    inventario = {f["asset"]: f["retention_proposal"] for f in _inventario()}
    politica = " ".join(f"{a} {p}" for a, p in _plazos_politica())
    for activo, meses in esperado.items():
        assert inventario[activo].startswith(meses), f"{activo}: {inventario[activo]}"
        assert meses in politica, f"{meses} no aparece en la política"
