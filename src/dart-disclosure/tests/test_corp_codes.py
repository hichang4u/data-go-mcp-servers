"""기업코드 스냅샷 — CORPCODE.xml 파싱과 검색."""

import pytest

from data_go_mcp.dart_disclosure.corp_codes import (
    load_snapshot,
    parse_corp_code_zip,
    search_corp_codes,
)


@pytest.fixture
def entries(corpcode_zip):
    return parse_corp_code_zip(corpcode_zip)


def test_parse_zip_reads_all_entries_and_blank_stock_code(corpcode_zip):
    entries = parse_corp_code_zip(corpcode_zip)
    assert [e["corp_code"] for e in entries] == ["00434003", "00126380", "00258801"]
    listed = entries[1]
    assert listed == {
        "corp_code": "00126380",
        "corp_name": "삼성전자",
        "stock_code": "005930",
        "corp_eng_name": "SAMSUNG ELECTRONICS CO,.LTD",
    }
    assert entries[0]["stock_code"] == ""  # 비상장은 공백 한 칸으로 온다


def test_exact_name_ranks_before_partial_match(entries):
    result = search_corp_codes("삼성전자", entries)
    assert [e["corp_name"] for e in result["items"]] == ["삼성전자", "삼성전자서비스"]
    assert result["total_count"] == 2


def test_search_ignores_case_and_spaces(entries):
    assert search_corp_codes("samsung electronics", entries)["items"][0]["corp_code"] == "00126380"
    assert search_corp_codes(" 삼성 전자 ", entries)["items"][0]["corp_code"] == "00126380"


def test_search_by_stock_code(entries):
    result = search_corp_codes("005930", entries)
    assert [e["corp_code"] for e in result["items"]] == ["00126380"]


def test_listed_only_drops_unlisted(entries):
    result = search_corp_codes("삼성", entries, listed_only=True)
    assert [e["corp_code"] for e in result["items"]] == ["00126380"]
    assert result["total_count"] == 1


def test_limit_caps_items_but_not_total(entries):
    result = search_corp_codes("삼성", entries, limit=1)
    assert len(result["items"]) == 1
    assert result["total_count"] == 2


def test_no_match_is_empty_not_error(entries):
    assert search_corp_codes("없는회사", entries) == {"items": [], "total_count": 0}


def test_blank_query_is_rejected(entries):
    with pytest.raises(ValueError, match="query"):
        search_corp_codes("   ", entries)


def test_bundled_snapshot_loads_and_contains_samsung():
    snapshot = load_snapshot()
    assert len(snapshot.entries) > 100_000
    assert len(snapshot.generated) == 8 and snapshot.generated.isdigit()
    hit = search_corp_codes("삼성전자", listed_only=True)["items"][0]
    assert hit["corp_code"] == "00126380" and hit["stock_code"] == "005930"
