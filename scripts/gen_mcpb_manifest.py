"""mcpb/manifest.json 의 tools 를 통합 서버의 실제 툴로 갱신하고(--check 면 검사만), --pack 이면 번들을 만든다.

Smithery 는 stdio 번들의 툴 목록을 실행해 보지 않고 manifest 의 ``tools`` 를 MCP 서버 카드로
그대로 올린다 — ``inputSchema`` 가 없으면 "expected object, received undefined" 로 거부한다.
반면 MCPB 스키마(0.4)는 tools 항목을 ``{name, description}`` 으로 엄격히 제한해 ``mcpb pack`` 과
Claude Desktop 직접 설치("확장 프로그램 미리보기 실패")가 거부한다. 그래서 번들을 둘 만든다:

- ``dist/data-go-mcp.mcpb`` — Smithery 용 (inputSchema 포함)
- ``dist/data-go-mcp-desktop.mcpb`` — Claude Desktop 드래그 설치용 (``type: uv``, tools 는 name/description 만)
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
OUTPUT_DESKTOP = ROOT / "dist" / "data-go-mcp-desktop.mcpb"
BUNDLE_FILES = ["pyproject.toml", "src/server.py"]


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


def desktop_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Claude Desktop 용 — tools 에서 inputSchema 를 빼고 server.type 은 uv.

    ``type: uv`` 면 호스트가 자체 uv 로 의존성을 설치·실행한다. ``python`` 이면 ``mcp_config`` 의
    ``uv`` 를 PATH 에서 찾아 ``spawn uv ENOENT`` 가 난다 (2026-09-20 확인). Smithery CLI 는
    반대로 ``uv`` 타입을 모르므로 그쪽은 ``python`` 으로 둔다.
    """
    return {
        **manifest,
        "server": {**manifest["server"], "type": "uv"},
        "tools": [{"name": t["name"], "description": t["description"]} for t in manifest["tools"]],
    }


def pack(manifest: dict[str, Any]) -> list[Path]:
    """mcpb/ 의 번들 파일과 manifest 를 zip 으로 묶는다 (Smithery 용, Claude Desktop 용)."""
    OUTPUT.parent.mkdir(exist_ok=True)
    outputs: list[Path] = []
    for path, m in ((OUTPUT, manifest), (OUTPUT_DESKTOP, desktop_manifest(manifest))):
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(m, ensure_ascii=False, indent=2) + "\n")
            for name in BUNDLE_FILES:
                zf.write(BUNDLE_DIR / name, name)
        outputs.append(path)
    return outputs


def main() -> int:
    """Manifest 를 갱신하거나(--check 면 검사만) 종료 코드를 돌려준다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pack", action="store_true", help="dist/ 에 번들 두 개 생성")
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
        for out in pack(manifest):
            print(f"packed: {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
