# Model Card · Territorial Review DSS (sintético) · modelo `logistic_sin_age`

*Basada en Model Cards for Model Reporting (Mitchell et al., DOI 10.1145/3287560.3287596). Las cifras de la tabla de trazabilidad se verifican con pruebas contra `reports/e07/variants_summary.csv`. Estado de la decisión: LIMITAR (REVIEW).*

## Detalles del modelo

- **Tipo:** regresión logística (`class_weight="balanced"`, `max_iter=1200`, `random_state=42`) con codificación one-hot de `zone` y estandarización de `previous_incidents`, `infrastructure_score` y `exposure`.
- **Sin `age_band`:** se retiró de los predictores por minimización (decisión del E07). No se usa `protected_group`.
- **Versión:** la del commit de Git etiquetado `u04-e08`; el archivo del modelo es `models/logistic_sin_age.joblib` (hash en el manifiesto del simulacro).
- **Alternativas evaluadas:** regresión logística con `age_band` y árbol de decisión de profundidad 5 (tabla de Green AI).

## Intended use

Ayudar a una persona a **ordenar la revisión** de casos sintéticos: el puntaje prioriza qué caso mirar primero. La decisión sobre cada caso la toma siempre una persona, que puede anular la recomendación. Uso previsto: piloto de aula con datos sintéticos.

## Out-of-scope use

No usar para decidir elegibilidad, intervención automática, declaración de emergencia, culpabilidad ni perfilamiento de personas reales. No usar con datos reales ni en operación real mientras la decisión siga en LIMITAR. Estos usos están prohibidos en `configs/governance.yml`; es un control documental, sin barrera técnica.

## Data and split

Dataset sintético de 640 casos (`docs/DATASET_CARD.md`). Partición **temporal**: los 480 casos más antiguos para entrenar y los 160 más recientes para evaluar. Los grupos G1 y G2 son etiquetas abstractas usadas solo para auditar. La tasa del target en G2 pasa de 0.611 (entrenamiento) a 0.729 (prueba): hay deriva de base entre ambos periodos.

## Global and subgroup evaluation

Prueba de 160 casos, umbral 0.50.

| Métrica | Valor | Fuente |
|---|---|---|
| accuracy | 0.725 | reports/e07/variants_summary.csv |
| recall | 0.717 | reports/e07/variants_summary.csv |
| fpr | 0.265 | reports/e07/variants_summary.csv |
| selection_rate | 0.525 | reports/e07/variants_summary.csv |
| recall_diff | 0.138 | reports/e07/variants_summary.csv |
| fpr_diff | 0.144 | reports/e07/variants_summary.csv |
| recall_ci_lo | -0.044 | reports/e07/variants_summary.csv |
| recall_ci_hi | 0.314 | reports/e07/variants_summary.csv |
| fpr_ci_lo | -0.107 | reports/e07/variants_summary.csv |
| fpr_ci_hi | 0.420 | reports/e07/variants_summary.csv |

Por grupo (`reports/e07/group_support_logistic_sin_age.csv`): G1 tiene 101 casos (49 positivos y 52 negativos), recall 0.653 y FPR 0.231. G2 tiene 59 casos (43 positivos y solo 16 negativos), recall 0.791 y FPR 0.375 con intervalo de 0.185 a 0.614. Las brechas se calculan como G2 menos G1.

**Cómo leerlo.** Las dos brechas están por debajo de la tolerancia de 0.16 y las puertas dan GO, pero los intervalos cruzan la tolerancia, así que "pasa las puertas" no demuestra equidad. La tasa de selección de G2 es mayor y su tasa base también: la brecha exige investigar, no prueba discriminación causal. Solo 2 de 8 celdas interseccionales tienen soporte suficiente (mínimo propuesto: 20 casos, 10 positivos y 10 negativos); ninguna es de G2 y las demás no se interpretan.

## Green AI evidence

| Variante | Exactitud | Recall | Tamaño del modelo | Puertas |
|---|---|---|---|---|
| logistic | 0.719 | 0.717 | 3.6 KB | GO |
| tree | 0.706 | 0.717 | 7.9 KB | REVIEW |
| logistic_sin_age | 0.725 | 0.717 | 3.3 KB | GO |

Los tres entrenan en menos de 0.1 s en un portátil y predicen en menos de 1 ms por caso, muy por debajo de los límites de 500 ms y 1024 KB. El costo computacional no discrimina entre variantes; la decisión se tomó por equidad y riesgo. Los tiempos dependen del equipo y no se usan como prueba.

## Limitations, human oversight and appeal

- Prueba de solo 160 casos; G2 con pocos negativos: la FPR de G2 es muy incierta. El barrido de umbral se calculó sobre la misma prueba y no se adopta sin validación separada.
- Los datos son sintéticos y su mecanismo generador no está documentado; nada de lo anterior vale para una población real.
- No se comparó con una alternativa no predictiva más allá de la cola por orden de llegada del simulacro (`reports/lab13/simulacro/safe_mode.json`).
- **Supervisión humana:** revisión obligatoria; el puntaje nunca descarta un caso. El operador registra acuerdo o desacuerdo (registro aún no implementado en el piloto sintético).
- **Apelación:** revisión humana con respuesta escrita en un plazo propuesto de 10 días hábiles (no es un plazo legal para apelar un puntaje).
- **Monitoreo y retiro:** `configs/monitoring.yml` y `docs/RUNBOOK.md`. Se vuelve a revisión manual si una brecha de recall o de FPR supera 0.16 con soporte suficiente, si el recall global baja de 0.68 o si se detecta un uso fuera de alcance.

## Owner and review date

- **Responsable final (Accountable):** Institutional Owner. **Responsable del modelo:** Data Scientist (Model Card) y ML Engineer (operación), según `student_inputs/raci.csv`.
- **Fecha de elaboración:** 31/10/2026. **Próxima revisión:** 30/11/2026, o antes si el monitoreo da REVIEW o STOP o cambia el modelo o la fuente de datos.
