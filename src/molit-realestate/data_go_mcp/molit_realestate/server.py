"""MCP server for 국토교통부 부동산 실거래가.

법정동코드(시군구 5자리)와 계약년월로 매매·전월세 신고 내역을 조회한다. 코드는 nps 서버의
``find_region_code`` 가 찾아 주며, 거기서 오는 10자리 코드를 그대로 넣어도 된다.
"""

from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import (
    BUILDING_KINDS,
    RENT_TYPES,
    TRADE_TYPES,
    MolitRealEstateAPIClient,
    normalize_region_code,
)


load_dotenv()

mcp = MCPServer("MOLIT Real Estate")

RegionCode = Annotated[
    str,
    Field(
        description=(
            "법정동코드. 시군구 5자리(예: 11680 강남구) 또는 10자리 전체 코드. "
            "모르면 nps 서버의 find_region_code 로 먼저 찾는다"
        )
    ),
]
DealYm = Annotated[str, Field(description="계약년월 YYYYMM (예: 202608)")]
NumOfRows = Annotated[int, Field(description="한 페이지 결과 수 (기본값: 100, 최대: 1000)")]
BuildingRows = Annotated[int, Field(description="한 페이지 결과 수 (기본값: 50, 최대: 1000)")]
PageNo = Annotated[int, Field(description="페이지 번호 (기본값: 1)")]


@mcp.tool(annotations=READ_ONLY)
async def search_property_trades(
    region_code: RegionCode,
    deal_ym: DealYm,
    property_type: Annotated[
        str, Field(description=f"부동산 종류: {', '.join(TRADE_TYPES)}")
    ] = "아파트",
    num_of_rows: NumOfRows = 100,
    page_no: PageNo = 1,
) -> dict[str, Any]:
    """부동산 매매 실거래가를 조회합니다. Search reported sale prices of real estate.

    한 번에 **지역(시군구) 하나 + 계약년월 하나**만 조회합니다 (API 제약). 여러 달을 보려면
    월별로 나눠 호출하세요. 금액 단위는 **만원**이고, 해제된 거래는 cancelled=true 로 표시되니
    시세를 볼 때는 제외하세요. 면적은 종류마다 뜻이 달라 각각 다른 필드로 돌려줍니다
    (전용면적/연면적/대지면적/거래면적).
    """
    async with tool_errors():
        async with MolitRealEstateAPIClient() as client:
            result = await client.search_trades(
                region_code, deal_ym, property_type, num_of_rows, page_no
            )
        region = normalize_region_code(region_code)
    return {
        **result,
        "region_code": region,
        "deal_ym": deal_ym,
        "property_type": property_type,
        "page_no": page_no,
    }


@mcp.tool(annotations=READ_ONLY)
async def search_property_rents(
    region_code: RegionCode,
    deal_ym: DealYm,
    property_type: Annotated[
        str, Field(description=f"부동산 종류: {', '.join(RENT_TYPES)} (토지·상업업무용은 없음)")
    ] = "아파트",
    num_of_rows: NumOfRows = 100,
    page_no: PageNo = 1,
) -> dict[str, Any]:
    """부동산 전월세 실거래가를 조회합니다. Search reported rent contracts of real estate.

    한 번에 **지역(시군구) 하나 + 계약년월 하나**만 조회합니다. 보증금·월세 단위는 **만원**이고,
    월세가 0이면 전세입니다 (rent_type 으로 구분해 돌려줍니다). 갱신 계약이면 종전 보증금·월세가
    함께 옵니다.
    """
    async with tool_errors():
        async with MolitRealEstateAPIClient() as client:
            result = await client.search_rents(
                region_code, deal_ym, property_type, num_of_rows, page_no
            )
        region = normalize_region_code(region_code)
    return {
        **result,
        "region_code": region,
        "deal_ym": deal_ym,
        "property_type": property_type,
        "page_no": page_no,
    }


@mcp.tool(annotations=READ_ONLY)
async def get_building_register(
    region_code: Annotated[
        str,
        Field(
            description=(
                "법정동코드 10자리(예: 1168010500 삼성동) 또는 시군구 5자리. "
                "5자리면 bjdong_code 도 함께 준다"
            )
        ),
    ],
    bun: Annotated[str, Field(description="본번 (예: 493). 실거래 결과의 bun 을 그대로 쓴다")],
    ji: Annotated[
        Optional[str], Field(description="부번 (예: 0). 없으면 0000 으로 조회한다")
    ] = None,
    bjdong_code: Annotated[
        Optional[str], Field(description="법정동코드 5자리. region_code 가 10자리면 필요 없다")
    ] = None,
    kind: Annotated[str, Field(description=f"대장 종류: {', '.join(BUILDING_KINDS)}")] = "표제부",
    num_of_rows: BuildingRows = 50,
    page_no: PageNo = 1,
) -> dict[str, Any]:
    """건축물대장을 조회합니다. Look up the building register for one lot.

    지번(본번·부번) 기준입니다. **실거래 결과의 bun/ji 를 그대로 넘기면** 그 거래가 일어난
    건물의 연면적·용도·구조·사용승인일을 볼 수 있습니다. 종류를 바꾸면 층별 면적(층별개요),
    용도지역(지역지구) 등도 조회됩니다. 집합건물과 일반건축물은 채워지는 종류가 달라, 어떤
    종류는 0건으로 옵니다.

    이 API 는 일시적으로 SERVICETIMEOUT 을 돌려줄 때가 있어 몇 번 다시 시도합니다.
    """
    async with tool_errors():
        async with MolitRealEstateAPIClient() as client:
            result = await client.get_building_register(
                region_code=region_code,
                bjdong_code=bjdong_code,
                bun=bun,
                ji=ji,
                kind=kind,
                num_of_rows=num_of_rows,
                page_no=page_no,
            )
    return {**result, "kind": kind.strip(), "page_no": page_no}


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(MolitRealEstateAPIClient.key_env_prefix)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
