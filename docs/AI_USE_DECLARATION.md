# Declaración de uso de IA · U04.E07

**Estudiante:** Johanna Joaquín · INF-8239 Ciencia de Datos II · UASD


## Herramienta y finalidad

Claude (Anthropic), usado como asistente conversacional durante el ejercicio, para estructura, código de apoyo, pruebas y redacción. **No decidió los valores del análisis ni creó evidencia:** todas las cifras salen de `reports/lab12` y `reports/e07`, producidos al ejecutar el código en mi computadora.

## Fragmentos afectados

- `src/inf8239_u04/e07_stats.py`, `scripts/e07_audit_extended.py` y `tests/test_e07_stats.py`: auditoría ampliada (soporte por grupo, intervalos, brechas con IC, chequeo de proxies y barrido de umbral).
- `scripts/lab11_impact.py` y `scripts/simulate_incident.py`: versiones corregidas.
- Borradores de `student_inputs/*`, `reports/lab11/DECISION_RECORD.md`, `docs/MARCO_NORMATIVO.md`, `docs/APLICACION_TF10.md`, `docs/rmf_mapping.csv`, `tests/test_e07_artifacts.py` y el informe PDF.

## Prompts relevantes (resumen)

1. Pegué el mandato del ejercicio, la rúbrica y los manuales de LAB11, LAB12 y LAB13 y pedí un plan.
2. Pegué las salidas de mi terminal, el código del proyecto base y los resultados del LAB12.
3. Pedí una auditoría que vaya más allá de las métricas puntuales: incertidumbre, soporte por grupo, interseccionalidad y comparación de mitigaciones.
4. Pedí borradores de los registros y del marco normativo, que revisé y ajusté.

## Verificaciones

- Ejecuté todas las pruebas con `pytest`.
- Ejecuté los dos modelos del LAB12 y la auditoría ampliada; las cifras puntuales coinciden con las de Fairlearn (`reconciled_with_lab12` es verdadero para los dos modelos).
- Contrasté las cifras del registro de riesgos, la decisión y el informe con los archivos de `reports/`.
- Las referencias normativas se consultaron en fuentes web; las fuentes secundarias se marcan como tales y no sustituyen el texto oficial.

## Correcciones a la salida de la IA o del material base

- Los scripts `lab11_impact.py` y `simulate_incident.py` del proyecto base no se podían ejecutar (`SyntaxError`, saltos de línea dentro de comillas simples) y sobrescribían `DECISION_RECORD.md` en cada ejecución; se corrigieron.
- La plantilla del registro de riesgos traía una probabilidad de 2 para R01 (falso negativo); la evidencia (28 % de los positivos no se prioriza) indica que ocurre con frecuencia, y la subí a 4. Esta es una decisión mía, basada en el recall medido.
- El barrido de umbral se hizo sobre la misma muestra de prueba; por eso no lo uso para elegir un umbral y lo documento como exploratorio.
- "Pasa las puertas" no se presenta como "es equitativo": los intervalos de las brechas cruzan la tolerancia y varios grupos no tienen soporte suficiente.

## Responsabilidad

Las interpretaciones, la decisión final (limitar), las referencias normativas y las conclusiones las reviso y puedo defender. Los datos son sintéticos y no contienen información personal.
