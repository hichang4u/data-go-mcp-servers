"""OpenDART corpCode.xml 을 받아 dart-disclosure 의 기업코드 스냅샷을 다시 만든다.

사용법:
    DART_DISCLOSURE_API_KEY=... uv run python scripts/harvest_dart_corp_codes.py

출력: src/dart-disclosure/data_go_mcp/dart_disclosure/corp_codes.json.gz (약 1.5MB).
신규 등록·개명·상장을 반영하려면 릴리스 전에 한 번 돌린다.
"""

import asyncio
import datetime as dt
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from data_go_mcp.dart_disclosure.api_client import DartDisclosureAPIClient
from data_go_mcp.dart_disclosure.corp_codes import SNAPSHOT_FILE, dump_snapshot


load_dotenv()

TARGET = (
    Path(__file__).resolve().parents[1]
    / "src/dart-disclosure/data_go_mcp/dart_disclosure"
    / SNAPSHOT_FILE
)


async def main() -> int:
    """corpCode.xml 을 받아 스냅샷 파일을 쓴다."""
    async with DartDisclosureAPIClient(timeout=180) as client:
        entries = await client.download_corp_codes()
    today = dt.date.today().strftime("%Y%m%d")
    TARGET.write_bytes(dump_snapshot(entries, today))
    listed = sum(1 for e in entries if e["stock_code"])
    print(
        f"{os.path.relpath(TARGET)}: {len(entries)} companies ({listed} listed), "
        f"{TARGET.stat().st_size // 1024} KB, generated {today}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
