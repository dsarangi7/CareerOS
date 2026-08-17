from pathlib import Path

from scripts.tasks import export_demo, seed


def test_seed_and_export_demo_workflow() -> None:
    seed()
    output = export_demo()

    assert Path(output).exists()
    assert Path(output).stat().st_size > 0
