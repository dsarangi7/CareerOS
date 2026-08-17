from sqlalchemy.orm import Session

from app.models.entities import AuditEvent


def record_audit(
    session: Session,
    *,
    action: str,
    subject_type: str,
    subject_id: str | None = None,
    details: dict[str, object] | None = None,
    actor: str = "system",
) -> AuditEvent:
    event = AuditEvent(
        actor=actor,
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        details=details or {},
    )
    session.add(event)
    return event
