"""MCP server for 국세청 사업자등록정보 진위확인 및 상태조회."""

import json
from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import MAX_BATCH, NtsBusinessVerificationAPIClient
from .models import BusinessInfo, BusinessStatus


load_dotenv()

mcp = MCPServer("NTS Business Verification")

OptStr = Optional[str]


def _digits(value: str, length: int, label: str) -> str:
    cleaned = value.replace("-", "").strip()
    if len(cleaned) != length or not cleaned.isdigit():
        raise ValueError(f"{label}는 {length}자리 숫자여야 합니다: {value}")
    return cleaned


def _status_dict(business: BusinessStatus) -> dict[str, Any]:
    """빈 문자열 필드는 빼고 snake_case 영문 키로."""
    out: dict[str, Any] = {
        "business_number": business.b_no,
        "status": business.b_stt,
        "status_code": business.b_stt_cd,
        "tax_type": business.tax_type,
        "tax_type_code": business.tax_type_cd,
    }
    optional = {
        "end_date": business.end_dt,
        "utcc_yn": business.utcc_yn,
        "tax_type_change_date": business.tax_type_change_dt,
        "invoice_apply_date": business.invoice_apply_dt,
        "rbf_tax_type": business.rbf_tax_type,
        "rbf_tax_type_code": business.rbf_tax_type_cd,
    }
    out.update({k: v for k, v in optional.items() if v})
    return out


@mcp.tool(annotations=READ_ONLY)
async def validate_business(
    business_number: Annotated[str, Field(description="사업자등록번호 10자리 (하이픈 허용)")],
    start_date: Annotated[str, Field(description="개업일자 YYYYMMDD (하이픈 허용)")],
    representative_name: Annotated[str, Field(description="대표자성명")],
    representative_name2: Annotated[
        OptStr, Field(description="대표자성명2 (외국인 한글명)")
    ] = None,
    business_name: Annotated[OptStr, Field(description="상호")] = None,
    corp_number: Annotated[OptStr, Field(description="법인등록번호 13자리")] = None,
    business_sector: Annotated[OptStr, Field(description="주업태명")] = None,
    business_type: Annotated[OptStr, Field(description="주종목명")] = None,
    business_address: Annotated[OptStr, Field(description="사업장주소")] = None,
) -> dict[str, Any]:
    """사업자등록정보 진위확인을 수행합니다. Validate business registration information.

    Returns business_number, valid (01: 일치, 02: 불일치), valid_msg, status (일치 시 상태 정보).
    """
    async with tool_errors():
        info = BusinessInfo(
            b_no=_digits(business_number, 10, "사업자등록번호"),
            start_dt=_digits(start_date, 8, "개업일자"),
            p_nm=representative_name,
            p_nm2=representative_name2,
            b_nm=business_name,
            corp_no=_digits(corp_number, 13, "법인등록번호") if corp_number else None,
            b_sector=business_sector,
            b_type=business_type,
            b_adr=business_address,
        )
        async with NtsBusinessVerificationAPIClient() as client:
            response = await client.validate_business([info])
        if not response.data:
            raise ValueError("응답 데이터가 없습니다.")
    result = response.data[0]
    return {
        "business_number": result.b_no,
        "valid": result.valid,
        "valid_msg": result.valid_msg
        or ("일치" if result.valid == "01" else "확인할 수 없습니다"),
        "status": result.status.model_dump() if result.status else None,
    }


@mcp.tool(annotations=READ_ONLY)
async def check_business_status(
    business_numbers: Annotated[
        str, Field(description="사업자등록번호 목록, 쉼표 구분, 최대 100개 (하이픈 허용)")
    ],
) -> dict[str, Any]:
    """사업자등록 상태를 조회합니다. Check business registration status.

    Returns request_count, match_count, businesses[] (status_code 01: 계속사업자, 02: 휴업자,
    03: 폐업자; 미등록 번호는 tax_type 에 안내 문구가 온다).
    """
    async with tool_errors():
        numbers = [n.strip().replace("-", "") for n in business_numbers.split(",") if n.strip()]
        invalid = [n for n in numbers if len(n) != 10 or not n.isdigit()]
        if invalid:
            raise ValueError(
                f"잘못된 사업자등록번호: {', '.join(invalid)} (10자리 숫자여야 합니다)"
            )
        if len(numbers) > MAX_BATCH:
            raise ValueError(
                f"한 번에 최대 {MAX_BATCH}개까지 조회 가능합니다. (요청: {len(numbers)}개)"
            )
        async with NtsBusinessVerificationAPIClient() as client:
            response = await client.check_status(numbers)
    return {
        "request_count": response.request_cnt,
        "match_count": response.match_cnt,
        "businesses": [_status_dict(b) for b in response.data],
    }


@mcp.tool(annotations=READ_ONLY)
async def batch_validate_businesses(
    businesses_json: Annotated[
        str,
        Field(
            description=(
                "JSON 배열 문자열, 최대 100개. 각 항목 필수: b_no, start_dt, p_nm. "
                "선택: p_nm2, b_nm, corp_no, b_sector, b_type, b_adr. "
                '예: [{"b_no": "1234567890", "start_dt": "20200101", "p_nm": "홍길동"}]'
            )
        ),
    ],
) -> dict[str, Any]:
    """여러 사업자등록정보를 한 번에 진위확인합니다. Batch validate business registrations.

    Returns request_count, valid_count, results[] (business_number, valid, valid_msg, status).
    """
    async with tool_errors():
        try:
            rows = json.loads(businesses_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 오류: {e}") from e
        if not isinstance(rows, list):
            raise ValueError("입력은 배열 형식이어야 합니다: [{...}, {...}]")
        if len(rows) > MAX_BATCH:
            raise ValueError(
                f"한 번에 최대 {MAX_BATCH}개까지 진위확인 가능합니다. (요청: {len(rows)}개)"
            )
        businesses = []
        for idx, row in enumerate(rows):
            missing = [k for k in ("b_no", "start_dt", "p_nm") if not row.get(k)]
            if missing:
                raise ValueError(f"인덱스 {idx}: 필수 필드 누락 — {', '.join(missing)}")
            row = dict(row)
            row["b_no"] = _digits(row["b_no"], 10, "사업자등록번호")
            row["start_dt"] = _digits(row["start_dt"], 8, "개업일자")
            if row.get("corp_no"):
                row["corp_no"] = _digits(row["corp_no"], 13, "법인등록번호")
            businesses.append(BusinessInfo(**row))
        async with NtsBusinessVerificationAPIClient() as client:
            response = await client.validate_business(businesses)
    return {
        "request_count": response.request_cnt,
        "valid_count": response.valid_cnt,
        "results": [
            {
                "business_number": r.b_no,
                "valid": r.valid,
                "valid_msg": r.valid_msg or ("일치" if r.valid == "01" else "확인할 수 없습니다"),
                "status": r.status.model_dump() if r.status else None,
            }
            for r in response.data
        ],
    }


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(NtsBusinessVerificationAPIClient.key_env_prefix)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
