"""통합 서버 테스트 공용 fixture."""

import pytest


@pytest.fixture(autouse=True)
def _keys(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("DART_DISCLOSURE_API_KEY", "test-dart-key")
