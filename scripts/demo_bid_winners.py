"""업체 하나의 나라장터 낙찰 이력을 실제로 조회해 보여준다.

나라장터 API 는 낙찰업체로 검색할 수 없어서(사업자번호를 줘도 무시된다) 기간 안의 낙찰 건을
전부 받아 걸러낸다. 이 화면은 그 과정과 결과를 그대로 보여준다 — 훑은 건수까지.

사용법:
    uv run python scripts/demo_bid_winners.py [사업자등록번호]
    uv run python scripts/demo_bid_winners.py 111-81-26895 --business-type 물품

`API_KEY` 가 필요하다. 기본 기간은 최근 1개월이며 API 한도상 최대 3개월이다.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time

from dotenv import load_dotenv
from mcp import Client
from mcp.types import TextContent


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

load_dotenv()

# httpx 는 INFO 로 요청 URL 을 남기는데 거기에 serviceKey 가 들어 있다. 이 스크립트의 출력은
# 캡처해 공유하라고 만든 것이므로 키가 화면에 찍히지 않도록 반드시 올린다.
logging.getLogger().setLevel(logging.WARNING)
for _noisy in ("httpx", "httpcore", "mcp"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

DEFAULT_BUSINESS_NUMBER = "111-81-26895"  # (주)레드캡투어 — 공공 차량 임차 낙찰이 잦다
BAR = "─" * 78


def _fmt_won(value: object) -> str:
    """원 단위 금액을 읽기 쉽게."""
    try:
        amount = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "-"
    if amount >= 10**8:
        return f"{amount / 10**8:,.1f}억"
    return f"{amount / 10**4:,.0f}만"


async def run(business_number: str, business_type: str, start: str | None, end: str | None) -> int:
    """낙찰 이력을 조회해 출력한다."""
    from data_go_mcp.pps_narajangteo.server import mcp

    digits = re.sub(r"\D", "", business_number)
    args: dict[str, object] = {"business_number": digits, "business_type": business_type}
    if start:
        args["start_date"] = start
    if end:
        args["end_date"] = end

    print(BAR)
    print(f"  사업자번호 {business_number} · {business_type} 낙찰 이력")
    print(BAR)
    print("\n  조달청 나라장터")
    print("  ·· find_bid_winners")

    async with Client(mcp) as client:
        started = time.time()
        result = await client.call_tool("find_bid_winners", args)
        elapsed = time.time() - started

    content = result.content[0] if result.content else None
    text = content.text if isinstance(content, TextContent) else ""
    if result.is_error:
        print(f"     실패 ({elapsed:.1f}초) {' '.join(text.split())[:100]}")
        return 1

    data = json.loads(text)
    print(f"     ({elapsed:.1f}초)")
    print(f"     {data['message']}")  # 덜 훑었으면 message 에 경고가 이미 붙는다
    items = data["items"]
    if items:
        print(f"\n     {items[0]['company_name']} · 대표 {items[0].get('ceo_name') or '-'}")
        print()
        for bid in items:
            print(
                f"     {bid['opening_date']}  {_fmt_won(bid['winning_amount']):>8}"
                f"  {(bid['bid_notice_name'] or '')[:30]:30}  {(bid['demand_institution'] or '')[:22]}"
            )
    print(f"\n{BAR}")
    print(
        f"  업체 검색이 없는 API 에서 {data['scanned_count']:,}건을 훑어 {len(items)}건을 찾았습니다."
    )
    print(BAR)
    return 0


def main() -> int:
    """인자를 읽고 조회한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("business_number", nargs="?", default=DEFAULT_BUSINESS_NUMBER)
    parser.add_argument("--business-type", default="물품", help="용역/물품/공사/외자 (기본 물품)")
    parser.add_argument("--start-date", default=None, help="시작일 YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="종료일 YYYY-MM-DD")
    args = parser.parse_args()

    if not os.getenv("API_KEY"):
        print("API_KEY 환경변수가 필요합니다 (.env 또는 export)", file=sys.stderr)
        return 1
    return asyncio.run(
        run(args.business_number, args.business_type, args.start_date, args.end_date)
    )


if __name__ == "__main__":
    sys.exit(main())
