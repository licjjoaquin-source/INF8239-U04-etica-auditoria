# Retención, minimización y eliminación

*Los plazos de esta política son **propuestas de la autora** para un eventual uso con datos reales. Ninguno es un plazo legal. Antes de usar datos reales debe revisarlos un profesional del derecho. El caso del curso es sintético y no tiene obligación de retención.*

## Principios aplicados

| Tipo | Principio | Fuente |
|---|---|---|
| Obligación legal (Ley 172-13, según el texto consultado) | Medidas técnicas, organizativas y de seguridad (art. 5.5 y 13.2); datos almacenados de modo que se pueda ejercer el acceso (art. 5.2 d); cancelación y supresión a solicitud, con respuesta en 10 días hábiles (arts. 6.5, 8 y 14); bloqueo durante la prescripción y supresión después (art. 15). | `docs/MARCO_NORMATIVO.md` |
| Marco voluntario | NIST AI RMF (GOVERN y MAP): inventario de datos y documentación. Datasheets: la sección de mantenimiento. | NIST AI 100-1; Gebru et al. |
| Recomendación ética (propia) | Recolectar y conservar lo mínimo; separar atributos sensibles; plazos cortos; evidencia de incidentes conservada con hashes. | Esta política |

En el texto consultado de la Ley 172-13 no encontré un principio explícito que limite el plazo de conservación al necesario para la finalidad. Por eso los plazos de abajo son una recomendación ética propia y no una exigencia legal.

## Minimización aplicada (con evidencia)

1. **Sin identificadores directos.** El contrato rechaza `name`, `document_number`, `email` y `phone` y la señal `data_contract` detiene el sistema si aparecen (`tests/test_privacy.py` y `tests/test_e08_artifacts.py`).
2. **Atributos sensibles fuera del modelo.** `protected_group` nunca es predictor y `age_band` se retiró en el E07. Siguen en los datos solo para auditar.
3. **Fecha.** La fecha exacta aumenta la unicidad. `reports/e08/minimizacion_kanon.csv` mide el k mínimo y el porcentaje de filas en grupos de menos de 5 casos al combinar zona, edad y grupo con la fecha exacta, mes, trimestre y año. Regla derivada: en tablas compartidas se generaliza a año y se suprimen las celdas con menos de 5 casos.
4. **Agregados por defecto.** Los informes de auditoría son agregados; las celdas sin soporte se marcan y no se interpretan.

## Plazos propuestos

Cada plazo es **un valor único con su fecha de inicio**: no hay intervalos ni alternativas («o»). Todos son propuestas de la autora, no plazos legales.

| Activo | Plazo propuesto | Responsable de eliminar |
|---|---|---|
| Registros de casos (datos reales) | 12 meses desde el cierre del caso y de su apelación; luego se eliminan | Data Engineer |
| Tablas de auditoría agregadas | 24 meses desde su generación | Data Scientist |
| Modelo elegido (`models/logistic_sin_age.joblib`) | 12 meses desde que se retira de uso la versión | ML Engineer |
| Decisión de puertas (`reports/lab13/deployment_decision.json`) | 24 meses desde que se retira de uso la versión que describe | Product Owner |
| Registro de revisión del operador | 12 meses desde la fecha del registro | Operator |
| Registro de apelaciones | 24 meses desde el cierre de la apelación | Institutional Owner |
| Evidencia de incidentes (con hashes) | 36 meses desde el cierre del postmortem y de sus acciones | Institutional Owner |

Notas:
- Los agregados que se derivan de los registros de casos antes de eliminarlos siguen la fila de las tablas de auditoría (24 meses desde su generación); no contienen casos.
- La evidencia de incidentes se limita a las columnas necesarias y no es una copia completa del registro del caso; por eso puede conservarse más tiempo (36 meses) que el registro de casos (12 meses).
- El registro de apelaciones guarda solo la clave del caso, fechas y resultado.

## Eliminación

- La eliminación la ejecuta el responsable de la tabla y la **autoriza el Accountable** (Institutional Owner, `student_inputs/raci.csv`).
- Se deja constancia de qué se eliminó, cuándo y por quién; no se conservan copias en el repositorio.
- Una solicitud de eliminación de una persona afectada se atiende con prioridad y se responde por escrito (10 días hábiles es el plazo que fija el art. 8 para reclamos de rectificación y supresión, según el texto consultado).
- Los datos que ya están en un repositorio público no se pueden retirar de verdad: por eso **no se suben datos reales**.

## Límites de esta política

- No se ha probado con un caso real de eliminación.
- Los plazos no se han contrastado con una norma ni con un asesor jurídico.
- El inventario cubre las columnas del archivo y los activos derivados conocidos; los registros de operador y de apelaciones aún no existen en el piloto sintético.
