"""InsuranceStatusAPIClient(고용·산재보험 가입 사업장) 테스트. XML 실응답을 respx 로."""

import httpx
import pytest
import respx

from data_go_mcp.nps_business_enrollment.api_client import InsuranceStatusAPIClient


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")


@respx.mock
async def test_get_workplaces_parses_both_insurance_kinds(insurance_base_url, insurance_xml):
    route = respx.get(f"{insurance_base_url}/getGySjBoheomBsshItem").mock(
        return_value=httpx.Response(200, text=insurance_xml)
    )
    async with InsuranceStatusAPIClient() as client:
        result = await client.get_workplaces("120-88-00767", num_of_rows=5)

    params = route.calls.last.request.url.params
    assert params["v_saeopjaDrno"] == "1208800767"
    assert "opaBoheomFg" not in params
    assert params["numOfRows"] == "5"

    assert result["total_count"] == 3
    assert result["page_no"] == 1
    sanjae, goyong, sanjae2 = result["items"]
    assert sanjae["insurance"] == "산재"
    assert sanjae["workplace_nm"] == "주식회사포워드벤처스/캐슬캠프"
    assert sanjae["employee_cnt"] == 0
    assert sanjae["industry_cd"] == "50109"
    assert sanjae["industry_nm"] == "소형화물운수업"
    assert goyong["insurance"] == "고용"
    assert goyong["employee_cnt"] == 11070
    assert goyong["industry_cd"] == "47919"
    assert goyong["industry_nm"] == "기타 통신 판매업"
    assert goyong["established_dt"] == "20131001"
    assert goyong["addr"] == "서울특별시 광진구 아차산로 412 2층"
    assert sanjae2["industry_nm"] == "도.소매 및 소비자용품수리업"  # 뒤 공백 제거


@respx.mock
async def test_get_workplaces_single_item_and_filter(insurance_base_url, insurance_single_xml):
    route = respx.get(f"{insurance_base_url}/getGySjBoheomBsshItem").mock(
        return_value=httpx.Response(200, text=insurance_single_xml)
    )
    async with InsuranceStatusAPIClient() as client:
        result = await client.get_workplaces("1248100998", insurance="고용")

    assert route.calls.last.request.url.params["opaBoheomFg"] == "2"
    assert len(result["items"]) == 1
    assert result["items"][0]["employee_cnt"] == 128093


@respx.mock
async def test_get_workplaces_empty(insurance_base_url, insurance_empty_xml):
    respx.get(f"{insurance_base_url}/getGySjBoheomBsshItem").mock(
        return_value=httpx.Response(200, text=insurance_empty_xml)
    )
    async with InsuranceStatusAPIClient() as client:
        result = await client.get_workplaces("9999999999")

    assert result["items"] == []
    assert result["total_count"] == 0


@pytest.mark.parametrize("bzno", ["12345", "120-88-0076A"])
async def test_get_workplaces_rejects_bad_bzno(bzno):
    async with InsuranceStatusAPIClient() as client:
        with pytest.raises(ValueError, match="사업자등록번호"):
            await client.get_workplaces(bzno)


async def test_get_workplaces_rejects_unknown_insurance():
    async with InsuranceStatusAPIClient() as client:
        with pytest.raises(ValueError, match="산재"):
            await client.get_workplaces("1208800767", insurance="건강")


def test_insured_workplace_empty_kind_element_does_not_become_the_string_none():
    from data_go_mcp.nps_business_enrollment.models import InsuredWorkplace

    item = InsuredWorkplace.from_api(
        {"opaBoheomFg": None, "saeopjangNm": "x", "saeopjaDrno": "1208800767"}
    )
    assert item.insurance == "미상"
