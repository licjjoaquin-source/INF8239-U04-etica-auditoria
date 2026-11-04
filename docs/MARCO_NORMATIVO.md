# Marco normativo: obligación legal, marco voluntario y recomendación ética

*Interpretación de la autora con fines académicos; no es asesoría legal. Consultas del 30/10/2026 y 31/10/2026; verificación ampliada el 04/11/2026 (sección 5). Antes de cualquier uso con datos reales debe revisarlo un profesional del derecho.*

## 1. Obligación legal (vinculante)

| Norma | Qué exige | Aplicación a este proyecto |
|---|---|---|
| **Ley 172-13 sobre protección de datos de carácter personal** (República Dominicana, promulgada el 13/12/2013) | Según la copia del texto que leí (no oficial, ver sección 5): calidad de los datos (art. 5, num. 2), consentimiento libre, expreso e informado (art. 5, num. 4), seguridad (art. 5, num. 5), confidencialidad (art. 5, num. 6); definición de datos sensibles (art. 6) y consentimiento escrito para tratarlos (arts. 75 y 76); derechos de acceso, rectificación y cancelación (arts. 7 a 15) y acción de *habeas data* (arts. 17 a 24). | El caso del laboratorio usa **datos sintéticos** (`docs/DATASET_CARD.md`), por lo que no trata datos personales reales. Si se alimentara con datos de personas reales, aplicaría la ley: base legal o consentimiento, minimización, seguridad y vías de acceso y rectificación. |

| **Decreto 787-26 (dado el 2/11/2026), Código de Ética de la Inteligencia Artificial para los Servicios Públicos** | Vinculante para los órganos y entes de la Administración Pública que diseñen, adquieran o usen sistemas de IA en servicios públicos, funciones administrativas o actos administrativos (arts. 2 y 3). Entre otras cosas (art. 11 y Código, sección II): registro institucional de sistemas, Evaluación de Impacto Ético y de Derechos (EIED) antes de poner en funcionamiento un sistema cuando corresponda, supervisión humana y monitoreo continuo, informar a las personas, vías de revisión humana y corrección de errores, comunicar incidentes y sesgos emergentes de sistemas de alto impacto, y medidas contra sesgos que pueden llegar a limitar, suspender o retirar el sistema. Plazo de adecuación de 180 días desde su publicación (art. 14). | **Condicional.** No aplica a un ejercicio de aula con datos sintéticos ni a un uso privado. Sí aplicaría si una institución pública usara el modelo para apoyar la preparación de decisiones administrativas, como priorizar casos (art. 3, b). Mi decisión de limitar, con revisión humana y sin elegibilidad automática, es coherente con ese marco, pero no la tomé por este decreto. |

Límites de lo verificado (detalle, fechas y fuentes en la sección 5):
- En la copia de la Ley 172-13 que leí (no oficial) **no encontré una regla explícita sobre decisiones automatizadas**; solo menciona el *credit score* en el contexto de las sociedades de información crediticia (arts. 6 y 25) y los perfiles con fines comerciales (art. 71). Es ausencia en la copia leída, no prueba de que la ley no regule el tema.
- **No encontré una *ley* de inteligencia artificial promulgada** en las fuentes oficiales que revisé el 04/11/2026; sí hay proyectos de ley en estudio y el decreto 787-26, que obliga a la Administración Pública. No consulté la Gaceta Oficial, el sistema legislativo completo ni la Cámara de Diputados, así que no afirmo que no exista ninguna otra norma aplicable.

## 2. Marco voluntario (buenas prácticas, no vinculantes)

| Marco | Cómo se usa aquí |
|---|---|
| **NIST AI Risk Management Framework 1.0** (DOI 10.6028/NIST.AI.100-1) | Organiza la evidencia en GOVERN, MAP, MEASURE y MANAGE (`docs/rmf_mapping.csv`). Que exista un archivo no prueba que el control sea eficaz. |
| **Recomendación de la OCDE sobre IA** (DOI 10.1787/cc2e1d3e-en) | Referencia de principios: transparencia, robustez, rendición de cuentas y supervisión humana. |
| **Estrategia Nacional de Inteligencia Artificial de República Dominicana (2023)** | Política pública aprobada por el Decreto 498-23: obliga a entidades del Poder Ejecutivo a coordinar y planificar sus proyectos de IA (arts. 9 a 11), no a particulares ni a este ejercicio. Es hoja de ruta, no una norma de conducta para sistemas de IA. |
| **Model Cards** (Mitchell et al., DOI 10.1145/3287560.3287596) y **Datasheets for Datasets** (Gebru et al., DOI 10.1145/3458723) | Formato de documentación del modelo y del dataset. |
| **Fairlearn** (documentación oficial, *Performing a Fairness Assessment*) | Método de la auditoría por grupo. |

## 3. Recomendación ética (decisión de la autora; en este contexto de aula y datos sintéticos no la exige ninguna norma que identifiqué; ver Decreto 787-26 si lo usara una institución pública)

- La revisión humana es obligatoria y el puntaje nunca descarta un caso.
- Ningún grupo se interpreta sin soporte mínimo (20 casos, 10 positivos y 10 negativos) y toda brecha se reporta con intervalo.
- No se usa el puntaje para elegibilidad, intervención automática ni declaración de emergencia.
- La edad se retira de los predictores y se conserva solo para auditar, por minimización, sin que ninguna norma que identifiqué la exija para este ejercicio.
- Existe una vía de apelación con respuesta humana en un plazo propuesto de 10 días hábiles. Ese plazo lo elegí yo para apelar una priorización y no lo exige ninguna norma. Coincide con los 10 días hábiles que el art. 8 de la Ley 172-13 fija, según el texto consultado, para atender reclamos de rectificación, actualización o supresión de datos; es una analogía, no un plazo legal para apelar un puntaje. Si lo usara una institución pública, el Decreto 787-26 deja los plazos máximos de respuesta a solicitudes de revisión humana a un órgano nacional de supervisión (Código, regla 12).
- Una brecha observada obliga a investigar; no se presenta como prueba de discriminación causal ni como prueba de justicia.

## Resumen de la separación

| | Obligatorio | Voluntario | Ético (propio) |
|---|---|---|---|
| Protección de datos personales | Ley 172-13 | NIST, OECD | Minimización de atributos sensibles |
| Equidad entre grupos | No identifiqué una norma específica de IA promulgada (sección 5) | NIST MEASURE, Fairlearn | Tolerancia de 0.16 y soporte mínimo |
| Supervisión humana y apelación | Solo si lo usa una institución pública: Decreto 787-26 (sección 5); fuera de eso no identifiqué exigencia | NIST MANAGE, OCDE | Revisión obligatoria y plazo de respuesta |

## 4. Conservación, minimización y monitoreo (E08)

| Tema | Obligación legal (Ley 172-13, texto consultado el 31/10/2026; el Decreto 787-26 solo para la Administración Pública) | Marco voluntario | Recomendación ética (propia) |
|---|---|---|---|
| Conservación y eliminación | Acceso del titular (art. 5.2 d); cancelación y supresión a solicitud, respuesta en 10 días hábiles (arts. 6.5, 8 y 14); bloqueo durante la prescripción y supresión después (art. 15). No encontré un principio explícito que limite el plazo de conservación a la finalidad. | NIST AI RMF (GOVERN, MAP); Datasheets (mantenimiento) | Plazos cortos de `docs/RETENCION.md`; evidencia de incidentes con hashes |
| Seguridad | Medidas técnicas y organizativas (art. 5.5); conservar la información sin riesgo de adulteración (art. 13.2) | NIST AI RMF (MANAGE) | Manifiesto SHA-256 de la evidencia; acceso por rol |
| Estadística o investigación | Los datos sensibles pueden tratarse con fines estadísticos o científicos si no se puede identificar a sus titulares (art. 75, último párrafo); art. 72 excluye datos no atribuibles a una persona | OCDE: transparencia | Reportar solo agregados con soporte mínimo |
| Monitoreo y respuesta a incidentes | La Ley 172-13 (texto consultado) no trae una obligación de monitoreo de sistemas de IA ni de notificar incidentes de IA. Para la Administración Pública, el Decreto 787-26 (art. 11, f, i y j) exige supervisión humana y monitoreo continuo, medidas ante sesgos y errores, y comunicar a DIGEIG y OGTIC los incidentes y sesgos emergentes de sistemas de alto impacto; no aplica a este ejercicio (sección 5) | NIST AI RMF (MEASURE y MANAGE); Model Cards | `configs/monitoring.yml`, `docs/RUNBOOK.md` y simulacro |

El texto web de la Ley 172-13 que consulté terminaba en el art. 83; los artículos posteriores no pude leerlos. Esta tabla es mi interpretación académica y no es asesoría legal.

## 5. Registro de verificación (consulta del 04/11/2026)

Distingo lo que **verifiqué en una fuente oficial**, lo que **solo leí en una fuente secundaria** y lo que **no verifiqué**. Es un registro de lo consultado, no una revisión exhaustiva de la legislación dominicana.

| Afirmación | Fuente consultada | Tipo | Qué confirma y qué no |
|---|---|---|---|
| La Ley 172-13 existe y protege de forma integral los datos personales; fecha 13/12/2013 | Senado de la República Dominicana, Departamento Técnico de Revisión Legislativa, opinión DETEREL 244/2021 (9/6/2021), repositorio memoriahistorica.senadord.gob.do | Oficial | Confirma número, objeto y fecha. El propio documento usa también "15 de diciembre" en un pasaje; no resolví la discrepancia con la Gaceta Oficial. |
| Contenido de los artículos 5, 6, 71, 75 y 76 (y los demás que cito) | Copias del texto en drlawyer.com y bdi.com.do | No oficial | No las cotejé con la Gaceta Oficial; una de ellas está truncada y tiene errores de transcripción. Las citas por artículo son provisionales. |
| En esa copia no encontré una regla sobre decisiones automatizadas | Mismas copias | No oficial | Solo hallé menciones tangenciales (art. 6, definición de datos informáticos y de puntaje de crédito; art. 71, perfiles con fines comerciales). Es ausencia en la copia leída, no prueba de que la ley no regule el tema. |
| Un proyecto de modificación de la Ley 172-13 (expediente 00486-2021) quedó perimido | Repositorio del Senado (ficha del expediente, período 2020-2024) | Oficial | Solo cubre ese expediente. Una reforma más reciente que se menciona en prensa y blogs (autoridad de protección de datos, derecho a no ser sujeto de decisiones automatizadas) **no la pude confirmar con fuente oficial**. |
| El 15/09/2026 la Comisión de Educación Superior, Ciencia y Tecnología del Senado acordó fusionar dos proyectos de IA (uso ético y seguro; lineamientos de políticas públicas) | senadord.gob.do (nota de prensa del 15/09/2026) | Oficial | La nota no informa de aprobación; no revisé el estado posterior del trámite ni el sistema legislativo completo. |
| Proyecto de ley de IA en la Cámara de Diputados (Tobías Crespo, 19/02/2025) | Prensa (acento.com.do) y blog de un consultor | Secundaria | No lo verifiqué en el sitio de la Cámara de Diputados. |
| El Decreto 787-26 (dado el 2/11/2026) aprueba el Código de Ética de la IA para los Servicios Públicos y es vinculante para la Administración Pública (arts. 2, 3, 11 y 14) | Copia en PDF con membrete de la Presidencia de la República (decreto de 14 páginas y Código, versión 1.0, julio 2026) | Oficial (copia del documento; no cotejada con la Gaceta Oficial) | No conozco su fecha de publicación (de la que corre el plazo de 180 días). Deja a un órgano nacional de supervisión la clasificación oficial por impacto (en 6 meses) y los plazos máximos de respuesta a solicitudes de revisión humana. No lo aplica al sector privado. Lo conocí después de la primera consulta del 04/11/2026, que no lo había encontrado. |
| La Estrategia Nacional de IA se aprobó por el Decreto 498-23 (11/10/2023); vigencia hasta el 31/12/2030; obliga a entidades del Poder Ejecutivo, no a empresas privadas (arts. 9 a 11) | Texto del decreto publicado por OGTIC (wp.ogtic.gob.do) | Oficial (copia publicada por la entidad) | No la cotejé con la Gaceta Oficial. Es política pública, no una ley sobre sistemas de IA. |

**Conclusión acotada.** A la fecha de consulta (04/11/2026), en las fuentes oficiales que revisé (sitio del Senado y decretos 498-23 y 787-26) **no encontré una *ley* de inteligencia artificial promulgada**; sí hay proyectos de ley en estudio y un decreto del Poder Ejecutivo (787-26) que obliga a la Administración Pública. No consulté la Gaceta Oficial, el sistema legislativo completo ni la Cámara de Diputados, así que no afirmo que no exista ninguna otra norma aplicable; antes de usar el sistema con datos reales debe revisarlo un profesional del derecho.

**Qué no cambia.** La decisión (limitar, revisión humana, datos sintéticos) no depende de este registro. Las medidas de supervisión humana, apelación, minimización y monitoreo son recomendaciones propias en este contexto; en una institución pública el Decreto 787-26 las exigiría en lo sustancial (supervisión humana, revisión humana, EIED previa, monitoreo continuo).
