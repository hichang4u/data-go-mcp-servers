"""API 클라이언트 테스트 — respx 로 HTTP 를 막고 응답 파싱·파라미터 전달·오류를 확인한다."""

from datetime import date

import httpx
import pytest
import respx

from data_go_mcp.core import DataGoAPIError
from data_go_mcp.dart_disclosure.api_client import DartDisclosureAPIClient, default_bgn_de


@pytest.fixture
def client():
    return DartDisclosureAPIClient()


# -- 키 ---------------------------------------------------------------------


def test_uses_dart_key_not_common_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "data-go-key")
    monkeypatch.delenv("DART_DISCLOSURE_API_KEY")
    with pytest.raises(ValueError, match="DART_DISCLOSURE_API_KEY") as exc_info:
        DartDisclosureAPIClient()
    assert "opendart.fss.or.kr" in str(exc_info.value)


@respx.mock
async def test_key_is_sent_as_crtfc_key(client, base_url, company_response):
    route = respx.get(f"{base_url}/company.json").mock(
        return_value=httpx.Response(200, json=company_response)
    )
    async with client:
        await client.get_company("00126380")
    params = route.calls.last.request.url.params
    assert params["crtfc_key"] == "dart-test-key"
    assert "serviceKey" not in params
    assert params["corp_code"] == "00126380"


# -- 회사 개황 --------------------------------------------------------------


@respx.mock
async def test_get_company_parses_fields(client, base_url, company_response):
    respx.get(f"{base_url}/company.json").mock(
        return_value=httpx.Response(200, json=company_response)
    )
    async with client:
        company = await client.get_company("00126380")
    assert company is not None
    assert company["corp_name"] == "삼성전자(주)"
    assert company["stock_code"] == "005930"
    assert company["corp_cls"] == "Y"
    assert company["corp_cls_name"] == "유가증권시장"
    assert company["jurir_no"] == "1301110006246"
    assert company["bizr_no"] == "1248100998"
    assert company["est_dt"] == "19690113"
    assert "status" not in company and "message" not in company


@respx.mock
async def test_get_company_returns_none_when_no_data(client, base_url, no_data_response):
    respx.get(f"{base_url}/company.json").mock(
        return_value=httpx.Response(200, json=no_data_response)
    )
    async with client:
        assert await client.get_company("99999999") is None


async def test_get_company_validates_corp_code(client):
    with pytest.raises(ValueError, match="corp_code"):
        await client.get_company("5930")


# -- 공시 목록 --------------------------------------------------------------


@respx.mock
async def test_list_disclosures_passes_params_and_parses(
    client, base_url, disclosure_list_response
):
    route = respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=disclosure_list_response)
    )
    async with client:
        result = await client.list_disclosures(
            corp_code="00126380", bgn_de="20250101", end_de="20250331", pblntf_ty="A", page_count=5
        )
    params = route.calls.last.request.url.params
    assert params["corp_code"] == "00126380"
    assert params["bgn_de"] == "20250101"
    assert params["end_de"] == "20250331"
    assert params["pblntf_ty"] == "A"
    assert params["page_count"] == "5"
    assert params["page_no"] == "1"

    assert result["total_count"] == 49
    assert result["total_page"] == 10
    assert result["page_no"] == 1
    assert len(result["items"]) == 2
    first = result["items"][0]
    assert first["rcept_no"] == "20250325800172"
    assert first["report_nm"] == "대표이사(대표집행임원)변경(안내공시)"  # 꼬리 공백 제거
    assert first["rcept_dt"] == "20250325"
    assert first["corp_cls"] == "Y"
    assert first["rm"] == "유"


@respx.mock
async def test_list_disclosures_no_data_is_empty(client, base_url, no_data_response):
    respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=no_data_response)
    )
    async with client:
        result = await client.list_disclosures(
            corp_code="00126380", bgn_de="20250101", end_de="20250102"
        )
    assert result["items"] == []
    assert result["total_count"] == 0


@respx.mock
async def test_list_disclosures_omits_none_params(client, base_url, disclosure_list_response):
    route = respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=disclosure_list_response)
    )
    async with client:
        await client.list_disclosures(bgn_de="20250901")
    params = route.calls.last.request.url.params
    assert "corp_code" not in params and "end_de" not in params and "pblntf_ty" not in params


def test_default_bgn_de_is_one_year_with_corp_code_and_one_month_without():
    today = date(2026, 9, 17)
    assert default_bgn_de(has_corp_code=True, today=today) == "20250917"
    assert default_bgn_de(has_corp_code=False, today=today) == "20260818"


@respx.mock
async def test_list_disclosures_fills_bgn_de_when_omitted(
    client, base_url, disclosure_list_response
):
    # API 는 bgn_de 가 없으면 당일만 검색하므로 기본 시작일을 채워 보낸다.
    route = respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=disclosure_list_response)
    )
    async with client:
        await client.list_disclosures(corp_code="00126380")
        await client.list_disclosures()
    with_corp, without_corp = (c.request.url.params["bgn_de"] for c in route.calls)
    assert with_corp == default_bgn_de(has_corp_code=True)
    assert without_corp == default_bgn_de(has_corp_code=False)
    assert with_corp < without_corp


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"bgn_de": "2025-01-01"}, "bgn_de"),
        ({"bgn_de": "20250101", "end_de": "202501"}, "end_de"),
        ({"bgn_de": "20250101", "page_count": 101}, "page_count"),
        ({"bgn_de": "20250101", "page_no": 0}, "page_no"),
        ({"bgn_de": "20250101", "pblntf_ty": "Z"}, "pblntf_ty"),
    ],
)
async def test_list_disclosures_validates_input(client, kwargs, match):
    with pytest.raises(ValueError, match=match):
        await client.list_disclosures(**kwargs)


@respx.mock
async def test_api_error_status_raises_with_opendart_source(
    client, base_url, period_too_long_response
):
    respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=period_too_long_response)
    )
    async with client:
        with pytest.raises(DataGoAPIError) as exc_info:
            await client.list_disclosures(bgn_de="20240101", end_de="20250101")
    err = exc_info.value
    assert err.result_code == "100"
    assert err.source == "OpenDART"
    assert "3개월" in str(err)


@respx.mock
async def test_bad_key_raises(client, base_url, bad_key_response):
    respx.get(f"{base_url}/company.json").mock(
        return_value=httpx.Response(200, json=bad_key_response)
    )
    async with client:
        with pytest.raises(DataGoAPIError, match=r"\[010\]"):
            await client.get_company("00126380")


# -- 재무제표 ---------------------------------------------------------------


@respx.mock
async def test_get_key_accounts_parses_amounts(client, base_url, key_accounts_response):
    route = respx.get(f"{base_url}/fnlttSinglAcnt.json").mock(
        return_value=httpx.Response(200, json=key_accounts_response)
    )
    async with client:
        result = await client.get_key_accounts("00126380", "2024")
    params = route.calls.last.request.url.params
    assert params["bsns_year"] == "2024"
    assert params["reprt_code"] == "11011"  # 기본: 사업보고서

    items = result["items"]
    assert len(items) == 3
    assets = items[0]
    assert assets["fs_div"] == "CFS" and assets["sj_div"] == "BS"
    assert assets["account_nm"] == "자산총계"
    assert assets["thstrm_amount"] == 514_531_948_000_000  # "514,531,948,000,000"
    assert assets["frmtrm_amount"] == 455_905_980_000_000
    assert assets["bfefrmtrm_amount"] == 448_424_507_000_000
    assert assets["thstrm_dt"] == "2024.12.31 현재"
    assert assets["currency"] == "KRW"


@respx.mock
async def test_get_key_accounts_filters_by_fs_div(client, base_url, key_accounts_response):
    respx.get(f"{base_url}/fnlttSinglAcnt.json").mock(
        return_value=httpx.Response(200, json=key_accounts_response)
    )
    async with client:
        result = await client.get_key_accounts("00126380", "2024", fs_div="OFS")
    assert [i["fs_div"] for i in result["items"]] == ["OFS"]


@respx.mock
async def test_get_financial_statements_passes_fs_div_and_parses(
    client, base_url, fs_all_response
):
    route = respx.get(f"{base_url}/fnlttSinglAcntAll.json").mock(
        return_value=httpx.Response(200, json=fs_all_response)
    )
    async with client:
        result = await client.get_financial_statements(
            "00126380", "2024", reprt_code="11014", fs_div="OFS"
        )
    params = route.calls.last.request.url.params
    assert params["fs_div"] == "OFS"
    assert params["reprt_code"] == "11014"

    items = result["items"]
    assert len(items) == len(fs_all_response["list"])
    first = items[0]
    assert first["sj_div"] == "BS"
    assert first["account_id"] == "ifrs-full_Assets"
    assert first["thstrm_amount"] == 514_531_948_000_000  # "514531948000000" (쉼표 없음)
    assert first["account_detail"] is None  # "-" 는 없음으로
    op = next(i for i in items if i["account_id"] == "dart_OperatingIncomeLoss")
    assert op["thstrm_add_amount"] is None  # ""


@respx.mock
async def test_get_financial_statements_filters_sj_div(client, base_url, fs_all_response):
    respx.get(f"{base_url}/fnlttSinglAcntAll.json").mock(
        return_value=httpx.Response(200, json=fs_all_response)
    )
    async with client:
        result = await client.get_financial_statements("00126380", "2024", sj_div="IS")
    assert result["items"] and all(i["sj_div"] == "IS" for i in result["items"])


@respx.mock
async def test_get_financial_statements_no_data_is_empty(client, base_url, no_data_response):
    respx.get(f"{base_url}/fnlttSinglAcntAll.json").mock(
        return_value=httpx.Response(200, json=no_data_response)
    )
    async with client:
        result = await client.get_financial_statements("00126380", "1990")
    assert result["items"] == []


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"bsns_year": "24"}, "bsns_year"),
        ({"bsns_year": "2024", "reprt_code": "11015"}, "reprt_code"),
        ({"bsns_year": "2024", "fs_div": "XXX"}, "fs_div"),
        ({"bsns_year": "2024", "sj_div": "XX"}, "sj_div"),
    ],
)
async def test_get_financial_statements_validates_input(client, kwargs, match):
    with pytest.raises(ValueError, match=match):
        await client.get_financial_statements("00126380", **kwargs)


# -- 공시 원문 --------------------------------------------------------------


@respx.mock
async def test_get_document_extracts_text_from_main_file(client, base_url, document_zip):
    route = respx.get(f"{base_url}/document.xml").mock(
        return_value=httpx.Response(
            200,
            content=document_zip,
            headers={"content-type": "application/x-msdownload;charset=UTF-8"},
        )
    )
    async with client:
        doc = await client.get_document("20250325800172")
    assert route.calls.last.request.url.params["rcept_no"] == "20250325800172"
    assert doc["rcept_no"] == "20250325800172"
    assert doc["file_name"] == "20250325800172.xml"  # 첨부(_00001)가 아니라 본문
    assert doc["attachment_files"] == ["20250325800172_00001.xml"]
    text = doc["text"]
    assert "대표이사 변경" in text
    assert "변경 전 한종희" in text  # 셀 사이 공백 하나
    assert "기타 & 참고사항 <없음>" in text  # 엔티티 복원
    assert "font-family" not in text and "var x" not in text  # style/script 제거
    assert "<" not in text.replace("<없음>", "")


@respx.mock
async def test_get_document_error_xml_raises(client, base_url, document_error_xml):
    respx.get(f"{base_url}/document.xml").mock(
        return_value=httpx.Response(
            200, text=document_error_xml, headers={"content-type": "application/xml;charset=UTF-8"}
        )
    )
    async with client:
        with pytest.raises(DataGoAPIError) as exc_info:
            await client.get_document("00000000000000")
    assert exc_info.value.result_code == "013"
    assert "접수번호 오류" in str(exc_info.value)


async def test_get_document_validates_rcept_no(client):
    with pytest.raises(ValueError, match="rcept_no"):
        await client.get_document("2025")


# -- 기업코드 --------------------------------------------------------------


@respx.mock
async def test_download_corp_codes_parses_zip(client, base_url, corpcode_zip):
    respx.get(f"{base_url}/corpCode.xml").mock(
        return_value=httpx.Response(200, content=corpcode_zip)
    )
    async with client:
        entries = await client.download_corp_codes()
    assert len(entries) == 3
    assert entries[1]["corp_code"] == "00126380"


@respx.mock
async def test_download_corp_codes_error_xml_raises(client, base_url):
    respx.get(f"{base_url}/corpCode.xml").mock(
        return_value=httpx.Response(
            200,
            text='<?xml version="1.0"?><result><status>010</status><message>등록되지 않은 인증키입니다.</message></result>',
            headers={"content-type": "application/xml;charset=UTF-8"},
        )
    )
    async with client:
        with pytest.raises(DataGoAPIError, match=r"\[010\]"):
            await client.download_corp_codes()


@respx.mock
async def test_default_bgn_de_is_anchored_on_end_de(client, base_url, disclosure_list_response):
    route = respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=disclosure_list_response)
    )
    async with client:
        await client.list_disclosures(corp_code="00126380", end_de="20231231")
    assert route.calls.last.request.url.params["bgn_de"] == "20221231"


async def test_bgn_de_after_end_de_is_rejected(client):
    with pytest.raises(ValueError, match="bgn_de"):
        await client.list_disclosures(bgn_de="20250201", end_de="20250101")


@respx.mock
async def test_get_document_is_cached_per_rcept_no(client, base_url, document_zip):
    route = respx.get(f"{base_url}/document.xml").mock(
        return_value=httpx.Response(200, content=document_zip)
    )
    async with client:
        first = await client.get_document("20250325800172")
        second = await client.get_document("20250325800172")
    assert route.call_count == 1
    assert first == second
