from dataclasses import dataclass
import re


@dataclass
class ScoreResult:
    score: int
    classification: str
    reasons: list[str]


def score_lead(data: dict) -> ScoreResult:
    score = 0
    reasons = []

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
        if any(x in text for x in ["13 week", "90 day", "30 day", "60 day", "90-day"]):
            score += 20
            reasons.append("Evidence suggests a mid-term stay")

    occupation = str(data.get("occupation", "")).lower()
    target_terms = [
        "nurse", "physician", "medical", "healthcare", "consultant",
        "project manager", "engineer", "contractor", "relocation",
        "it ", "software", "banking",
    ]
    if any(term in occupation for term in target_terms):
        score += 10
        reasons.append("Target professional audience")

    location = str(data.get("assignment_location", "")).lower()
    evidence = str(data.get("evidence", "")).lower()
    combined = f"{location} {evidence}"
    if "dallas" in combined:
        score += 20
        reasons.append("Dallas housing signal")

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

    if data.get("move_in"):
        score += 10
        reasons.append("Move-in timing identified")

    if data.get("reason_for_stay"):
        score += 5

    score = min(score, 100)
    classification = (
        "HOT" if score >= 90 else
        "HIGH" if score >= 80 else
        "WARM" if score >= 65 else
        "LOW" if score >= 50 else
        "UNQUALIFIED"
    )
    return ScoreResult(score, classification, reasons)
