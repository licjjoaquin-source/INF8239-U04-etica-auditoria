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
- Existe una vía de apelación con respuesta humana en un plazo propuesto de 10 días hábiles. Ese plazo es mío; no proviene de ninguna ley.
- Una brecha observada obliga a investigar; no se presenta como prueba de discriminación causal ni como prueba de justicia.

## Resumen de la separación

| | Obligatorio | Voluntario | Ético (propio) |
|---|---|---|---|
| Protección de datos personales | Ley 172-13 | NIST, OECD | Minimización de atributos sensibles |
| Equidad entre grupos | No hay norma específica de IA vigente | NIST MEASURE, Fairlearn | Tolerancia de 0.16 y soporte mínimo |
| Supervisión humana y apelación | No exigida expresamente para sistemas de IA | NIST MANAGE, OCDE | Revisión obligatoria y plazo de respuesta |
