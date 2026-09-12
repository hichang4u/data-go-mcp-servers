"""presidential 테스트 공용 fixture — 2026-09-12 odcloud 실제 응답 형태."""

import pytest


BASE = "https://api.odcloud.kr/api/15084167/v1"
UDDI_2023 = "uddi:f30c6ace-297a-4a9e-9229-844153ed21ba"
UDDI_2022 = "uddi:1c8b5454-bd4e-45db-98f7-fe94d71f271b"

ROW_2023_A = {
    "구분번호": 1310440,
    "글제목": "대통령 취임사(大統領就任辭)",
    "대통령": "이승만",
    "연설연도": 1948,
    "연설장소": "국내",
    "원문보기": "https://dams.pa.go.kr/dams/DOCUMENT/a.PDF",
}
ROW_2023_B = {
    "구분번호": 1401097,
    "글제목": "2020 신년 합동 인사회",
    "대통령": "문재인",
    "연설연도": 2020,
    "연설장소": "국내",
    "원문보기": "https://dams.pa.go.kr/dams/PUBLICATION/b.pdf",
}
ROW_2022_A = {
    "구분번호": 1310440,
    "글제목": "대통령 취임사(大統領就任辭)",
    "대통령": "이승만",
    "연설일자": "1948-07-24",
    "연설장소": "국내",
    "원문보기": "http://dams.pa.go.kr:8888/dams/DOCUMENT/a.PDF",
}


def page(
    rows: list, *, page: int = 1, per_page: int = 10, total: int = 8565, match: int | None = None
) -> dict:
    return {
        "currentCount": len(rows),
        "data": rows,
        "matchCount": total if match is None else match,
        "page": page,
        "perPage": per_page,
        "totalCount": total,
    }


@pytest.fixture
def url_2023() -> str:
    return f"{BASE}/{UDDI_2023}"


@pytest.fixture
def url_2022() -> str:
    return f"{BASE}/{UDDI_2022}"


@pytest.fixture
def page_response():
    return page


@pytest.fixture
def rows_2023() -> list:
    return [dict(ROW_2023_A), dict(ROW_2023_B)]


@pytest.fixture
def rows_2022() -> list:
    return [dict(ROW_2022_A)]


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("PRESIDENTIAL_SPEECHES_API_KEY", raising=False)
