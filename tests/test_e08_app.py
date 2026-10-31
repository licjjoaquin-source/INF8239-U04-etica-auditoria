"""El tablero debe mostrar el modelo que decidió la gobernanza y la supervisión humana."""
from pathlib import Path

import yaml
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def _page_text(at) -> str:
    parts = []
    for group in (at.markdown, at.caption, at.info, at.subheader, at.warning):
        parts.extend(str(x.value) for x in group)
    return " ".join(parts)


def test_app_shows_the_selected_model_and_human_oversight():
    decision = yaml.safe_load((ROOT / "student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
    at = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not at.exception
    text = _page_text(at)
    assert decision["selected_model"] in text, "el tablero debe nombrar el modelo elegido"
    assert "age_band" in text, "debe declarar el predictor excluido"
    assert decision["recommendation"].split(":")[0].lower() in text.lower(), "debe mostrar la recomendación vigente (p. ej. Limitar)"
    assert "acción humana" in text.lower() and "apelación" in text.lower() and "retiro" in text.lower()
    assert any(m.label == "Recall" for m in at.metric)
    assert any("sintético" in str(w.value).lower() for w in at.warning)
