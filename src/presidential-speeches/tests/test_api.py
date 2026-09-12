"""PresidentialSpeechesAPIClient 테스트 (odcloud 파일데이터 API, cond[] 서버측 필터)."""

import httpx
import pytest
import respx

from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.presidential_speeches.api_client import PresidentialSpeechesAPIClient


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY")
    with pytest.raises(ValueError, match="API_KEY"):
        PresidentialSpeechesAPIClient()


@respx.mock
async def test_get_speeches_2023_parses_rows(url_2023, page_response, rows_2023):
    route = respx.get(url_2023).mock(
        return_value=httpx.Response(200, json=page_response(rows_2023, per_page=2))
    )
    async with PresidentialSpeechesAPIClient() as client:
        resp = await client.get_speeches_2023(page=1, per_page=2)

    q = route.calls.last.request.url.params
    assert q["serviceKey"] == "test-key"
    assert q["returnType"] == "json"
    assert q["page"] == "1"
    assert q["perPage"] == "2"

    assert resp.total_count == 8565
    assert resp.data[1].president == "문재인"
    assert resp.data[1].speech_year == 2020
    assert resp.data[1].title == "2020 신년 합동 인사회"


@respx.mock
async def test_get_speeches_2022_has_dates(url_2022, page_response, rows_2022):
    respx.get(url_2022).mock(
        return_value=httpx.Response(200, json=page_response(rows_2022, total=7173))
    )
    async with PresidentialSpeechesAPIClient() as client:
        resp = await client.get_speeches_2022()
    assert resp.data[0].speech_date == "1948-07-24"


@respx.mock
async def test_search_sends_server_side_cond_filters(url_2023, page_response):
    route = respx.get(url_2023).mock(
        return_value=httpx.Response(200, json=page_response([], match=0))
    )
    async with PresidentialSpeechesAPIClient() as client:
        await client.search_speeches(president="노무현", title="통일", year=2005, location="국내")

    q = route.calls.last.request.url.params
    assert q["cond[대통령::EQ]"] == "노무현"
    assert q["cond[글제목::LIKE]"] == "통일"
    assert q["cond[연설연도::EQ]"] == "2005"
    assert q["cond[연설장소::LIKE]"] == "국내"


@respx.mock
async def test_search_omits_unused_filters(url_2023, page_response):
    route = respx.get(url_2023).mock(
        return_value=httpx.Response(200, json=page_response([], match=0))
    )
    async with PresidentialSpeechesAPIClient() as client:
        await client.search_speeches(title="통일")

    q = route.calls.last.request.url.params
    assert "cond[대통령::EQ]" not in q
    assert q["cond[글제목::LIKE]"] == "통일"


@respx.mock
async def test_match_count_reflects_filter(url_2023, page_response, rows_2023):
    respx.get(url_2023).mock(
        return_value=httpx.Response(200, json=page_response(rows_2023[:1], match=41))
    )
    async with PresidentialSpeechesAPIClient() as client:
        resp = await client.search_speeches(president="이승만")
    assert resp.match_count == 41
    assert resp.total_count == 8565


@respx.mock
async def test_auth_error_raises_data_go_error(url_2023):
    respx.get(url_2023).mock(
        return_value=httpx.Response(
            401, json={"code": -401, "msg": "유효하지 않은 인증키 입니다."}
        )
    )
    async with PresidentialSpeechesAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get_speeches_2023()
    assert exc.value.result_code == "-401"
