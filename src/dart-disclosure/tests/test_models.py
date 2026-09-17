"""모델 변환 — 금액 문자열 정규화 (API 는 금액을 문자열로 준다)."""

from data_go_mcp.dart_disclosure.models import FinancialStatementItem, KeyAccount


def test_amounts_with_and_without_commas_become_int():
    assert (
        KeyAccount.model_validate({"thstrm_amount": "514,531,948,000,000"}).thstrm_amount
        == 514_531_948_000_000
    )
    assert (
        FinancialStatementItem.model_validate({"thstrm_amount": "-241413000000"}).thstrm_amount
        == -241_413_000_000
    )


def test_blank_and_dash_amounts_become_none():
    item = FinancialStatementItem.model_validate({"thstrm_amount": "", "frmtrm_amount": "-"})
    assert item.thstrm_amount is None and item.frmtrm_amount is None
    assert item.thstrm_add_amount is None


def test_decimal_amount_is_kept_as_float_not_error():
    # 주당이익 등 소수 금액이 와도 호출 전체가 실패하면 안 된다
    item = FinancialStatementItem.model_validate(
        {"thstrm_amount": "2,569.5", "frmtrm_amount": "1.25"}
    )
    assert item.thstrm_amount == 2569.5 and item.frmtrm_amount == 1.25


def test_unparseable_amount_becomes_none_without_failing_row():
    assert KeyAccount.model_validate({"thstrm_amount": "N/A"}).thstrm_amount is None
