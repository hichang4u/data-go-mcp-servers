"""지역 하나의 한 달치 아파트 실거래를 조회해 요약한다.

지역코드는 nps 서버의 ``find_region_code`` 로 찾는다 — 사용자는 법정동코드를 모르기 때문에
이 두 단계가 한 대화에서 이어지는 것이 이 저장소의 쓸모다.

사용법:
    uv run python scripts/demo_realestate.py [지역명] [계약년월]
    uv run python scripts/demo_realestate.py 해운대구 202608

``API_KEY`` 가 필요하고, 부동산 종류마다 활용신청이 따로 필요하다.
"""

import argparse
import asyncio
import json
import logging
import os
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

DEFAULT_REGION = "강남구"
DEFAULT_MONTH = "202608"
BAR = "─" * 78
PYEONG = 3.3058  # ㎡ → 평


async def call(client: Client, tool: str, args: dict) -> tuple[dict | None, float]:
    """툴 하나를 부르고 결과와 소요 시간을 돌려준다."""
    started = time.time()
    result = await client.call_tool(tool, args)
    content = result.content[0] if result.content else None
    text = content.text if isinstance(content, TextContent) else ""
    elapsed = time.time() - started
    if result.is_error:
        print(f"     실패 ({elapsed:.1f}초) {' '.join(text.split())[:90]}")
        return None, elapsed
    print(f"     ({elapsed:.1f}초)")
    return json.loads(text), elapsed


async def run(region_name: str, deal_ym: str) -> int:
    """지역명 → 지역코드 → 실거래 순으로 조회한다."""
    from data_go_mcp.all_servers.server import mcp

    print(BAR)
    print(f"  {region_name} {deal_ym[:4]}년 {int(deal_ym[4:])}월 아파트 실거래")
    print(BAR)

    async with Client(mcp) as client:
        print("\n  국민연금공단 (법정동코드)")
        print("  ·· find_region_code")
        regions, _ = await call(client, "find_region_code", {"name": region_name})
        if not regions or not regions.get("items"):
            print(f"     지역을 찾지 못했습니다: {region_name}")
            return 1
        sigungu = next(
            (r for r in regions["items"] if r.get("level") == "시군구"), regions["items"][0]
        )
        code = sigungu["region_cd"]
        print(f"     {sigungu['name']} · {code[:5]}")

        print("\n  국토교통부 (매매)")
        print("  ·· search_property_trades")
        trades, _ = await call(
            client,
            "search_property_trades",
            {"region_code": code, "deal_ym": deal_ym, "num_of_rows": 1000},
        )
        if not trades:
            return 1
        live = [t for t in trades["items"] if not t["cancelled"] and t["deal_amount"]]
        cancelled = len(trades["items"]) - len(live)
        live.sort(key=lambda t: -(t["deal_amount"] or 0))
        print(f"     신고 {trades['total_count']}건 (해제 {cancelled}건 제외)")

        if live:
            prices = sorted(t["deal_amount"] for t in live)
            middle = prices[len(prices) // 2]
            print(f"     중위 거래가 {middle / 10000:,.1f}억 · 최고 {prices[-1] / 10000:,.1f}억")
            print("\n     가장 비싼 거래")
            for t in live[:5]:
                pyeong = (t["exclusive_area"] or 0) / PYEONG
                per = (t["deal_amount"] / pyeong / 10000) if pyeong else 0
                print(
                    f"     {t['deal_date']}  {(t['name'] or '')[:14]:14}"
                    f"  {t['exclusive_area']:>6}㎡  {str(t['floor']) + '층':>4}"
                    f"  {t['deal_amount'] / 10000:>6,.1f}억  평당 {per:>4,.1f}억  {t['dong']}"
                )

        print("\n  국토교통부 (전월세)")
        print("  ·· search_property_rents")
        rents, _ = await call(
            client,
            "search_property_rents",
            {"region_code": code, "deal_ym": deal_ym, "num_of_rows": 1000},
        )
        if rents and rents["items"]:
            jeonse = [r for r in rents["items"] if r["rent_type"] == "전세" and r["deposit"]]
            monthly = [r for r in rents["items"] if r["rent_type"] == "월세"]
            print(f"     신고 {rents['total_count']}건 · 전세 {len(jeonse)} · 월세 {len(monthly)}")
            if jeonse:
                deposits = sorted(r["deposit"] for r in jeonse)
                print(f"     전세 중위 보증금 {deposits[len(deposits) // 2] / 10000:,.1f}억")

    print(f"\n{BAR}")
    print("  지역명만으로 코드를 찾아 그달 실거래를 훑었습니다.")
    print(BAR)
    return 0


def main() -> int:
    """인자를 읽고 조회한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("region", nargs="?", default=DEFAULT_REGION, help="지역명 (예: 강남구)")
    parser.add_argument("deal_ym", nargs="?", default=DEFAULT_MONTH, help="계약년월 YYYYMM")
    args = parser.parse_args()

    if not os.getenv("API_KEY"):
        print("API_KEY 환경변수가 필요합니다 (.env 또는 export)", file=sys.stderr)
        return 1
    return asyncio.run(run(args.region, args.deal_ym))


if __name__ == "__main__":
    sys.exit(main())
