from __future__ import annotations

import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "openai_api_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "env_secret": re.compile(
        r"(?i)\b(api[_-]?key|password|secret|token)\s*=\s*['\"]?[^'\"\s#{}]{8,}"
    ),
}
ALLOWED_UPLOAD_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".txt", ".pdf", ".docx"}
SKIPPED_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", ".venv"}
SKIPPED_SUFFIXES = {".db", ".sqlite", ".xlsx", ".pdf", ".pyc", ".png", ".jpg", ".jpeg"}


def scan_text_for_secrets(text: str) -> list[str]:
    findings: list[str] = []
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            findings.append(name)
    return findings


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS.values():
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def scan_repo_for_secrets(root: Path) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for path in root.rglob("*"):
        if path.is_dir() or any(part in SKIPPED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIPPED_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        matches = scan_text_for_secrets(text)
        if matches:
            findings[str(path.relative_to(root))] = matches
    return findings


def validate_upload(
    path: Path,
    *,
    max_mb: int = 10,
    allowed_suffixes: set[str] | None = None,
) -> None:
    suffixes = allowed_suffixes or ALLOWED_UPLOAD_SUFFIXES
    if not path.exists() or not path.is_file():
        raise ValueError("Upload does not exist")
    if path.suffix.lower() not in suffixes:
        raise ValueError(f"Unsupported upload type: {path.suffix}")
    if path.stat().st_size > max_mb * 1024 * 1024:
        raise ValueError(f"Upload exceeds {max_mb} MB limit")


def create_sqlite_backup(db_path: Path, output_dir: Path) -> Path:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = output_dir / f"{db_path.stem}_{stamp}{db_path.suffix}"
    shutil.copy2(db_path, output)
    return output
