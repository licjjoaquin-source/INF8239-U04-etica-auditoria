"""LAB13 - Simulacro de incidente (versión corregida del script base).

Corrige las cadenas de varias líneas (comillas triples) y no sobrescribe el
postmortem si ya existe, para conservar lo que la estudiante complete.
"""
from datetime import datetime, timezone
from pathlib import Path

path = Path("reports/lab13/INCIDENT_POSTMORTEM.md")
path.parent.mkdir(parents=True, exist_ok=True)
if path.exists():
    print(f"{path} ya existe: no se sobrescribe")
else:
    text = f"""# Incident simulation

- detected_at: {datetime.now(timezone.utc).isoformat()}
- signal: recall gap exceeded
- containment: REVIEW and safe baseline
- evidence: preserved report and model version
- communication: REPLACE
- corrective actions, owners and dates: REPLACE
"""
    path.write_text(text, encoding="utf-8")
    print(path)
