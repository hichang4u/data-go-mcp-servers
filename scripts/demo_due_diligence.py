"""사업자등록번호 하나로 여러 기관을 가로지르는 조회를 실제로 실행해 보여준다.

단일 API 를 감싼 MCP 서버로는 할 수 없는 것을 보이기 위한 데모다. 화면에 나오는 값은
모두 **실제 호출 결과**이며, 호출하는 시점의 공개 데이터에 따라 달라진다.

사용법:
    uv run python scripts/demo_due_diligence.py [사업자등록번호]
    uv run python scripts/demo_due_diligence.py 214-87-12538 --json

기본 대상은 공개 낙찰 이력이 있는 업체(214-87-12538)다. 국세청·공정위·금융위·근로복지공단·
조달청은 `API_KEY` 하나로 돌고,
고용24·DART 단계는 각각 `WORK24_API_KEY`, `DART_DISCLOSURE_API_KEY` 가 있을 때만 돈다.
"""

import argparse
import asyncio
import datetime as dt
import json
import logging
import os
import re
import sys
import time
from typing import Any, Optional

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

DEFAULT_BUSINESS_NUMBER = "214-87-12538"


def _now() -> dt.datetime:
    """현재 시각."""
    return dt.datetime.now()


BAR = "─" * 72


def _fmt_won(value: Any) -> str:
    """원 단위 정수를 읽기 쉬운 한국어 금액으로."""
    try:
        amount = int(value)
    except (TypeError, ValueError):
        return str(value)
    if amount >= 10**12:
        return f"{amount / 10**12:,.1f}조원"
    if amount >= 10**8:
        return f"{amount / 10**8:,.0f}억원"
    if amount >= 10**4:
        return f"{amount / 10**4:,.0f}만원"
    return f"{amount:,}원"


class Demo:
    """툴 호출과 출력을 한 군데서 처리한다."""

    def __init__(self, client: Client, as_json: bool) -> None:
        self.client = client
        self.as_json = as_json
        self.record: dict[str, Any] = {}
        self.queried: list[str] = []

    def say(self, text: str = "") -> None:
        """JSON 모드가 아니면 화면에 쓴다."""
        if not self.as_json:
            print(text)

    def step(self, agency: str, tool: str) -> None:
        """단계 머리말. 어떤 기관을 지났는지 모아 둔다."""
        self.queried.append(agency)
        self.say(f"\n  {agency}")
        self.say(f"  {'·' * 2} {tool}")

    async def call(self, tool: str, args: dict[str, Any]) -> Optional[dict[str, Any]]:
        """툴 하나를 부르고 소요 시간을 표시한다. 실패는 None."""
        started = time.time()
        result = await self.client.call_tool(tool, args)
        content = result.content[0] if result.content else None
        text = content.text if isinstance(content, TextContent) else ""
        elapsed = time.time() - started
        if result.is_error:
            self.say(f"     실패 ({elapsed:.1f}초) {' '.join(text.split())[:90]}")
            return None
        self.say(f"     ({elapsed:.1f}초)")
        try:
            return json.loads(text)
        except ValueError:
            return {"text": text}


async def run(business_number: str, as_json: bool, months: int) -> int:
    """기관을 차례로 조회한다."""
    from data_go_mcp.all_servers.server import mcp

    digits = re.sub(r"\D", "", business_number)
    if len(digits) != 10:
        print(f"사업자등록번호는 숫자 10자리여야 합니다: {business_number!r}", file=sys.stderr)
        return 1

    async with Client(mcp) as client:
        demo = Demo(client, as_json)
        demo.say(BAR)
        demo.say(f"  사업자등록번호 {business_number} 거래처 실사")
        demo.say(BAR)

        # 1. 국세청 — 살아 있는 사업자인가
        demo.step("국세청", "check_business_status")
        status = await demo.call("check_business_status", {"business_numbers": digits})
        if status:
            first = (status.get("businesses") or status.get("items") or [{}])[0]
            demo.record["status"] = first
            demo.say(f"     {first.get('status', '?')} · {first.get('tax_type', '')}")

        # 2. 공정거래위원회 — 온라인으로 파는가, 그리고 법인번호는 무엇인가
        demo.step("공정거래위원회", "get_online_seller")
        seller_crno = None
        seller = await demo.call("get_online_seller", {"business_number": digits})
        if seller is not None:
            rows = seller.get("items") or []
            demo.record["seller"] = rows
            if rows:
                row = rows[0]
                seller_crno = row.get("corporate_number")
                demo.say(
                    f"     {row.get('name', '')} · {row.get('operating_status', '')}"
                    f" · 신고 {row.get('report_number', '')} ({row.get('reported_on', '')})"
                    + (f" · {row.get('product_type')}" if row.get("product_type") else "")
                )
                for domain in (row.get("domains") or [])[:2]:
                    demo.say(f"     {domain}")
            else:
                demo.say("     통신판매업 신고 없음 (온라인 판매를 하지 않는다)")

        # 3. 금융위 — 사업자번호를 법인번호로 바꿔 재무를 본다
        demo.step("금융위원회", "find_corp_number → get_summary_financial_statement")
        corp = await demo.call("find_corp_number", {"bzno": digits})
        crno = None
        if corp and corp.get("items"):
            found = corp["items"][0]
            crno = found.get("crno")
            demo.record["corp"] = found
            demo.say(f"     {found.get('corp_nm', '')} · 법인번호 {crno}")
        elif seller_crno:  # 금융위에 없으면 공정위가 준 법인번호로 이어 간다
            crno = seller_crno
            demo.say(f"     금융위 기업기본정보에 없음 — 공정위의 법인번호 {crno} 로 계속")
        if crno:
            fin = await demo.call(
                "get_summary_financial_statement",
                {"crno": crno, "biz_year": "2024", "num_of_rows": 1},
            )
            if fin:
                demo.record["financial"] = fin
                body = fin.get("text", "")
                sales = re.search(r"매출액[^\d\-]*(-?[\d,]+)", body)
                if sales:
                    demo.say(f"     2024 매출액 {_fmt_won(sales.group(1).replace(',', ''))}")
                elif "없습니다" in body:
                    demo.say("     금융위 재무정보에 없음 (공시대상 법인만 실린다)")

        # 4. 근로복지공단 — 사람을 얼마나 쓰는가
        demo.step("근로복지공단", "get_insurance_status")
        insurance = await demo.call("get_insurance_status", {"bzno": digits, "num_of_rows": 3})
        if insurance and insurance.get("items"):
            demo.record["insurance"] = insurance["items"]
            for site in insurance["items"][:2]:
                name = site.get("workplace_nm") or site.get("addr") or ""
                count = site.get("employee_cnt")
                industry = site.get("industry_nm") or ""
                line = f"     {site.get('insurance', '')}보험 · {name[:24]}"
                if count:
                    line += f" · {count}명"
                if industry:
                    line += f" · {industry[:22]}"
                demo.say(line)

        # 5. 조달청 — 등록·제재는 번호로 바로, 낙찰은 기간을 훑어야 한다
        bid_args: dict[str, Any] = {"business_number": digits}
        if months > 1:
            start = (_now() - dt.timedelta(days=30 * months)).strftime("%Y-%m-%d")
            bid_args |= {"start_date": start, "end_date": _now().strftime("%Y-%m-%d")}
        demo.step(
            "조달청",
            f"get_procurement_company → check_procurement_sanctions → "
            f"find_bid_winners (최근 {months}개월 훑기 — 수십 초 걸린다)",
        )
        vendor = await demo.call("get_procurement_company", {"business_number": digits})
        if vendor is not None:
            demo.record["vendor"] = vendor
            if vendor.get("registered"):
                company = vendor.get("company") or {}
                line = f"     조달 등록 · {company.get('name', '')}"
                if company.get("employees"):
                    line += f" · 직원 {company['employees']}명"
                if company.get("opened_on"):
                    line += f" · 개업 {company['opened_on']}"
                demo.say(line)
                trades = [
                    i.get("name") for i in (vendor.get("industries") or [])[:3] if i.get("name")
                ]
                if trades:
                    demo.say(f"     업종 {vendor.get('industry_count')}건 — {', '.join(trades)}")
                goods = [
                    p.get("name") for p in (vendor.get("products") or [])[:3] if p.get("name")
                ]
                if goods:
                    demo.say(f"     공급물품 {vendor.get('product_count')}건 — {', '.join(goods)}")
            else:
                demo.say("     조달시장 등록 없음")

        sanctions = await demo.call("check_procurement_sanctions", {"business_number": digits})
        if sanctions is not None:
            demo.record["sanctions"] = sanctions
            if sanctions.get("total_count"):
                state = "현재 제한 중" if sanctions.get("restricted_now") else "기간 만료"
                demo.say(f"     부정당업자 제재 {sanctions['total_count']}건 · {state}")
                for hit in (sanctions.get("items") or [])[:2]:
                    demo.say(
                        f"     {hit.get('begins_on', '')}~{hit.get('ends_on', '')}"
                        f" · {hit.get('institution', '')} · {(hit.get('short_reason') or '')[:30]}"
                    )
            else:
                demo.say("     부정당업자 제재 없음")

        winners = await demo.call("find_bid_winners", bid_args)
        if winners:
            demo.record["bids"] = winners
            demo.say(f"     {winners.get('message', '')}")
            for bid in (winners.get("items") or [])[:3]:
                demo.say(
                    f"     {bid.get('opening_date', '')} · {(bid.get('bid_notice_name') or '')[:32]}"
                    f" · {_fmt_won(bid.get('winning_amount'))} · {bid.get('demand_institution', '')}"
                )

        # 6. 고용24 — 사업자번호로 채용 공고가 바로 필터된다 (키가 있을 때만)
        if os.getenv("WORK24_API_KEY"):
            demo.step("고용24", "search_job_postings")
            jobs = await demo.call(
                "search_job_postings", {"business_number": digits, "num_of_rows": 3}
            )
            if jobs is not None:
                demo.record["jobs"] = jobs
                count = jobs.get("total_count", 0)
                demo.say(f"     진행 중인 공고 {count}건")
                for job in (jobs.get("items") or [])[:2]:
                    pay = job.get("min_salary")
                    demo.say(
                        f"     {job.get('posted_date', '')} · {(job.get('title') or '')[:30]}"
                        + (f" · {pay / 10000:,.0f}만원" if pay else "")
                    )
                if not count:
                    demo.say("     채용 중인 자리 없음")

        # 7. DART — 키가 있을 때만
        if os.getenv("DART_DISCLOSURE_API_KEY"):
            name = (demo.record.get("corp") or {}).get("corp_nm", "")
            if name:
                demo.step("금융감독원 DART", "find_corp_code → list_disclosures")
                code = await demo.call("find_corp_code", {"query": name.replace("(주)", "")})
                items = (code or {}).get("items") or []
                if items:
                    corp_code = items[0].get("corp_code")
                    demo.say(f"     {items[0].get('corp_name')} · 고유번호 {corp_code}")
                    filings = await demo.call(
                        "list_disclosures", {"corp_code": corp_code, "page_count": 3}
                    )
                    rows = (filings or {}).get("items") or []
                    demo.record["filings"] = rows
                    for filing in rows[:2]:
                        demo.say(
                            f"     {filing.get('rcept_dt', '')} · {(filing.get('report_nm') or '')[:40]}"
                        )
                    if not rows:
                        demo.say("     최근 공시 없음 (비상장·공시의무 없음)")

        demo.say(f"\n{BAR}")
        agencies = " · ".join(demo.queried)
        demo.say(f"  {agencies} — {len(demo.queried)}개 기관을 한 번에 조회했습니다.")
        demo.say(BAR)

        if as_json:
            print(json.dumps(demo.record, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    """인자를 읽고 데모를 실행한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("business_number", nargs="?", default=DEFAULT_BUSINESS_NUMBER)
    parser.add_argument("--json", action="store_true", help="사람용 출력 대신 원자료를 JSON 으로")
    parser.add_argument(
        "--months", type=int, default=3, help="낙찰 이력을 훑을 개월 수 (기본 3, 최대 3)"
    )
    args = parser.parse_args()

    if not os.getenv("API_KEY"):
        print("API_KEY 환경변수가 필요합니다 (.env 또는 export)", file=sys.stderr)
        return 1
    return asyncio.run(run(args.business_number, args.json, max(1, min(args.months, 3))))


if __name__ == "__main__":
    sys.exit(main())
