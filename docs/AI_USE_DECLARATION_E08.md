# Declaración de uso de IA · U04.E08

**Estudiante:** Johanna Joaquín · INF-8239 Ciencia de Datos II · UASD
**Estado:** documento revisado por la autora el 04/11/2026, después de la observación del profesor. Describe lo que hice, lo que verifiqué y los valores que adopté.

## Herramienta y finalidad

Claude (Anthropic), usado como asistente conversacional durante el ejercicio, para estructura, código de apoyo, pruebas y redacción. **No decidió los valores del análisis ni creó evidencia:** las cifras de la auditoría salen de `reports/e07` y las del simulacro salen de `reports/lab13/simulacro`, producidos al ejecutar el código en mi computadora.

## Valores y decisiones que adopté

Son míos: la IA propuso formatos y borradores, y yo elegí y asumo cada valor.

- Decisión: **LIMITAR**. Uso el modelo `logistic_sin_age` solo como ayuda de priorización, con revisión humana obligatoria, en un piloto con datos sintéticos o de aula.
- Tolerancia de brecha de 0.16 y soporte mínimo de 20 casos (10 positivos y 10 negativos) por grupo.
- Minimización: la fecha se generaliza a año y se suprimen las celdas con menos de 5 casos (k = 5), según `reports/e08/minimizacion_kanon.csv`.
- Retención (propuestas mías, no plazos legales; cada plazo es un valor único con su fecha de inicio): registros de casos, 12 meses desde el cierre del caso y de su apelación; tablas de auditoría agregadas, 24 meses desde su generación; modelo, 12 meses desde que se retira de uso la versión; decisión de puertas, 24 meses desde que se retira de uso la versión que describe; registro de revisión del operador, 12 meses desde la fecha del registro; registro de apelaciones, 24 meses desde el cierre de la apelación; evidencia de incidentes, 36 meses desde el cierre del postmortem y de sus acciones.
- Umbrales de deriva PSI de 0.10 (vigilar) y 0.25 (alertar): regla práctica, no estándar; deben recalibrarse con datos reales.
- Plazo de apelación de 10 días hábiles: propuesta mía. Coincide por analogía con el art. 8 de la Ley 172-13 (rectificación y supresión), pero no es un plazo legal para apelar un puntaje.

## Fragmentos afectados

- `src/inf8239_u04/e08_ops.py`, `configs/monitoring.yml`, `scripts/e08_inventario.py`, `scripts/e08_simulacro.py` y las pruebas `tests/test_e08_ops.py`, `tests/test_e08_artifacts.py` y `tests/test_e08_retencion.py`.
- Cambios compatibles en `data.py`, `model.py`, `pipeline.py` y `scripts/lab13_governance.py` para poder entrenar sin `age_band` (con `drop=()` el comportamiento es el del proyecto base).
- `app.py` y `tests/test_e08_app.py`: el tablero base entrenaba el logístico con `age_band` y sobrescribía `models/model.joblib`; ahora muestra el modelo elegido en `lab12_decision.yml`, el soporte por grupo, el estado del monitoreo y la supervisión humana.
- Borradores de `docs/INVENTARIO_DATOS.csv`, `docs/RETENCION.md`, `docs/MARCO_NORMATIVO.md`, `docs/DATASET_CARD.md`, `docs/MODEL_CARD.md`, `docs/RUNBOOK.md`, `docs/HANDOFFS.csv`, `student_inputs/raci.csv`, `docs/rmf_mapping.csv` y el informe.

## Prompts relevantes (resumen)

1. Pegué el mandato del E08, la rúbrica y el manual de LAB13 y pedí un plan que integrara lo hecho en LAB11 y LAB12 y en el E07.
2. Pedí un monitoreo con dueño, umbral y soporte por grupo, y un simulacro que generara evidencia verificable, no solo capturas.
3. Pedí que los documentos citen cifras de mis reportes y que una prueba las compare con esos archivos.
4. Pedí separar obligación legal, marco voluntario y recomendación ética en la retención y el monitoreo.
5. Pedí borradores de la política de retención, del RACI con traspasos y del runbook, que revisé y ajusté.
6. Tras la observación del profesor, pedí cerrar los intervalos de retención en valores únicos con fecha de inicio y repetir la verificación normativa con fuentes oficiales.

## Verificaciones

- Ejecuté todas las pruebas con `pytest` en mi computadora.
- Ejecuté `lab13_governance.py`, `e08_inventario.py` y `e08_simulacro.py` y usé sus salidas para los documentos y el informe.
- Las pruebas comparan la Model Card y el Datasheet con `reports/e07` y `reports/e08`, y comprueban que el RACI tenga un solo Accountable por actividad, que los traspasos y los dueños de las señales existan en el RACI y que el simulacro detecte la falla inyectada.
- Una prueba (`tests/test_e08_retencion.py`) falla si algún plazo de retención es un intervalo o una alternativa («12 a 24 meses», «o hasta») o si el inventario y `docs/RETENCION.md` no coinciden.
- Normativa: el texto de la Ley 172-13 que pude leer terminaba en el art. 83 y era una copia no oficial, sin cotejar con la Gaceta Oficial. El 04/11/2026 repetí la consulta con fuentes oficiales (Senado, decretos 498-23 y 787-26) y dejé un registro en `docs/MARCO_NORMATIVO.md` (sección 5) que separa lo oficial, lo secundario y lo no verificado.

## Correcciones a la salida de la IA o del material base

- En el E07 afirmé que el plazo de 10 días hábiles de la apelación "no proviene de ninguna ley". Al leer la Ley 172-13 vi que el art. 8 fija 10 días hábiles para reclamos de rectificación y supresión. Lo corregí en `docs/MARCO_NORMATIVO.md`: mi plazo es propio y coincide por analogía, no es un plazo legal para apelar un puntaje.
- Mis plazos de retención tenían intervalos y alternativas («12 a 24 meses», «36 meses o hasta cerrar el postmortem», «se eliminan o se agregan»). Los cerré en valores únicos con fecha de inicio y alineé el inventario con la política.
- Escribí que no había ninguna norma aplicable de IA en la República Dominicana. Mi primera búsqueda no encontró el Decreto 787-26 (2/11/2026), que obliga a la Administración Pública; por eso ahora afirmo solo lo que verifiqué, con fecha y fuente.
- Generalizar la fecha a mes no reduce la unicidad lo bastante (la medición de k-anonimato lo muestra); la regla que adopto es generalizar a año y suprimir celdas con menos de 5 casos.
- Con pocas observaciones el recall de una ventana es ruidoso; la señal de recall muestra su intervalo y la política dice que REVIEW significa que una persona investiga, no que el sistema se apague.
- Los umbrales de deriva (PSI 0.10 y 0.25) son una regla práctica, no un estándar; los trato como propuesta que debe recalibrarse con datos reales.
- El simulacro usa una falla inyectada y obvia; no demuestra que el monitoreo detecte fallas parciales.
- El simulacro mostró que la brecha de recall cambió de sentido (G2 pasó de estar por encima de G1 a quedar por debajo) casi sin cambiar de tamaño absoluto, y que la FPR de G2 bajó porque el modelo dejó de marcar casos. Por eso el postmortem incluye una lectura por grupo y no se confía solo en el valor absoluto de la brecha.

## Responsabilidad

Las interpretaciones, la decisión final (limitar), los plazos de retención, las referencias normativas y las conclusiones las reviso y puedo defender. Los datos son sintéticos y no contienen información personal.
