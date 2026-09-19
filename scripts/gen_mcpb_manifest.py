"""mcpb/manifest.json 의 tools 목록을 통합 서버의 실제 툴로 갱신한다 (--check 면 검사만).

Smithery 는 stdio 번들의 툴 목록을 실행해 보지 않고 manifest 의 ``tools`` 에서 읽는다.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "mcpb" / "manifest.json"


async def tools() -> list[dict[str, str]]:
    """{name, description(첫 줄)} 을 이름순으로."""
    from data_go_mcp.all_servers.server import mcp

    return [
        {"name": t.name, "description": (t.description or "").strip().splitlines()[0]}
        for t in sorted(await mcp.list_tools(), key=lambda t: t.name)
    ]


def main() -> int:
    """Manifest 를 갱신하거나(--check 면 검사만) 종료 코드를 돌려준다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fresh = asyncio.run(tools())
    if manifest.get("tools") == fresh:
        print(f"up to date: {len(fresh)} tools")
        return 0
    if args.check:
        print(f"stale: {MANIFEST.relative_to(ROOT)} (run scripts/gen_mcpb_manifest.py)")
        return 1
    manifest["tools"] = fresh
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"updated: {len(fresh)} tools")
    return 0


if __name__ == "__main__":
    sys.exit(main())
