from enum import StrEnum


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    USER_REPORTED_PENDING_EVIDENCE = "user_reported_pending_evidence"
    IN_PROGRESS = "in_progress"
    PLANNED = "planned"
    INFERRED = "inferred"
    UNSUPPORTED = "unsupported"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class JobStatus(StrEnum):
    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    SHORTLISTED = "shortlisted"
    CV_DRAFTING = "cv_drafting"
    AWAITING_REVIEW = "awaiting_review"
    READY_TO_APPLY = "ready_to_apply"
    APPLIED = "applied"
    RECRUITER_CONTACT = "recruiter_contact"
    SCREENING = "screening"
    TECHNICAL_INTERVIEW = "technical_interview"
    HIRING_MANAGER_INTERVIEW = "hiring_manager_interview"
    FINAL_INTERVIEW = "final_interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"


class SponsorshipStatus(StrEnum):
    EXPLICITLY_AVAILABLE = "explicitly_available"
    EXPLICITLY_UNAVAILABLE = "explicitly_unavailable"
    POSSIBLY_AVAILABLE = "possibly_available"
    NOT_MENTIONED = "not_mentioned"
    REQUIRES_EXISTING_WORK_AUTHORIZATION = "requires_existing_work_authorization"
    CITIZENSHIP_REQUIRED = "citizenship_required"
    SECURITY_CLEARANCE_REQUIRED = "security_clearance_required"
    NEEDS_MANUAL_RESEARCH = "needs_manual_research"
    NOT_APPLICABLE = "not_applicable"


class ApprovalStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RecommendationBand(StrEnum):
    PRIORITY = "priority"
    STRONG = "strong"
    CONDITIONAL = "conditional"
    WEAK = "weak"
    ARCHIVE = "archive"
    BLOCKED = "blocked"
