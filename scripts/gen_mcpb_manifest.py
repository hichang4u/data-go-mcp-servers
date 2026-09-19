"""mcpb/manifest.json 의 tools 를 통합 서버의 실제 툴로 갱신하고(--check 면 검사만), --pack 이면 번들을 만든다.

Smithery 는 stdio 번들의 툴 목록을 실행해 보지 않고 manifest 의 ``tools`` 를 MCP 서버 카드로
그대로 올린다 — ``inputSchema`` 가 없으면 "expected object, received undefined" 로 거부한다.
반면 MCPB 스키마(0.4)는 tools 항목을 ``{name, description}`` 으로 엄격히 제한해 ``mcpb pack`` 이
거부하므로, 번들은 여기서 직접 zip 한다 (manifest.json, pyproject.toml, src/server.py).
"""

import argparse
import asyncio
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = ROOT / "mcpb"
MANIFEST = BUNDLE_DIR / "manifest.json"
OUTPUT = ROOT / "dist" / "data-go-mcp.mcpb"
BUNDLE_FILES = ["manifest.json", "pyproject.toml", "src/server.py"]


async def tools() -> list[dict[str, Any]]:
    """{name, description(첫 줄), inputSchema} 를 이름순으로."""
    from data_go_mcp.all_servers.server import mcp

    return [
        {
            "name": t.name,
            "description": (t.description or "").strip().splitlines()[0],
            "inputSchema": t.input_schema,
        }
        for t in sorted(await mcp.list_tools(), key=lambda t: t.name)
    ]


def pack() -> Path:
    """mcpb/ 의 번들 파일만 zip 으로 묶는다."""
    OUTPUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in BUNDLE_FILES:
            zf.write(BUNDLE_DIR / name, name)
    return OUTPUT


def main() -> int:
    """Manifest 를 갱신하거나(--check 면 검사만) 종료 코드를 돌려준다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pack", action="store_true", help=f"{OUTPUT.relative_to(ROOT)} 생성")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fresh = asyncio.run(tools())
    if manifest.get("tools") == fresh:
        print(f"up to date: {len(fresh)} tools")
    elif args.check:
        print(f"stale: {MANIFEST.relative_to(ROOT)} (run scripts/gen_mcpb_manifest.py)")
        return 1
    else:
        manifest["tools"] = fresh
        MANIFEST.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"updated: {len(fresh)} tools")
    if args.pack:
        out = pack()
        print(f"packed: {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
