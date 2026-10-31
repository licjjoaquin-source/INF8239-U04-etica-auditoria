"""LAB11 - Evaluación de impacto ético (versión corregida del script base).

Cambios respecto al script del proyecto base:
  * las cadenas de varias líneas usan comillas triples (el original tenía saltos de línea
    dentro de comillas simples y no se podía ejecutar: SyntaxError);
  * NO sobrescribe reports/lab11/DECISION_RECORD.md si ya existe, para no perder la
    decisión escrita por la estudiante cada vez que se reejecuta.
"""
import json
from pathlib import Path

import pandas as pd
import yaml

from inf8239_u04.impact import score_risks, validate_impact

out = Path("reports/lab11")
out.mkdir(parents=True, exist_ok=True)
impact = yaml.safe_load(Path("student_inputs/lab11_impact.yml").read_text(encoding="utf-8"))
validate_impact(impact)
stake = pd.read_csv("student_inputs/stakeholders.csv")
if stake.astype(str).apply(lambda s: s.str.contains("REPLACE")).any().any():
    raise ValueError("Complete stakeholders.csv")
risks = score_risks(pd.read_csv("student_inputs/risk_register.csv"))
risks.to_csv(out / "risk_register_scored.csv", index=False)
stake.to_csv(out / "stakeholders.csv", index=False)
(out / "rmf_summary.json").write_text(
    json.dumps({"GOVERN": "owner and policy", "MAP": f"{len(risks)} documented risks",
                "MEASURE": "LAB12 pending", "MANAGE": "withdrawal and appeal documented"}, indent=2),
    encoding="utf-8")
record = out / "DECISION_RECORD.md"
if record.exists():
    print(f"{record} ya existe: no se sobrescribe")
else:
    record.write_text("# Decision record\n\nREPLACE with evidence, uncertainty, owner and GO/REVIEW/STOP.\n",
                      encoding="utf-8")
print(risks[["id", "priority", "owner"]].head(3).to_string(index=False))
