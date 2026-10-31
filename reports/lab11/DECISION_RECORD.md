# Registro de decisión · Territorial Review DSS (sintético)

**Fecha:** 30/10/2026 · **Responsable final (Accountable):** Institutional Owner · **Autora del análisis:** Johanna Joaquín

## Decisión: LIMITAR (estado REVIEW)

Usar el modelo logístico **sin `age_band`** únicamente como ayuda para ordenar la revisión humana, en un piloto con datos sintéticos o de aula. No se despliega en operación real, no decide elegibilidad ni intervenciones, y no se adopta el árbol de decisión.

## Evidencia

| Modelo | Recall | FPR | Brecha de recall (G2−G1) | Brecha de FPR | Puertas |
|---|---|---|---|---|---|
| logistic | 0.717 | 0.279 | 0.138 (IC -0.045 a 0.318) | 0.125 (IC -0.135 a 0.398) | GO |
| tree | 0.717 | 0.309 | 0.181 (IC -0.003 a 0.357) | 0.168 (IC -0.098 a 0.438) | REVIEW (falla ambas brechas) |
| logistic sin age_band | 0.717 | 0.265 | 0.138 (IC -0.044 a 0.314) | 0.144 (IC -0.107 a 0.420) | GO |

Puertas de `configs/governance.yml`: recall mínimo 0.68, brechas máximas 0.16. Fuente: `reports/e07/variants_summary.csv` (conciliado con las cifras de Fairlearn del LAB12).

## Incertidumbre

- La prueba tiene 160 casos y G2 solo 59 (16 negativos): los intervalos de las brechas de recall y de FPR cruzan la tolerancia, así que "pasa las puertas" no equivale a "es equitativo".
- La tasa de selección de G2 es mayor que la de G1 (diferencia 0.232, IC 0.077 a 0.387), pero la tasa base también (prueba: 0.729 en G2 contra 0.485 en G1). Esa brecha exige investigación; no prueba discriminación causal.
- Solo 2 de 8 celdas interseccionales tienen soporte suficiente y ninguna de G2: no se interpretan.
- Proxies: la asociación de zona y edad con el grupo es baja (V de Cramér 0.039 y 0.025) y predecir el grupo con los predictores da 0.664 frente a 0.619 de la referencia: señal débil, que no se puede descartar con 640 filas.
- Retirar `age_band` no reduce la brecha de recall (0.138 igual que antes) ni cuesta utilidad (recall 0.717; exactitud 0.725 frente a 0.719). Se retira por minimización, no por haber corregido la brecha.

## Tres riesgos prioritarios (registro puntuado)

1. **R01 (16)**: falso negativo; el 28 % de los positivos no se prioriza. Control: revisión humana obligatoria; el puntaje no descarta casos.
2. **R02 (9)**: carga de revisión desigual sobre G2 (selección y FPR más altos). Control: reportar por grupo con IC e investigar antes de cambiar el modelo.
3. **R07 (8)**: uso fuera de alcance. Control: usos prohibidos en `governance.yml` y un solo Accountable; es un control documental, sin barrera técnica.

## Alternativas y trade-offs

- **Alternativa no predictiva** (cola cronológica o regla simple por incidentes previos): no se comparó todavía; es el siguiente paso para justificar el modelo.
- **Árbol:** más grande (7.9 KB contra 3.6 KB) y falla las dos puertas de brecha; descartado.
- **Cambiar el umbral:** a 0.40 el recall sube a 0.848 y las brechas bajan (recall 0.067, FPR 0.096), pero la FPR sube a 0.426: más falsos positivos y más carga de revisión. Se calculó sobre la misma prueba, así que no se adopta sin validación separada.
- **Costo computacional:** los modelos entrenan en menos de 0.1 s y pesan entre 3 y 8 KB; el costo no discrimina, la decisión se toma por equidad y riesgo.

## Condición de retiro

Volver a revisión manual si, con soporte suficiente (al menos 20 casos, 10 positivos y 10 negativos por grupo), la brecha de recall o de FPR supera 0.16, el recall global baja de 0.68, o se detecta un uso fuera de alcance.

## Apelación y supervisión humana

Toda persona afectada o su representante puede pedir revisión humana de su priorización; el Product Owner responde por escrito en un plazo propuesto de 10 días hábiles y deja registro. El operador registra si acepta o anula cada recomendación.

## Pendiente

Runbook de incidentes y Model Card (LAB13), comparación con la alternativa no predictiva y más casos de G2.
