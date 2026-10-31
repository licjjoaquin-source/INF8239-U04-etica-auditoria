# Marco normativo: obligación legal, marco voluntario y recomendación ética

*Interpretación de la autora con fines académicos; no es asesoría legal. Consultado el 30/10/2026. Antes de cualquier uso con datos reales debe revisarlo un profesional del derecho.*

## 1. Obligación legal (vinculante)

| Norma | Qué exige | Aplicación a este proyecto |
|---|---|---|
| **Ley 172-13 sobre protección de datos de carácter personal** (República Dominicana, promulgada el 13/12/2013) | Según el texto consultado: calidad de los datos (art. 5, num. 2), consentimiento libre, expreso e informado (art. 5, num. 4), seguridad (art. 5, num. 5), confidencialidad (art. 5, num. 6); definición de datos sensibles (art. 6) y consentimiento escrito para tratarlos (arts. 75 y 76); derechos de acceso, rectificación y cancelación (arts. 7 a 15) y acción de *habeas data* (arts. 17 a 24). | El caso del laboratorio usa **datos sintéticos** (`docs/DATASET_CARD.md`), por lo que no trata datos personales reales. Si se alimentara con datos de personas reales, aplicaría la ley: base legal o consentimiento, minimización, seguridad y vías de acceso y rectificación. |

Límites de lo verificado:
- El texto consultado **no contiene una regla explícita sobre decisiones automatizadas**; solo menciona el *credit score* en el contexto de las sociedades de información crediticia (arts. 6 y 25).
- **No existe una ley de inteligencia artificial vigente en República Dominicana.** Según fuentes secundarias consultadas hay proyectos en trámite (Cámara de Diputados y Senado) y una discusión de reforma de la Ley 172-13 cuyo estado no pude confirmar con fuente oficial. Son propuestas: no generan obligaciones hoy.

## 2. Marco voluntario (buenas prácticas, no vinculantes)

| Marco | Cómo se usa aquí |
|---|---|
| **NIST AI Risk Management Framework 1.0** (DOI 10.6028/NIST.AI.100-1) | Organiza la evidencia en GOVERN, MAP, MEASURE y MANAGE (`docs/rmf_mapping.csv`). Que exista un archivo no prueba que el control sea eficaz. |
| **Recomendación de la OCDE sobre IA** (DOI 10.1787/cc2e1d3e-en) | Referencia de principios: transparencia, robustez, rendición de cuentas y supervisión humana. |
| **Estrategia Nacional de Inteligencia Artificial de República Dominicana (2023)** | Política pública no vinculante; hoja de ruta del Estado, no una obligación para este proyecto. |
| **Model Cards** (Mitchell et al., DOI 10.1145/3287560.3287596) y **Datasheets for Datasets** (Gebru et al., DOI 10.1145/3458723) | Formato de documentación del modelo y del dataset. |
| **Fairlearn** (documentación oficial, *Performing a Fairness Assessment*) | Método de la auditoría por grupo. |

## 3. Recomendación ética (decisión de la autora, no exigida por ninguna norma)

- La revisión humana es obligatoria y el puntaje nunca descarta un caso.
- Ningún grupo se interpreta sin soporte mínimo (20 casos, 10 positivos y 10 negativos) y toda brecha se reporta con intervalo.
- No se usa el puntaje para elegibilidad, intervención automática ni declaración de emergencia.
- La edad se retira de los predictores y se conserva solo para auditar, por minimización aunque ninguna norma lo exija.
- Existe una vía de apelación con respuesta humana en un plazo propuesto de 10 días hábiles. Ese plazo lo elegí yo para apelar una priorización y no lo exige ninguna norma. Coincide con los 10 días hábiles que el art. 8 de la Ley 172-13 fija, según el texto consultado, para atender reclamos de rectificación, actualización o supresión de datos; es una analogía, no un plazo legal para apelar un puntaje.
- Una brecha observada obliga a investigar; no se presenta como prueba de discriminación causal ni como prueba de justicia.

## Resumen de la separación

| | Obligatorio | Voluntario | Ético (propio) |
|---|---|---|---|
| Protección de datos personales | Ley 172-13 | NIST, OECD | Minimización de atributos sensibles |
| Equidad entre grupos | No hay norma específica de IA vigente | NIST MEASURE, Fairlearn | Tolerancia de 0.16 y soporte mínimo |
| Supervisión humana y apelación | No exigida expresamente para sistemas de IA | NIST MANAGE, OCDE | Revisión obligatoria y plazo de respuesta |

## 4. Conservación, minimización y monitoreo (E08)

| Tema | Obligación legal (Ley 172-13, texto consultado el 31/10/2026) | Marco voluntario | Recomendación ética (propia) |
|---|---|---|---|
| Conservación y eliminación | Acceso del titular (art. 5.2 d); cancelación y supresión a solicitud, respuesta en 10 días hábiles (arts. 6.5, 8 y 14); bloqueo durante la prescripción y supresión después (art. 15). No encontré un principio explícito que limite el plazo de conservación a la finalidad. | NIST AI RMF (GOVERN, MAP); Datasheets (mantenimiento) | Plazos cortos de `docs/RETENCION.md`; evidencia de incidentes con hashes |
| Seguridad | Medidas técnicas y organizativas (art. 5.5); conservar la información sin riesgo de adulteración (art. 13.2) | NIST AI RMF (MANAGE) | Manifiesto SHA-256 de la evidencia; acceso por rol |
| Estadística o investigación | Los datos sensibles pueden tratarse con fines estadísticos o científicos si no se puede identificar a sus titulares (art. 75, último párrafo); art. 72 excluye datos no atribuibles a una persona | OCDE: transparencia | Reportar solo agregados con soporte mínimo |
| Monitoreo y respuesta a incidentes | El texto consultado no trae una obligación de monitoreo de sistemas de IA ni de notificar incidentes de IA | NIST AI RMF (MEASURE y MANAGE); Model Cards | `configs/monitoring.yml`, `docs/RUNBOOK.md` y simulacro |

El texto web consultado terminaba en el art. 83; los artículos posteriores no pude leerlos. Esta tabla es mi interpretación académica y no es asesoría legal.
