from types import SimpleNamespace

import pytest

from app.ai import _parse_discovery_output


def test_valid_discovery_json():
    response = SimpleNamespace(status="completed", output_text='{"candidates": []}')
    assert _parse_discovery_output(response) == {"candidates": []}


def test_truncated_discovery_json_raises_value_error():
    response = SimpleNamespace(status="completed", output_text='{"candidates": [')
    with pytest.raises(ValueError):
        _parse_discovery_output(response)


def test_noncompleted_response_raises_value_error():
    response = SimpleNamespace(status="incomplete", output_text='{"candidates": []}')
    with pytest.raises(ValueError):
        _parse_discovery_output(response)
