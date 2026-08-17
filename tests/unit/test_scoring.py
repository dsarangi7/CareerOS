from app.core.enums import RecommendationBand, SponsorshipStatus
from app.scoring.fit import calculate_fit_score, recommendation_for_score


def test_recommendation_bands() -> None:
    assert recommendation_for_score(90) == RecommendationBand.PRIORITY
    assert recommendation_for_score(80) == RecommendationBand.STRONG
    assert recommendation_for_score(70) == RecommendationBand.CONDITIONAL
    assert recommendation_for_score(55) == RecommendationBand.WEAK
    assert recommendation_for_score(20) == RecommendationBand.ARCHIVE


def test_hard_authorization_restriction_blocks_recommendation() -> None:
    result = calculate_fit_score(
        matched_skills=6,
        required_skills=6,
        matched_achievements=3,
        relevant_domain=True,
        seniority_aligned=True,
        sponsorship_status=SponsorshipStatus.CITIZENSHIP_REQUIRED,
        compensation_aligned=True,
        strategic_value=True,
    )

    assert result["recommendation"] == RecommendationBand.BLOCKED.value
    assert result["category_scores"]["visa_location_feasibility"] == 0
    assert result["explanation"]["hard_disqualifiers"]
