"""루트 pytest 설정: integration 마커 (실제 API 호출) 는 API_KEY 가 있을 때만 실행."""

import os

import pytest
from dotenv import load_dotenv


load_dotenv()  # 저장소 루트 .env 의 API_KEY 를 integration 판정에 쓴다


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.getenv("API_KEY"):
        return
    skip = pytest.mark.skip(reason="API_KEY not set — integration tests need a data.go.kr key")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
