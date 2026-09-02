from app.scoring import score_lead


def test_hot_healthcare_lead():
    result = score_lead({
        "occupation": "Travel Nurse",
        "assignment_location": "Medical City Dallas",
        "stay_days": 90,
        "budget": 3500,
        "move_in": "2026-10-01",
        "reason_for_stay": "13-week assignment",
        "evidence": "Travel nurse starting a 13-week Dallas assignment",
    })
    assert result.score >= 90
    assert result.classification == "HOT"


def test_short_stay_is_not_hot():
    result = score_lead({
        "occupation": "Traveler",
        "assignment_location": "Dallas",
        "stay_days": 7,
        "budget": 2000,
        "evidence": "Looking for 7 nights",
    })
    assert result.classification in {"LOW", "UNQUALIFIED"}
