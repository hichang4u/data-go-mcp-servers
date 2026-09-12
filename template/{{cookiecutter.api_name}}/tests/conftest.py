"""공용 fixture. 실제 API 응답 샘플로 교체한다."""

import pytest


BASE = "{{ cookiecutter.api_base_url }}"


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def sample_response() -> dict:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
                "items": {"item": [{"itemId": "1", "itemNm": "예시"}]},
                "pageNo": 1,
                "numOfRows": 10,
                "totalCount": 1,
            },
        }
    }


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("{{ cookiecutter.api_name_underscore.upper() }}_API_KEY", raising=False)
