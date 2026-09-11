from dataclasses import dataclass


@dataclass
class ScoreResult:
    score: int
    classification: str
    reasons: list[str]


def score_lead(data: dict) -> ScoreResult:
    score = 0
    reasons = []

    lead_type = str(data.get("lead_type", "")).upper()
    lead_type_points = {
        "DIRECT_HOUSING_LEAD": 25,
        "ORGANIZATION_LEAD": 18,
        "ASSIGNMENT_SIGNAL": 8,
        "REJECT": -100,
    }
    if lead_type in lead_type_points:
        score += lead_type_points[lead_type]
        reasons.append(f"Lead type: {lead_type}")

    if lead_type == "REJECT":
        return ScoreResult(0, "UNQUALIFIED", reasons)

    stay = data.get("stay_days")
    if isinstance(stay, int):
        if stay >= 90:
            score += 25
            reasons.append("Strong 90+ day stay fit")
        elif stay >= 30:
            score += 20
            reasons.append("Meets 30+ day minimum")
        else:
            reasons.append("Below 30-day minimum")
    else:
        text = str(data.get("evidence", "")).lower()
        if any(
            x in text
            for x in [
                "13 week",
                "13-week",
                "90 day",
                "90-day",
                "30 day",
                "30-day",
                "60 day",
                "60-day",
                "8 week",
                "8-week",
                "3 month",
                "3-month",
            ]
        ):
            score += 20
            reasons.append("Evidence suggests a mid-term stay")

    occupation = str(data.get("occupation", "")).lower()
    target_terms = [
        "nurse",
        "physician",
        "medical",
        "healthcare",
        "therapist",
        "consultant",
        "project manager",
        "engineer",
        "contractor",
        "relocation",
        "it ",
        "software",
        "banking",
    ]
    if any(term in occupation for term in target_terms):
        score += 10
        reasons.append("Target professional audience")

    location = str(data.get("assignment_location", "")).lower()
    evidence = str(data.get("evidence", "")).lower()
    combined = f"{location} {evidence}"
    dallas_terms = [
        "dallas",
        "north dallas",
        "northeast dallas",
        "dfw",
        "medical city dallas",
        "texas health presbyterian hospital dallas",
    ]
    if any(term in combined for term in dallas_terms):
        score += 20
        reasons.append("Dallas-area housing signal")

    # Keep current rent-fit thresholds unchanged in V2 discovery optimization.
    budget = data.get("budget")
    if isinstance(budget, (int, float)):
        if budget >= 3200:
            score += 20
            reasons.append("Budget appears compatible")
        elif budget >= 2800:
            score += 10
            reasons.append("Budget may be workable")
    else:
        score += 5
        reasons.append("Budget not stated; candidate retained")

    if data.get("move_in"):
        score += 10
        reasons.append("Move-in timing identified")

    if data.get("reason_for_stay"):
        score += 5

    confidence = data.get("confidence")
    if isinstance(confidence, (int, float)) and confidence >= 0.8:
        score += 5
        reasons.append("High evidence confidence")

    score = max(0, min(score, 100))
    classification = (
        "HOT"
        if score >= 90
        else "HIGH"
        if score >= 80
        else "WARM"
        if score >= 65
        else "LOW"
        if score >= 50
        else "UNQUALIFIED"
    )
    return ScoreResult(score, classification, reasons)
