# Runbook de incidentes · Territorial Review DSS (sintético)

*Convierte una alerta del monitoreo (`configs/monitoring.yml`) en acciones con responsable. Se probó con `scripts/e08_simulacro.py` (resultados en `reports/lab13/simulacro/`). Los tiempos objetivo son propuestas de la autora.*

## Niveles

| Nivel | Qué significa | Quién actúa | Tiempo objetivo (propuesta) |
|---|---|---|---|
| GO | Dentro de los límites del piloto | Nadie | Revisión semanal |
| WATCH | Señal en vigilancia o grupo sin soporte (SIN_EVIDENCIA) | ML Engineer | Mismo ciclo semanal |
| REVIEW | Una puerta falla o hay deriva fuerte: una persona analiza la evidencia y registra su decisión | ML Engineer, Product Owner | 1 día hábil |
| STOP | Contrato de datos roto o uso prohibido: no se producen puntajes | ML Engineer, Institutional Owner | Inmediato |

**Autoridad de contención.** Cualquier **Operator** o el **ML Engineer** puede pasar el sistema a REVIEW o al modo seguro sin pedir permiso previo: detener es más barato que dañar. **Solo el Institutional Owner** (Accountable) autoriza reanudar.

## 1. Detección y clasificación

1. El ML Engineer ejecuta la evaluación de monitoreo con cada lote nuevo (`scripts/e08_simulacro.py` es el ensayo; en operación sería el mismo código con datos nuevos).
2. Se leen las señales con estado REVIEW o STOP en `monitor_resumen.csv`. Cada señal indica su dueño y el paso de este runbook.
3. Una brecha sin soporte suficiente aparece como SIN_EVIDENCIA y cuenta como WATCH: **nunca se interpreta como "todo bien"**.
4. Las señales manuales (uso prohibido, apelaciones vencidas, desacuerdo del operador) las revisa el rol indicado cada semana.

## 2. Autoridad de contención

1. Quien detecte la señal deshabilita el puntaje y pasa al modo seguro (`reports/lab13/simulacro/safe_mode.json` es el ejemplo del estado).
2. Se avisa al Institutional Owner (traspaso H05 en `docs/HANDOFFS.csv`).
3. Mientras dure el modo seguro, **ninguna decisión usa el puntaje**.

## 3. Preservación de evidencia

Antes de corregir nada:

1. Guardar datos, configuración, modelo, señales y el lote sospechoso.
2. Generar el manifiesto con SHA-256 (`evidence_manifest.json`) y verificar que no cambió (`verify_manifest`).
3. No sobrescribir ni "limpiar" el lote sospechoso.

## 4. Comunicación interna y a las partes afectadas

1. El Product Owner redacta y Legal revisa; el **Institutional Owner aprueba** antes de enviar (`reports/lab13/simulacro/comunicaciones.md` tiene los borradores).
2. Los mensajes dicen qué se sabe y qué no, sin datos personales y sin culpar a personas.
3. Las apelaciones recibidas durante el incidente se responden por escrito con revisión humana, en el plazo propuesto de 10 días hábiles.

## 5. Reversión o línea base segura

1. Línea base: revisión humana por orden de llegada, sin puntaje. Su costo medido en el simulacro: recall esperado más bajo con la misma capacidad de revisión (`expected_recall_fifo_same_capacity` frente a `expected_recall_model` en `safe_mode.json`).
2. Se revierte a una versión anterior del modelo solo si hay una versión verificada con su manifiesto.
3. **Condición para reanudar:** dos evaluaciones consecutivas sin señales REVIEW o STOP y autorización escrita del Institutional Owner (traspaso H08).

## 6. Postmortem, responsable y fecha

1. El Product Owner dirige el postmortem sin culpas y lo cierra en 5 días hábiles (propuesta).
2. Debe incluir impacto, línea de tiempo, causa raíz, lo que funcionó y lo que no, y acciones con **un solo responsable y una fecha** (`reports/lab13/INCIDENT_POSTMORTEM.md`).
3. Los responsables deben existir en `student_inputs/raci.csv`.
4. Las acciones abiertas se revisan en la siguiente evaluación semanal.

## Límites del runbook

- Se probó con una falla total y obvia en datos sintéticos; no se probó con fallas parciales ni con personas reales.
- Los umbrales de deriva son una regla práctica, no un estándar, y deben recalibrarse con datos reales.
- Los pasos humanos (comunicación, aprobación) se ensayaron como borradores, no con las personas reales de cada rol.
