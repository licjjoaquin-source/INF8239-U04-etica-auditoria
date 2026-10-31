"""LAB13 - Pipeline gobernado. Versión del E08: usa el modelo elegido en student_inputs/lab12_decision.yml.

Con selected_model: logistic_sin_age entrena sin age_band (decisión del E07) y guarda el modelo en
models/logistic_sin_age.joblib. Si falta la clave, usa el modelo logístico base.
"""
import json
from pathlib import Path

import pandas as pd
import yaml

from inf8239_u04.data import load_data
from inf8239_u04.governance import load_config, validate_raci
from inf8239_u04.pipeline import run

VARIANTS = {"logistic": ("logistic", ()), "tree": ("tree", ()), "logistic_sin_age": ("logistic", ("age_band",))}

cfg = load_config()
validate_raci(pd.read_csv("student_inputs/raci.csv"))
decision = yaml.safe_load(Path("student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
selected = str(decision.get("selected_model", "logistic"))
kind, drop = VARIANTS[selected]
result = run(load_data(), cfg["gates"], kind=kind, drop=drop, output=f"models/{selected}.joblib")
out = Path("reports/lab13")
out.mkdir(parents=True, exist_ok=True)
payload = {"selected_model": selected, "dropped_features": list(drop), "metrics": result["metrics"], "gaps": result["gaps"],
           "resources": result["resources"], "decision": result["decision"]}
(out / "deployment_decision.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
result["by_group"].to_csv(out / "fairness_by_group.csv")
print(selected, result["decision"])
