from app.ai import _resolve_source_url


def test_evidence_url_is_preferred_over_related_model_url():
    evidence_url = "https://www.vivian.com/job/1118-15311260/"
    related_url = "https://staydeco.com/relocation-housing/"
    evidence = (
        "Verified Dallas assignment. "
        f"([vivian.com]({evidence_url}))"
    )

    selected = _resolve_source_url(
        evidence=evidence,
        model_source_url=related_url,
        web_source_urls=[related_url, evidence_url],
    )

    assert selected == evidence_url


def test_ungrounded_model_url_is_not_saved():
    selected = _resolve_source_url(
        evidence="Supported assignment with no embedded link.",
        model_source_url="https://example.com/not-returned",
        web_source_urls=["https://example.com/actual-source"],
    )

    assert selected is None
