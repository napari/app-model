import runpy
from pathlib import Path

import pytest
from qtpy.QtWidgets import QApplication

DEMO = Path(__file__).parent.parent / "demo"


@pytest.mark.parametrize("fname", ["qapplication.py", "model_app.py"])
def test_qapp(fname, monkeypatch):
    monkeypatch.setattr(QApplication, "exec_", lambda *a, **k: None)
    runpy.run_path(str(DEMO / fname), run_name="__main__")
