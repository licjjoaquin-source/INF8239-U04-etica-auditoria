# Declaración de uso de IA · U04.E08

**Estudiante:** Johanna Joaquín · INF-8239 Ciencia de Datos II · UASD
*Borrador preparado con ayuda de IA. Debo revisarlo y ajustarlo a lo que realmente hice antes de entregarlo.*

## Herramienta y finalidad

Claude (Anthropic), usado como asistente conversacional durante el ejercicio, para estructura, código de apoyo, pruebas y redacción. **No decidió los valores del análisis ni creó evidencia:** las cifras de la auditoría salen de `reports/e07` y las del simulacro salen de `reports/lab13/simulacro`, producidos al ejecutar el código en mi computadora.

## Fragmentos afectados

- `src/inf8239_u04/e08_ops.py`, `configs/monitoring.yml`, `scripts/e08_inventario.py`, `scripts/e08_simulacro.py` y las pruebas `tests/test_e08_ops.py` y `tests/test_e08_artifacts.py`.
- Cambios compatibles en `data.py`, `model.py`, `pipeline.py` y `scripts/lab13_governance.py` para poder entrenar sin `age_band` (con `drop=()` el comportamiento es el del proyecto base).
- `app.py` y `tests/test_e08_app.py`: el tablero base entrenaba el logístico con `age_band` y sobrescribía `models/model.joblib`; ahora muestra el modelo elegido en `lab12_decision.yml`, el soporte por grupo, el estado del monitoreo y la supervisión humana.
- Borradores de `docs/INVENTARIO_DATOS.csv`, `docs/RETENCION.md`, `docs/DATASET_CARD.md`, `docs/MODEL_CARD.md`, `docs/RUNBOOK.md`, `docs/HANDOFFS.csv`, `student_inputs/raci.csv`, `docs/rmf_mapping.csv` y el informe PDF.

## Prompts relevantes (resumen)

1. Pegué el mandato del E08, la rúbrica y el manual de LAB13 y pedí un plan que integrara lo hecho en LAB11 y LAB12 y en el E07.
2. Pedí un monitoreo con dueño, umbral y soporte por grupo, y un simulacro que generara evidencia verificable, no solo capturas.
3. Pedí que los documentos citen cifras de mis reportes y que una prueba las compare con esos archivos.
4. Pedí separar obligación legal, marco voluntario y recomendación ética en la retención y el monitoreo.
5. Pedí borradores de la política de retención, del RACI con traspasos y del runbook, que debo revisar y ajustar.

## Verificaciones

- Ejecuté todas las pruebas con `pytest` en mi computadora.
- Ejecuté `lab13_governance.py`, `e08_inventario.py` y `e08_simulacro.py` y usé sus salidas para los documentos y el informe.
- Las pruebas comparan la Model Card y el Datasheet con `reports/e07` y `reports/e08`, y comprueban que el RACI tenga un solo Accountable por actividad, que los traspasos y los dueños de las señales existan en el RACI y que el simulacro detecte la falla inyectada.
- Las referencias normativas se consultaron en la web; el texto de la Ley 172-13 que pude leer terminaba en el art. 83, y las fuentes secundarias no sustituyen el texto oficial.

## Correcciones a la salida de la IA o del material base

- En el E07 afirmé que el plazo de 10 días hábiles de la apelación "no proviene de ninguna ley". Al leer la Ley 172-13 vi que el art. 8 fija 10 días hábiles para reclamos de rectificación y supresión. Lo corregí en `docs/MARCO_NORMATIVO.md`: mi plazo es propio y coincide por analogía, no es un plazo legal para apelar un puntaje.
- Generalizar la fecha a mes no reduce la unicidad lo bastante (la medición de k-anonimato lo muestra); la regla que adopto es generalizar a año y suprimir celdas con menos de 5 casos.
- Con pocas observaciones el recall de una ventana es ruidoso; la señal de recall muestra su intervalo y la política dice que REVIEW significa que una persona investiga, no que el sistema se apague.
- Los umbrales de deriva (PSI 0.10 y 0.25) son una regla práctica, no un estándar; los trato como propuesta que debe recalibrarse con datos reales.
- El simulacro usa una falla inyectada y obvia; no demuestra que el monitoreo detecte fallas parciales.
- El simulacro mostró que la brecha de recall cambió de sentido (G2 pasó de estar por encima de G1 a quedar por debajo) casi sin cambiar de tamaño absoluto, y que la FPR de G2 bajó porque el modelo dejó de marcar casos. Por eso el postmortem incluye una lectura por grupo y no se confía solo en el valor absoluto de la brecha.

## Responsabilidad

Las interpretaciones, la decisión final (limitar), los plazos de retención, las referencias normativas y las conclusiones las reviso y puedo defender. Los datos son sintéticos y no contienen información personal.
