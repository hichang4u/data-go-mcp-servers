"""사업자등록번호 하나로 그 회사의 채용 현황과 규모를 조회한다.

고용24는 **사업자번호로 공고가 바로 필터**되므로 기간을 훑지 않아도 된다. 공고 상세에는
종업원 수·자본금·연 매출액이 들어 있어, 금융위 재무정보에 없는 비상장사의 규모를 알 수 있다.

사용법:
    uv run python scripts/demo_jobs.py [사업자등록번호]
    uv run python scripts/demo_jobs.py 503-81-69211

`WORK24_API_KEY` 가 필요하다 (https://www.work24.go.kr 오픈API → 채용정보 신청).
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

# httpx 는 INFO 로 요청 URL 을 남기는데 거기에 인증키가 들어 있다. 이 스크립트의 출력은
# 캡처해 공유하라고 만든 것이므로 키가 화면에 찍히지 않도록 반드시 올린다.
logging.getLogger().setLevel(logging.WARNING)
for _noisy in ("httpx", "httpcore", "mcp"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

DEFAULT_BUSINESS_NUMBER = "503-81-69211"
BAR = "─" * 78


def _man(value: object) -> str:
    """원 단위 임금을 만원으로."""
    try:
        amount = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "-"
    return f"{amount / 10000:,.0f}만원"


async def call(client: Client, tool: str, args: dict) -> dict | None:
    """툴 하나를 부르고 소요 시간을 찍는다."""
    started = time.time()
    result = await client.call_tool(tool, args)
    content = result.content[0] if result.content else None
    text = content.text if isinstance(content, TextContent) else ""
    elapsed = time.time() - started
    if result.is_error:
        print(f"     실패 ({elapsed:.1f}초) {' '.join(text.split())[:90]}")
        return None
    print(f"     ({elapsed:.1f}초)")
    return json.loads(text)


async def run(business_number: str) -> int:
    """공고 목록 → 첫 공고 상세 순으로 조회한다."""
    from data_go_mcp.work24_jobs.server import mcp

    digits = re.sub(r"\D", "", business_number)
    print(BAR)
    print(f"  사업자번호 {business_number} 채용 현황")
    print(BAR)

    async with Client(mcp) as client:
        print("\n  고용24 (채용공고)")
        print("  ·· search_job_postings")
        listing = await call(
            client, "search_job_postings", {"business_number": digits, "num_of_rows": 5}
        )
        if not listing:
            return 1
        items = listing["items"]
        print(f"     진행 중인 공고 {listing['total_count']}건")
        if not items:
            print("\n     채용 중인 자리가 없습니다.")
            print(f"\n{BAR}")
            return 0
        print()
        for job in items:
            salary = _man(job["min_salary"]) + ("↑" if not job["max_salary"] else "")
            print(
                f"     {job['posted_date']}  {(job['title'] or '')[:30]:30}"
                f"  {salary:>10}  {job['region']}  {job['career'] or ''}"
            )

        print("\n  고용24 (공고 상세)")
        print("  ·· get_job_posting")
        detail = await call(
            client,
            "get_job_posting",
            {
                "wanted_auth_no": items[0]["wanted_auth_no"],
                "info_service": items[0]["info_service"] or "VALIDATION",
            },
        )
        if detail:
            company, posting = detail["company"], detail["posting"]
            print(f"     {company['name']} · 대표 {company['ceo_name']} · {company['size']}")
            print(
                f"     종업원 {company['employee_count']} · 자본금 {company['capital']}"
                f" · 연매출 {company['annual_sales']}"
            )
            print(f"     업종 {company['industry']} · {company['business_content']}")
            print(f"     직종 {posting['job_name']} · 모집 {posting['hiring_count']}명")
            print(
                f"     학력 {posting['education']} · {posting['career']}"
            )  # 값에 '경력'이 들어 있다
            if posting["certificate"]:
                print(f"     자격 {posting['certificate'][:48]}")

    print(f"\n{BAR}")
    print("  사업자번호 하나로 채용 중인 자리와 회사 규모를 확인했습니다.")
    print(BAR)
    return 0


def main() -> int:
    """인자를 읽고 조회한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("business_number", nargs="?", default=DEFAULT_BUSINESS_NUMBER)
    args = parser.parse_args()

    if not os.getenv("WORK24_API_KEY"):
        print("WORK24_API_KEY 환경변수가 필요합니다 (.env 또는 export)", file=sys.stderr)
        return 1
    return asyncio.run(run(args.business_number))


if __name__ == "__main__":
    sys.exit(main())
