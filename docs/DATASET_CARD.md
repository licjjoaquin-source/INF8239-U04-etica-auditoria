# Datasheet / Dataset Card · Territorial risk (sintético)

*Basado en Datasheets for Datasets (Gebru et al., DOI 10.1145/3458723). Las cifras de la tabla de trazabilidad se verifican con pruebas contra `reports/e08/dataset_stats.json` y `reports/e07/base_rates.csv`.*

## 1. Motivación

- **Para qué se creó:** practicar contratos de datos, evaluación temporal, auditoría por subgrupos y gobernanza en un DSS (LAB11–LAB13).
- **Quién lo creó y quién lo financia:** material del curso INF-8239 (UASD), generado con una semilla fija educativa. No hay financiador ni operación real.
- **Qué NO es:** no contiene personas, lugares, tasas ni estadísticas oficiales de la República Dominicana.

## 2. Composición

- **Qué representa cada fila:** un caso sintético que llega para revisión. Columnas: `case_id`, `received_date`, `zone`, `protected_group`, `age_band`, `previous_incidents`, `infrastructure_score`, `exposure`, `target`. Su clasificación (identificador sustituto, cuasi-identificador, sensible, predictor, etiqueta) está en `docs/INVENTARIO_DATOS.csv`.
- **Etiqueta:** `target` = 1 si el caso requiere revisión.
- **Grupos:** `protected_group` toma los valores G1 y G2, que son **etiquetas abstractas**. No corresponden a ninguna población real y por eso no se interpretan como tales. Se usan solo para auditar y nunca son predictores.
- **Datos faltantes y duplicados:** se miden con `scripts/e08_inventario.py` (campos `missing_cells` y `duplicated_case_id` de `dataset_stats.json`).
- **Identificadores directos:** el contrato de datos rechaza `name`, `document_number`, `email` y `phone`.
- **Datos sensibles:** `protected_group` y `age_band` están declarados sensibles en `configs/governance.yml`.

### Tabla de trazabilidad (verificada por pruebas)

| Dato | Valor | Fuente |
|---|---|---|
| n_rows | 640 | reports/e08/dataset_stats.json |
| n_train | 480 | reports/e08/dataset_stats.json |
| n_test | 160 | reports/e08/dataset_stats.json |
| G1_n | 396 | reports/e07/base_rates.csv |
| G2_n | 244 | reports/e07/base_rates.csv |
| G1_target_rate | 0.497 | reports/e07/base_rates.csv |
| G2_target_rate | 0.639 | reports/e07/base_rates.csv |
| G1_test_target_rate | 0.485 | reports/e07/base_rates.csv |
| G2_test_target_rate | 0.729 | reports/e07/base_rates.csv |

El rango de fechas, el hash del archivo y el k-anonimato están en `reports/e08/dataset_stats.json` y `reports/e08/minimizacion_kanon.csv`.

## 3. Proceso de recolección

Los datos no se recolectaron: se generaron con un programa. El mecanismo que relaciona los predictores con la etiqueta **no está documentado en el proyecto base**, así que no puedo afirmar qué tan realistas son esas relaciones. Los resultados sirven para practicar el método, no para sacar conclusiones sobre ningún territorio.

## 4. Preprocesamiento, limpieza y etiquetado

- El contrato (`validate_schema`) exige las columnas requeridas, rechaza identificadores directos y un `target` no binario.
- Partición temporal: el 75 % más antiguo para entrenar y el 25 % más reciente para evaluar. La fecha exacta no es predictor.
- `age_band` se retira de los predictores del modelo elegido (decisión del E07). Se conserva en los datos solo para auditar.

## 5. Usos

- **Previstos:** práctica de auditoría y gobernanza; piloto de aula con revisión humana.
- **Prohibidos:** perfilamiento operativo, inferencias sobre poblaciones reales, intervención automática, elegibilidad y declaración de emergencia.
- **Riesgos de uso indebido:** presentar resultados sintéticos como evidencia sobre grupos reales; interpretar G1 y G2 como poblaciones concretas.

## 6. Distribución

Material de curso. El repositorio no incluye datos personales. El archivo es sintético y puede compartirse con el proyecto; si algún día se reemplazara por datos reales, no debe subirse a un repositorio público.

## 7. Mantenimiento

- **Responsable:** Data Engineer (R) y Product Owner (A), según `student_inputs/raci.csv`.
- **Actualización:** una versión nueva del archivo exige repetir `scripts/e08_inventario.py` y las pruebas.
- **Retención y eliminación:** ver `docs/RETENCION.md`.
