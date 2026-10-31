# Expediente de gobernanza · U04.E08

Guía para reproducir y ubicar la evidencia. Decisión vigente: **LIMITAR** (piloto con revisión humana, datos sintéticos).

## Cómo reproducir

```
uv run python scripts/lab13_governance.py
uv run python scripts/e08_inventario.py
uv run --with matplotlib python scripts/e08_simulacro.py
uv run pytest -q
uv run streamlit run app.py
```

## Evidencia por criterio de la rúbrica

| Criterio | Artefactos | Verificación |
|---|---|---|
| Inventario, minimización y retención | `docs/INVENTARIO_DATOS.csv`, `docs/RETENCION.md`, `reports/e08/minimizacion_kanon.csv` | `test_inventory_covers_every_column`, `test_inventory_flags_sensitive_and_direct_identifiers` |
| Datasheet y Model Card trazables | `docs/DATASET_CARD.md`, `docs/MODEL_CARD.md`, `reports/e08/dataset_stats.json` | `test_datasheet_numbers_match_data`, `test_model_card_numbers_match_audit` |
| RACI y traspaso entre roles | `student_inputs/raci.csv`, `docs/HANDOFFS.csv` | `test_raci_has_exactly_one_accountable`, `test_handoffs_use_raci_roles_and_existing_evidence` |
| Monitoreo, runbook y simulacro | `configs/monitoring.yml`, `docs/RUNBOOK.md`, `reports/lab13/simulacro/*`, `reports/lab13/INCIDENT_POSTMORTEM.md` | `tests/test_e08_ops.py`, `test_monitoring_signals_have_owner_and_runbook_step`, `test_simulacro_detects_injected_fault` |
| Supervisión humana en el DSS | `app.py` (tablero con el modelo elegido, soporte por grupo, monitoreo, apelación y retiro) | `tests/test_e08_app.py` |
| Pruebas, Git y calidad documental | `tests/`, historial de commits, etiqueta `u04-e08`, `docs/AI_USE_DECLARATION_E08.md` | `uv run pytest -q` |

Marco normativo: `docs/MARCO_NORMATIVO.md` (obligación legal, marco voluntario y recomendación ética).
