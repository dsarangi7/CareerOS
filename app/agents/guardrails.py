from typing import Any

DANGEROUS_INSTRUCTION_MARKERS = [
    "ignore previous instructions",
    "ignore all instructions",
    "developer message",
    "system prompt",
    "reveal secrets",
    "submit the application",
    "send this email",
    "click apply",
    "publish this cv",
    "exfiltrate",
]

EXTERNAL_WRITE_ACTIONS = {
    "submit_application",
    "send_email",
    "send_linkedin_message",
    "update_external_crm",
    "complete_external_form",
    "publish_cv",
    "share_personal_data",
    "withdraw_application",
    "accept_offer",
    "reject_offer",
}


def sanitize_untrusted_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    sanitized: dict[str, Any] = {}
    warnings: list[str] = []
    for key, value in payload.items():
        if isinstance(value, str):
            cleaned, field_warnings = sanitize_untrusted_text(value)
            sanitized[key] = cleaned
            warnings.extend([f"{key}: {warning}" for warning in field_warnings])
        else:
            sanitized[key] = value
    return sanitized, warnings


def sanitize_untrusted_text(text: str) -> tuple[str, list[str]]:
    lowered = text.lower()
    warnings = [marker for marker in DANGEROUS_INSTRUCTION_MARKERS if marker in lowered]
    if not warnings:
        return text, []
    return (
        "[UNTRUSTED SOURCE TEXT - INSTRUCTIONS NEUTRALIZED]\n"
        + text.replace("ignore", "i_gnore").replace("Ignore", "I_gnore"),
        warnings,
    )


def requested_external_actions(output_actions: list[str]) -> list[str]:
    return sorted(EXTERNAL_WRITE_ACTIONS.intersection(output_actions))
