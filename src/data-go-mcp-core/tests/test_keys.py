"""load_api_key 우선순위 테스트."""

import pytest

from data_go_mcp.core.keys import load_api_key


def test_uses_common_api_key_when_no_prefixed_key(monkeypatch):
    monkeypatch.delenv("NPS_BUSINESS_ENROLLMENT_API_KEY", raising=False)
    monkeypatch.setenv("API_KEY", "common-key")

    assert load_api_key("NPS_BUSINESS_ENROLLMENT") == "common-key"


def test_prefixed_key_overrides_common_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "common-key")
    monkeypatch.setenv("NPS_BUSINESS_ENROLLMENT_API_KEY", "nps-key")

    assert load_api_key("NPS_BUSINESS_ENROLLMENT") == "nps-key"


def test_explicit_argument_beats_environment(monkeypatch):
    monkeypatch.setenv("API_KEY", "common-key")
    monkeypatch.setenv("NPS_BUSINESS_ENROLLMENT_API_KEY", "nps-key")

    assert load_api_key("NPS_BUSINESS_ENROLLMENT", explicit="arg-key") == "arg-key"


def test_raises_with_both_env_names_when_missing(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("NPS_BUSINESS_ENROLLMENT_API_KEY", raising=False)

    with pytest.raises(ValueError, match="NPS_BUSINESS_ENROLLMENT_API_KEY.*API_KEY"):
        load_api_key("NPS_BUSINESS_ENROLLMENT")


def test_blank_value_counts_as_missing(monkeypatch):
    monkeypatch.setenv("API_KEY", "   ")
    monkeypatch.delenv("NPS_BUSINESS_ENROLLMENT_API_KEY", raising=False)

    with pytest.raises(ValueError):
        load_api_key("NPS_BUSINESS_ENROLLMENT")


def test_shared_false_ignores_common_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "data-go-key")
    monkeypatch.delenv("DART_DISCLOSURE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DART_DISCLOSURE_API_KEY") as exc_info:
        load_api_key("DART_DISCLOSURE", shared=False)
    assert "or API_KEY" not in str(exc_info.value)


def test_shared_false_still_reads_prefixed_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "data-go-key")
    monkeypatch.setenv("DART_DISCLOSURE_API_KEY", "dart-key")

    assert load_api_key("DART_DISCLOSURE", shared=False) == "dart-key"


def test_shared_false_uses_custom_key_url(monkeypatch):
    monkeypatch.delenv("DART_DISCLOSURE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="opendart.fss.or.kr"):
        load_api_key("DART_DISCLOSURE", shared=False, key_url="https://opendart.fss.or.kr")
