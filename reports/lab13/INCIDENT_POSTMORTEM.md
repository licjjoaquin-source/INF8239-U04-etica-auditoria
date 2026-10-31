# Postmortem del incidente simulado (sin culpas)

> Simulacro. La falla fue **inyectada** con `scripts/e08_simulacro.py` en datos sintéticos; no hubo personas ni decisiones reales afectadas. Fechas y responsables de las acciones son una propuesta de la autora.

## Resumen

Un cambio en la fuente hace que `previous_incidents` llegue en 0 para `G2`. El monitoreo de datos lo detectó en la **primera ventana** con falla, sin esperar etiquetas. Señales de datos activadas al llegar el lote: `drift_psi:previous_incidents, zero_share_shift:previous_incidents` (se evalúan a la vez; no hay una "primera"). Cambio en la proporción de ceros: +0.265 con umbral 0.15. Las señales de rendimiento se confirman después, con las etiquetas acumuladas de la revisión humana. Estado del sistema: **REVIEW**; modo seguro: revisión manual por orden de llegada.

## Señales activadas

| Señal | Valor | Umbral | Estado | Dueño |
|---|---|---|---|---|
| drift_psi:previous_incidents | 0.2809 | watch 0.1 / alert 0.25 | REVIEW | ML Engineer |
| zero_share_shift:previous_incidents | 0.2646 | cambio absoluto < 0.15 | REVIEW | Data Engineer |
| recall | 0.5761 | >= 0.68 | REVIEW | Data Scientist |
| recall_gap | 0.1647 | <= 0.16 | REVIEW | Data Scientist |
| fpr_gap | 0.1683 | <= 0.16 | REVIEW | Data Scientist |

Controles sin falla: escenario A (primeros 80 casos) estado **REVIEW**; escenario B (acumulado de 160 casos) estado **GO**. Falsa alarma de REVIEW/STOP en B: no. Un REVIEW en el control pequeño (A) puede ser ruido de un recall puntual con pocos casos; REVIEW significa que una persona investiga, no que el sistema se apague.

## Impacto estimado en la ventana afectada

- Casos en la ventana: 80; de la fuente afectada: 26.
- Predicciones que cambian por la falla: 18.
- Positivos de la fuente afectada no priorizados: **14** con la falla frente a 1 sin ella (de 15 positivos).
- Brecha de recall acumulada: con falla 0.165; sin falla 0.138. Brecha de FPR: con falla 0.168; sin falla 0.144.
- Las brechas se reportan en valor absoluto; el sentido (qué grupo queda por encima) se ve en `reports/lab13/simulacro/monitor_grupos.csv`. Una brecha puede cambiar de sentido casi sin cambiar de tamaño.


## Lectura por grupo (el valor absoluto de la brecha esconde el sentido)

| | Sin falla (B) | Con falla (C) |
|---|---|---|
| Recall G1 | 0.653 | 0.653 |
| Recall G2 | 0.791 | 0.488 |
| Brecha de recall (G2 − G1) | +0.138 | -0.165 |
| FPR G1 | 0.231 | 0.231 |
| FPR G2 | 0.375 | 0.062 |
| Brecha de FPR (G2 − G1) | +0.144 | -0.168 |

La brecha de recall cambia de sentido (de +0.138 a -0.165); su tamaño absoluto pasa de 0.138 a 0.165. La FPR de G2 baja de 0.375 a 0.062: una FPR menor no es una mejora si el modelo dejó de marcar casos que sí requerían revisión.

Riesgo de "nivelar hacia abajo": una brecha puede cerrarse porque el grupo desfavorecido empeora y no porque mejore el otro. Por eso el monitoreo no se apoya solo en brechas: el recall global y las señales de datos también activan REVIEW.

## Línea de tiempo

| UTC | Paso | Rol | Automático | Detalle |
|---|---|---|---|---|
| 2026-10-31T17:47:23+00:00 | 0 línea base | ML Engineer | sí | modelo logistic_sin_age entrenado con 480 casos; ventanas A=80, B=80 |
| 2026-10-31T17:47:23+00:00 | 1 detección | ML Engineer | sí | monitoreo en C_con_falla: 5 señal(es) REVIEW/STOP; la primera ventana con falla ya dispara la alerta |
| 2026-10-31T17:47:23+00:00 | 2 contención | ML Engineer | sí | modelo deshabilitado; modo baseline_manual_fifo; el Institutional Owner debe autorizar la reanudación |
| 2026-10-31T17:47:23+00:00 | 3 evidencia | Operator | sí | 11 archivos con SHA-256; verificación inmediata sin cambios: True |
| 2026-10-31T17:47:23+00:00 | 4 comunicación | Product Owner | no (humano) | borradores interno y externo preparados; pendientes de aprobación humana |
| 2026-10-31T17:47:23+00:00 | 5 impacto | Data Scientist | sí | 18 predicciones cambiaron por la falla; positivos no priorizados en la fuente afectada: 14 (sin falla: 1) |
| 2026-10-31T17:47:23+00:00 | 6 reversión | ML Engineer | sí | línea base manual: recall esperado 0.533 con la misma capacidad frente a 0.717 del modelo |
| 2026-10-31T17:47:23+00:00 | 7 recuperación | Data Engineer | sí | ventana B con la fuente corregida: estado GO; falta una segunda evaluación limpia y la firma del Institutional Owner |

## Qué funcionó y qué no

- Funcionó: la señal de datos (proporción de ceros y PSI) se evalúa al llegar el lote, sin esperar etiquetas; las de rendimiento dependen de la revisión humana y llegan con retraso.
- Limitación: con ventanas pequeñas las brechas por grupo no tienen soporte y se reportan como SIN_EVIDENCIA, nunca como OK.
- Limitación: los umbrales de PSI son una regla práctica; una señal puede quedar apenas por encima del umbral (véase el valor de `drift_psi` en la tabla) y debe recalibrarse con datos reales.
- Limitación: el recall puntual de una ventana pequeña es ruidoso y puede dar REVIEW sin falla real (véase el escenario A).
- Limitación: el escenario es una falla total y obvia del campo. Fallas parciales o sutiles pueden no activar estos umbrales.
- Costo de la reversión: la revisión por orden de llegada con la misma capacidad tiene recall esperado 0.533 frente a 0.717 del modelo.

## Evidencia preservada

`reports/lab13/simulacro/evidence_manifest.json` registra SHA-256 de 11 archivos (datos, configuración, modelo, señales y ventana con falla). Verificación inmediata sin cambios: True.

## Causa raíz

Inyectada por diseño: pérdida del campo `previous_incidents` en la fuente de `G2`. En un incidente real la causa se confirmaría con el sistema de origen antes de cerrar.

## Acciones correctivas (propuestas)

| Acción | Responsable | Fecha límite |
|---|---|---|
| Añadir al contrato de datos una prueba que rechace lotes con un campo requerido constante | Data Engineer | 2026-11-07 |
| Documentar con el sistema de origen quién avisa cambios de esquema | Product Owner | 2026-11-10 |
| Recalibrar umbrales de PSI y de ceros con datos reales antes de operar | ML Engineer | 2026-11-14 |
| Revisar de nuevo los casos del periodo afectado | Operator | 2026-11-07 |
| Probar el simulacro con una falla parcial y repetirlo | Data Scientist | 2026-11-21 |

## Condición para levantar el REVIEW

Dos evaluaciones consecutivas sin señales REVIEW o STOP y autorización escrita del **Institutional Owner**. Estado del simulacro: 1 de 2 evaluaciones limpias (ventana B sin falla: GO); falta la segunda evaluación y la firma. Reanudar no se decide por script.
