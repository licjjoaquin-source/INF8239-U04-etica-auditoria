# Aplicación del expediente al trabajo final (TF.10: detección de spam en SMS)

*Esta sección usa el mismo método del E07 sobre el proyecto del trabajo final. Lo que aquí figura como "hipótesis" no es evidencia: debe comprobarse con los datos del equipo antes de afirmarlo.*

## Finalidad, interesados y proporcionalidad

- **Finalidad:** clasificar mensajes SMS como spam o legítimos (ham) para apoyar el filtrado.
- **Decisión asistida:** qué mensajes se marcan o se bloquean. Si el sistema bloquea sin revisión, la decisión deja de ser asistida.
- **Interesados:** receptores (quieren no recibir spam y no perder mensajes legítimos), remitentes legítimos (por ejemplo bancos o clínicas), el equipo que desarrolla el modelo y el operador o institución que lo usaría.
- **Alternativa no predictiva:** reglas simples (palabras clave, listas de remitentes) y el baseline que ya exige el trabajo. Un modelo más complejo debe justificarse frente a ellas.

## Daño prioritario (hipótesis)

Un **falso positivo** (un mensaje legítimo marcado como spam) puede ocultar un aviso importante, como un código de seguridad o una cita médica; un **falso negativo** deja pasar spam o fraude. Para el TF.10 propongo priorizar la FPR sobre mensajes legítimos y reportar también el recall de spam. El equipo debe confirmar esta prioridad.

## Auditoría por grupo: qué se puede y qué no

- El dataset UCI SMS Spam Collection **no trae atributos demográficos**, así que no se puede auditar por grupo protegido. Declarar "equidad por grupos" con este dataset sería inventar evidencia.
- Sí se pueden auditar **cortes observables**: longitud del mensaje, presencia de URL o de números, uso de mayúsculas, idioma. Hipótesis a verificar: que mensajes cortos o en otro idioma tengan más falsos positivos.
- **Riesgo de cobertura (hipótesis):** el dataset es en inglés y de otra época y contexto; un filtro entrenado así puede fallar con mensajes en español dominicano. Debe medirse con una muestra propia antes de afirmarlo.
- Con pocos mensajes por corte se aplican las mismas reglas del E07: soporte mínimo (n, positivos y negativos) e intervalos de incertidumbre.

## Cómo reutilizar el código del E07

`src/inf8239_u04/e07_stats.py` contiene `group_table` (soporte e intervalos de Wilson por corte), `bootstrap_difference` (brecha con IC) y `gap_status` (comparación con una tolerancia). Para el TF.10 basta pasar el corte (por ejemplo "mensaje corto o largo") como `groups`.

## Obligación legal, marco voluntario y recomendación ética

- **Legal:** los mensajes de personas reales son datos personales (Ley 172-13): exigen base legal, minimización y seguridad. Verificar el origen y la licencia del dataset y si contiene números telefónicos o datos identificables.
- **Voluntario:** NIST AI RMF y Model Card para documentar el modelo.
- **Ético:** revisión humana de los bloqueos, vía para recuperar un mensaje bloqueado por error y no usar el filtro para otro fin distinto del declarado.

## Decisión provisional

**Limitar:** usar el clasificador solo para *marcar* mensajes sospechosos, no para borrarlos, hasta medir la FPR por corte y con mensajes propios. Esta decisión debe revisarla el equipo con los resultados reales.
