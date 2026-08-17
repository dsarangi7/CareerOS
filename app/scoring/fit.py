from typing import TypedDict

from app.core.enums import RecommendationBand, SponsorshipStatus

DEFAULT_WEIGHTS = {
    "technical_skills": 25,
    "relevant_achievements": 20,
    "industry_domain_relevance": 15,
    "seniority_alignment": 10,
    "visa_location_feasibility": 15,
    "compensation_alignment": 10,
    "strategic_career_value": 5,
}

HARD_BLOCKING_SPONSORSHIP = {
    SponsorshipStatus.EXPLICITLY_UNAVAILABLE,
    SponsorshipStatus.CITIZENSHIP_REQUIRED,
    SponsorshipStatus.SECURITY_CLEARANCE_REQUIRED,
    SponsorshipStatus.REQUIRES_EXISTING_WORK_AUTHORIZATION,
}


def recommendation_for_score(score: float) -> RecommendationBand:
    if score >= 85:
        return RecommendationBand.PRIORITY
    if score >= 75:
        return RecommendationBand.STRONG
    if score >= 65:
        return RecommendationBand.CONDITIONAL
    if score >= 50:
        return RecommendationBand.WEAK
    return RecommendationBand.ARCHIVE


class FitScoreExplanation(TypedDict):
    hard_disqualifiers: list[str]
    strong_matches: list[str]
    partial_matches: list[str]
    missing_requirements: int
    risks: list[str]


class FitScoreResult(TypedDict):
    total_score: float
    recommendation: str
    category_scores: dict[str, float]
    explanation: FitScoreExplanation
    confidence: float


def calculate_fit_score(
    *,
    matched_skills: int,
    required_skills: int,
    matched_achievements: int,
    relevant_domain: bool,
    seniority_aligned: bool,
    sponsorship_status: SponsorshipStatus,
    compensation_aligned: bool,
    strategic_value: bool,
    weights: dict[str, int] | None = None,
) -> FitScoreResult:
    active_weights = weights or DEFAULT_WEIGHTS
    technical_ratio = matched_skills / max(required_skills, 1)
    category_scores = {
        "technical_skills": min(1.0, technical_ratio) * active_weights["technical_skills"],
        "relevant_achievements": min(1.0, matched_achievements / 3)
        * active_weights["relevant_achievements"],
        "industry_domain_relevance": active_weights["industry_domain_relevance"]
        if relevant_domain
        else 5,
        "seniority_alignment": active_weights["seniority_alignment"] if seniority_aligned else 3,
        "visa_location_feasibility": active_weights["visa_location_feasibility"],
        "compensation_alignment": active_weights["compensation_alignment"]
        if compensation_aligned
        else 4,
        "strategic_career_value": active_weights["strategic_career_value"]
        if strategic_value
        else 2,
    }

    hard_disqualifiers: list[str] = []
    if sponsorship_status in HARD_BLOCKING_SPONSORSHIP:
        hard_disqualifiers.append(f"Work authorization restriction: {sponsorship_status.value}")
        category_scores["visa_location_feasibility"] = 0

    total = round(sum(category_scores.values()), 2)
    recommendation = (
        RecommendationBand.BLOCKED if hard_disqualifiers else recommendation_for_score(total)
    )
    return {
        "total_score": total,
        "recommendation": recommendation.value,
        "category_scores": {key: round(value, 2) for key, value in category_scores.items()},
        "explanation": {
            "hard_disqualifiers": hard_disqualifiers,
            "strong_matches": ["technical overlap"] if technical_ratio >= 0.75 else [],
            "partial_matches": ["some transferable evidence"] if matched_achievements else [],
            "missing_requirements": max(required_skills - matched_skills, 0),
            "risks": hard_disqualifiers,
        },
        "confidence": 0.82,
    }
