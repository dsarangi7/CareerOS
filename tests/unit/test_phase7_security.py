from pathlib import Path

import pytest

from app.security.hardening import (
    create_sqlite_backup,
    redact_secrets,
    scan_repo_for_secrets,
    scan_text_for_secrets,
    validate_upload,
)


def test_secret_scan_detects_and_redacts_common_tokens() -> None:
    api_key = "sk-" + "testkey" + ("0" * 24)
    pass_fragment = "password=" + "correct" + "horse" + "battery"
    text = f"OPENAI_API_KEY={api_key} {pass_fragment}"

    findings = scan_text_for_secrets(text)
    redacted = redact_secrets(text)

    assert "openai_api_key" in findings
    assert "env_secret" in findings
    assert "sk-testkey" not in redacted
    assert "[REDACTED]" in redacted


def test_repo_secret_scan_skips_cache_and_reports_text_files(tmp_path: Path) -> None:
    token = "token=" + "abcdefghijklmnop"
    (tmp_path / "notes.txt").write_text(token, encoding="utf-8")
    cache = tmp_path / ".git"
    cache.mkdir()
    ignored = "password=" + "ignoredsecret"
    (cache / "config").write_text(ignored, encoding="utf-8")

    findings = scan_repo_for_secrets(tmp_path)

    assert findings == {"notes.txt": ["env_secret"]}


def test_upload_validation_and_sqlite_backup(tmp_path: Path) -> None:
    upload = tmp_path / "jobs.csv"
    upload.write_text("title,company\nEngineer,Example", encoding="utf-8")
    validate_upload(upload)

    with pytest.raises(ValueError):
        validate_upload(tmp_path / "jobs.exe")

    db = tmp_path / "career_os.db"
    db.write_bytes(b"sqlite bytes")
    backup = create_sqlite_backup(db, tmp_path / "backups")

    assert backup.exists()
    assert backup.read_bytes() == b"sqlite bytes"
