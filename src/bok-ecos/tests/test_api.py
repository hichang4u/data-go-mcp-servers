"""ECOS 클라이언트 테스트 — 키가 경로 세그먼트이고 오류가 RESULT 로 오는 것이 핵심."""

import httpx
import pytest
import respx

from data_go_mcp.bok_ecos.api_client import BokEcosAPIClient
from data_go_mcp.core import DataGoAPIError

from .conftest import ERROR_COUNT, ERROR_KEY, ERROR_NO_DATA


def test_client_requires_its_own_key(monkeypatch):
    """ECOS 는 data.go.kr 이 아니다 — 공통 API_KEY 로 대체되면 안 된다."""
    monkeypatch.delenv("BOK_ECOS_API_KEY", raising=False)
    monkeypatch.setenv("API_KEY", "data-go-kr-key")
    with pytest.raises(ValueError) as exc:
        BokEcosAPIClient()
    assert "BOK_ECOS_API_KEY" in str(exc.value)
    assert "ecos.bok.or.kr" in str(exc.value)


@respx.mock
async def test_key_and_arguments_go_into_the_path(base_url, search_result):
    """키·언어·건수·조건이 모두 경로 세그먼트다 (쿼리스트링이 아니다)."""
    route = respx.get(
        f"{base_url}/StatisticSearch/test-key/json/kr/1/100/722Y001/M/202401/202403/0101000"
    ).mock(return_value=httpx.Response(200, json=search_result))
    async with BokEcosAPIClient() as client:
        result = await client.search("722Y001", "M", "202401", "202403", ["0101000"])

    assert route.called
    assert not route.calls.last.request.url.params
    assert result["total_count"] == 27
    assert result["items"][0]["item_name1"] == "한국은행 기준금리"
    assert result["items"][0]["value"] == 3.5


@respx.mock
async def test_search_sends_up_to_four_item_codes(base_url, search_result):
    respx.get(url__startswith=base_url).mock(return_value=httpx.Response(200, json=search_result))
    async with BokEcosAPIClient() as client:
        await client.search("901Y009", "M", "202401", "202403", ["A", "B", "C", "D"])
        assert str(respx.calls.last.request.url).endswith("/202401/202403/A/B/C/D")


async def test_search_rejects_more_than_four_item_codes():
    async with BokEcosAPIClient() as client:
        with pytest.raises(ValueError, match="4개"):
            await client.search("901Y009", "M", "202401", "202403", ["A", "B", "C", "D", "E"])


@pytest.mark.parametrize(
    "cycle, start, end",
    [
        ("M", "2024", "202403"),  # 월인데 연 형식
        ("Q", "20231", "20234"),  # 분기는 2023Q1 형식 (ERROR-101 로 확인)
        ("D", "202401", "202403"),
        ("A", "202401", "202403"),
    ],
)
async def test_search_rejects_time_format_mismatched_with_cycle(cycle, start, end):
    async with BokEcosAPIClient() as client:
        with pytest.raises(ValueError, match="형식"):
            await client.search("722Y001", cycle, start, end)


async def test_search_rejects_unknown_cycle():
    async with BokEcosAPIClient() as client:
        with pytest.raises(ValueError, match="주기"):
            await client.search("722Y001", "X", "202401", "202403")


@respx.mock
async def test_no_data_is_an_empty_result_not_an_error(base_url):
    """INFO-200 은 '해당하는 데이터가 없습니다' — 오류가 아니라 빈 결과."""
    respx.get(url__startswith=base_url).mock(return_value=httpx.Response(200, json=ERROR_NO_DATA))
    async with BokEcosAPIClient() as client:
        result = await client.search("722Y001", "M", "209901", "209912")
    assert result == {"items": [], "total_count": 0}


@respx.mock
async def test_invalid_key_raises_with_ecos_source(base_url):
    respx.get(url__startswith=base_url).mock(return_value=httpx.Response(200, json=ERROR_KEY))
    async with BokEcosAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.search("722Y001", "M", "202401", "202403")
    assert exc.value.result_code == "INFO-100"
    assert exc.value.source == "한국은행 ECOS"


@respx.mock
async def test_row_limit_error_is_raised(base_url):
    """sample 키는 10건까지 — ERROR-301 이 그대로 전달돼야 원인을 안다."""
    respx.get(url__startswith=base_url).mock(return_value=httpx.Response(200, json=ERROR_COUNT))
    async with BokEcosAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.search("722Y001", "M", "202401", "202403")
    assert exc.value.result_code == "ERROR-301"
    assert "sample" in exc.value.result_msg


@respx.mock
async def test_find_tables_filters_by_name_and_cycle(base_url, table_list):
    """통계표 검색 API 가 없어 전체 목록을 받아 이름으로 거른다."""
    respx.get(url__startswith=f"{base_url}/StatisticTableList").mock(
        return_value=httpx.Response(200, json=table_list)
    )
    async with BokEcosAPIClient() as client:
        hits = await client.find_tables("기준금리")
        assert [t["stat_code"] for t in hits] == ["722Y001"]

        quarterly = await client.find_tables("가계신용", cycle="Q")
        assert [t["stat_code"] for t in quarterly] == ["151Y001"]

        assert await client.find_tables("기준금리", cycle="D") == []


@respx.mock
async def test_find_tables_skips_rows_that_cannot_be_searched(base_url, table_list):
    """SRCH_YN=N 은 분류 노드라 조회할 수 없다."""
    respx.get(url__startswith=f"{base_url}/StatisticTableList").mock(
        return_value=httpx.Response(200, json=table_list)
    )
    async with BokEcosAPIClient() as client:
        assert await client.find_tables("통화/금융") == []  # SRCH_YN=N 인 분류 노드
        assert [t["stat_code"] for t in await client.find_tables("본원통화")] == ["102Y004"]


@respx.mock
async def test_table_list_is_fetched_once_per_process(base_url, table_list):
    """844건을 툴 호출마다 다시 받지 않는다."""
    route = respx.get(url__startswith=f"{base_url}/StatisticTableList").mock(
        return_value=httpx.Response(200, json=table_list)
    )
    async with BokEcosAPIClient() as client:
        await client.find_tables("기준금리")
        calls_after_first = route.call_count
        await client.find_tables("가계신용")
    assert route.call_count == calls_after_first


@respx.mock
async def test_item_list_reports_searchable_period(base_url, item_list):
    respx.get(f"{base_url}/StatisticItemList/test-key/json/kr/1/100/722Y001").mock(
        return_value=httpx.Response(200, json=item_list)
    )
    async with BokEcosAPIClient() as client:
        result = await client.get_items("722Y001")

    monthly = [i for i in result["items"] if i["cycle"] == "M"][0]
    assert (monthly["start_time"], monthly["end_time"]) == ("199901", "202609")
    assert monthly["unit_name"] == "연%"


@respx.mock
async def test_key_statistics_values_are_numbers(base_url, key_statistics):
    respx.get(url__startswith=f"{base_url}/KeyStatisticList").mock(
        return_value=httpx.Response(200, json=key_statistics)
    )
    async with BokEcosAPIClient() as client:
        result = await client.get_key_statistics()
    assert result["items"][0]["value"] == 1356.7
    assert result["items"][0]["class_name"] == "환율"


@respx.mock
async def test_sample_key_requests_are_clamped_to_ten_rows(base_url, key_statistics, monkeypatch):
    """sample 키는 10건을 넘기면 ERROR-301 — 툴 기본값(100/200)이 그대로 나가면 안 된다."""
    monkeypatch.setenv("BOK_ECOS_API_KEY", "sample")
    respx.get(url__startswith=base_url).mock(return_value=httpx.Response(200, json=key_statistics))
    async with BokEcosAPIClient() as client:
        await client.get_key_statistics(num_of_rows=200)
        assert str(respx.calls.last.request.url).endswith("/sample/json/kr/1/10")

        await client.get_word("기준금리", num_of_rows=100)
        assert "/1/10/" in str(respx.calls.last.request.url)

        await client.search("722Y001", "M", "202401", "202403", num_of_rows=100)
        assert "/1/10/" in str(respx.calls.last.request.url)


@respx.mock
async def test_real_key_keeps_the_requested_row_count(base_url, key_statistics):
    respx.get(url__startswith=base_url).mock(return_value=httpx.Response(200, json=key_statistics))
    async with BokEcosAPIClient() as client:
        await client.get_key_statistics(num_of_rows=200)
    assert str(respx.calls.last.request.url).endswith("/1/200")


@respx.mock
async def test_concurrent_table_searches_do_not_duplicate_the_cache(base_url, table_list):
    """동시에 두 번 불러도 캐시가 두 배가 되면 안 된다 (클라이언트는 툴을 병렬 호출한다)."""
    import asyncio

    from data_go_mcp.bok_ecos import api_client as mod

    async def slow(request):  # 두 호출이 겹치도록 응답을 늦춘다
        await asyncio.sleep(0.02)
        return httpx.Response(200, json=table_list)

    respx.get(url__startswith=f"{base_url}/StatisticTableList").mock(side_effect=slow)
    async with BokEcosAPIClient() as client:
        first, second = await asyncio.gather(
            client.find_tables("기준금리"), client.find_tables("기준금리")
        )

    assert len(mod._table_cache) == len(table_list["StatisticTableList"]["row"])
    assert first == second == [first[0]]


@respx.mock
async def test_missing_total_count_does_not_truncate_the_table_list(base_url, table_list):
    """list_total_count 가 없다고 첫 페이지만 캐시하면 표 대부분을 조용히 잃는다."""
    page = {"StatisticTableList": {"row": table_list["StatisticTableList"]["row"]}}
    route = respx.get(url__startswith=f"{base_url}/StatisticTableList").mock(
        return_value=httpx.Response(200, json=page)
    )
    async with BokEcosAPIClient() as client:
        client_page_size = client.page_size
        await client.find_tables("기준금리")

    # 한 페이지가 page_size 보다 적게 왔으면 거기서 끝 — 4건 < 100건이므로 한 번만 호출
    assert len(table_list["StatisticTableList"]["row"]) < client_page_size
    assert route.call_count == 1


@respx.mock
async def test_partial_table_page_without_total_keeps_paging(base_url):
    """가득 찬 페이지가 total 없이 오면 다음 페이지도 받아야 한다."""
    full = {
        "StatisticTableList": {
            "row": [
                {"STAT_CODE": f"{i:06d}", "STAT_NAME": f"표 {i}", "CYCLE": "M", "SRCH_YN": "Y"}
                for i in range(100)
            ]
        }
    }
    empty = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}
    route = respx.get(url__startswith=f"{base_url}/StatisticTableList").mock(
        side_effect=[httpx.Response(200, json=full), httpx.Response(200, json=empty)]
    )
    async with BokEcosAPIClient() as client:
        await client.find_tables("표 1")
    assert route.call_count == 2


async def test_item_code_gap_is_rejected():
    """항목 코드는 위치 인자다 — 1을 비우고 2만 주면 2가 1 자리로 밀려 다른 값이 온다."""
    async with BokEcosAPIClient() as client:
        with pytest.raises(ValueError, match="순서대로"):
            await client.search("901Y009", "M", "202401", "202403", [None, "Group2Code"])
