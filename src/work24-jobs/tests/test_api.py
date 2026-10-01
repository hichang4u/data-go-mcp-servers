"""고용24 클라이언트 테스트 — 조용히 무시되는 파라미터와 두 가지 오류 래핑이 핵심."""

import httpx
import pytest
import respx

from data_go_mcp.core import DataGoAPIError
from data_go_mcp.work24_jobs.api_client import Work24JobsAPIClient

from .conftest import DETAIL_ERROR_XML, SERVICE_ERROR_XML


def _xml(body: str) -> httpx.Response:
    return httpx.Response(200, text=body, headers={"content-type": "application/xml"})


def test_client_requires_its_own_key(monkeypatch):
    """고용24는 data.go.kr 이 아니다 — 공통 API_KEY 로 대체되면 안 된다."""
    monkeypatch.delenv("WORK24_API_KEY", raising=False)
    monkeypatch.setenv("API_KEY", "data-go-kr-key")
    with pytest.raises(ValueError) as exc:
        Work24JobsAPIClient()
    assert "WORK24_API_KEY" in str(exc.value)
    assert "work24.go.kr" in str(exc.value)


@respx.mock
async def test_search_by_business_number(base_url, list_xml):
    route = respx.get(f"{base_url}/callOpenApiSvcInfo210L01.do").mock(return_value=_xml(list_xml))
    async with Work24JobsAPIClient() as client:
        result = await client.search_jobs(business_number="503-81-69211")

    q = route.calls.last.request.url.params
    assert q["busino"] == "5038169211"  # 하이픈을 떼고 보낸다
    assert q["callTp"] == "L" and q["returnType"] == "XML"

    first = result["items"][0]
    assert first["company"] == "워터매니지먼트주식회사"
    assert first["business_number"] == "5038169211"
    assert first["title"] == "[운영팀] 환경·안전 및 운영관리 담당자 채용"
    assert first["min_salary"] == 41000000
    assert first["region"] == "대구 서구"
    assert first["posted_date"] == "2026-10-01"  # 26-10-01 → 네 자리 연도
    assert result["total_count"] == 2


@respx.mock
async def test_region_code_is_truncated_to_five_digits(base_url, list_xml):
    """지역코드가 법정동코드와 호환이라 find_region_code 의 10자리를 그대로 받는다."""
    route = respx.get(url__startswith=base_url).mock(return_value=_xml(list_xml))
    async with Work24JobsAPIClient() as client:
        await client.search_jobs(region_code="1168000000")
    assert route.calls.last.request.url.params["region"] == "11680"


@pytest.mark.parametrize("region", ["1168", "서울", "11", "116800000000"])
async def test_bad_region_code_is_rejected(region):
    """이름이나 자리수가 틀리면 API 는 전국을 주거나 빈 결과를 준다 — 먼저 막는다."""
    async with Work24JobsAPIClient() as client:
        with pytest.raises(ValueError, match="지역코드"):
            await client.search_jobs(region_code=region)


@respx.mock
async def test_sido_level_code_works_here(base_url, list_xml):
    """molit 과 달리 고용24 는 시도 코드가 동작한다 (11000 → 서울 전체)."""
    route = respx.get(url__startswith=base_url).mock(return_value=_xml(list_xml))
    async with Work24JobsAPIClient() as client:
        await client.search_jobs(region_code="1100000000")
    assert route.calls.last.request.url.params["region"] == "11000"


async def test_bad_business_number_is_rejected():
    async with Work24JobsAPIClient() as client:
        with pytest.raises(ValueError, match="사업자"):
            await client.search_jobs(business_number="50381")


@respx.mock
async def test_display_is_capped_at_hundred(base_url, list_xml):
    """display 100 을 넘기면 API 가 조용히 100 으로 깎는다 — 먼저 맞춘다."""
    route = respx.get(url__startswith=base_url).mock(return_value=_xml(list_xml))
    async with Work24JobsAPIClient() as client:
        await client.search_jobs(business_number="5038169211", num_of_rows=1000)
    assert route.calls.last.request.url.params["display"] == "100"


@respx.mock
async def test_empty_result_is_not_an_error(base_url, empty_xml):
    """결과 없음은 messageCd 006 으로 온다 — 오류가 아니다."""
    respx.get(url__startswith=base_url).mock(return_value=_xml(empty_xml))
    async with Work24JobsAPIClient() as client:
        result = await client.search_jobs(business_number="0000000000")
    assert result["items"] == [] and result["total_count"] == 0


@respx.mock
async def test_service_not_applied_raises(base_url):
    """키가 그 서비스에 신청되지 않으면 GO24 래퍼로 온다 (wantedRoot 가 아니다)."""
    respx.get(url__startswith=base_url).mock(return_value=_xml(SERVICE_ERROR_XML))
    async with Work24JobsAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.search_jobs(business_number="5038169211")
    assert exc.value.source == "고용24"
    assert "신청" in exc.value.result_msg


@respx.mock
async def test_other_message_codes_raise(base_url):
    respx.get(url__startswith=base_url).mock(return_value=_xml(DETAIL_ERROR_XML))
    async with Work24JobsAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get_job("K140022610010052")
    assert exc.value.result_code == "018"


@respx.mock
async def test_detail_sends_the_required_info_service(base_url, detail_xml):
    """infoSvc 가 없으면 018 로 거절된다 (문서에 없던 필수 파라미터)."""
    route = respx.get(f"{base_url}/callOpenApiSvcInfo210D01.do").mock(
        return_value=_xml(detail_xml)
    )
    async with Work24JobsAPIClient() as client:
        result = await client.get_job("K140022610010052")

    q = route.calls.last.request.url.params
    assert q["wantedAuthNo"] == "K140022610010052"
    assert q["infoSvc"] == "VALIDATION"
    assert q["callTp"] == "D"

    assert result["company"]["name"] == "워터매니지먼트주식회사"
    assert result["company"]["ceo_name"] == "김남진"
    assert result["company"]["employee_count"] == "25 명"
    assert result["company"]["annual_sales"] == "5745 백만원"
    assert result["posting"]["title"] == "[운영팀] 환경·안전 및 운영관리 담당자 채용"
    assert result["posting"]["certificate"] == "수질환경산업기사,대기환경산업기사"


async def test_search_requires_at_least_one_filter():
    """조건 없이 부르면 전국 5만 건이 온다 — 사고를 막는다."""
    async with Work24JobsAPIClient() as client:
        with pytest.raises(ValueError, match="조건"):
            await client.search_jobs()
