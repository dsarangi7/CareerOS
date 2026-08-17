from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_windows_launcher_scripts_are_safe_and_local_only() -> None:
    start_script = (ROOT / "start-careeros.ps1").read_text(encoding="utf-8")
    stop_script = (ROOT / "stop-careeros.ps1").read_text(encoding="utf-8")

    assert '--host", "127.0.0.1"' in start_script
    assert '--server.address", "127.0.0.1"' in start_script
    assert "private_data\\runtime" in start_script
    assert "careeros-processes.json" in start_script
    assert "Stop-Process -Id $process.Id" in start_script
    assert "Stop-Process -Id $pid" in stop_script
    assert "Get-Process |" not in stop_script
    assert "taskkill" not in start_script.lower()
    assert "taskkill" not in stop_script.lower()
