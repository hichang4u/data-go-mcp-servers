"""DataGoAPIError / RESULT_CODES 테스트."""

from data_go_mcp.core.errors import RESULT_CODES, DataGoAPIError


def test_error_carries_code_and_message():
    err = DataGoAPIError("30", "SERVICE_KEY_IS_NOT_REGISTERED_ERROR")

    assert err.result_code == "30"
    assert err.result_msg == "SERVICE_KEY_IS_NOT_REGISTERED_ERROR"


def test_str_includes_code_message_and_korean_description():
    err = DataGoAPIError("30", "SERVICE_KEY_IS_NOT_REGISTERED_ERROR")

    assert str(err) == "[30] SERVICE_KEY_IS_NOT_REGISTERED_ERROR (등록되지 않은 서비스키)"


def test_unknown_code_has_no_description_suffix():
    err = DataGoAPIError("77", "SOMETHING")

    assert str(err) == "[77] SOMETHING"


def test_result_codes_table_covers_documented_codes():
    # fsc api_client.py 에 있던 표 그대로 (data.go.kr 공통 코드)
    assert RESULT_CODES["00"] == "정상처리"
    assert RESULT_CODES["12"].startswith("NO_OPENAPI_SERVICE_ERROR")
    assert RESULT_CODES["22"].startswith("LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR")
    assert RESULT_CODES["99"].startswith("UNKNOWN_ERROR")


def test_source_defaults_to_data_go_kr():
    assert DataGoAPIError("30", "KEY").source == "data.go.kr"


def test_custom_source_is_kept():
    err = DataGoAPIError("010", "등록되지 않은 인증키입니다.", source="OpenDART")
    assert err.source == "OpenDART"
    assert str(err) == "[010] 등록되지 않은 인증키입니다."
