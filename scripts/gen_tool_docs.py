"""서버의 list_tools() 스키마에서 툴 레퍼런스 마크다운을 생성한다.

사용법:
    uv run python scripts/gen_tool_docs.py            # docs/guide/servers/*.md 의 마커 사이를 갱신
    uv run python scripts/gen_tool_docs.py --check    # 갱신이 필요하면 exit 1 (CI 용)

각 서버 문서의 ``<!-- tools:start -->`` 와 ``<!-- tools:end -->`` 사이만 다시 쓴다.
"""

import argparse
import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "guide" / "servers"
START, END = "<!-- tools:start -->", "<!-- tools:end -->"

SERVERS = {
    "nps-business-enrollment": "nps_business_enrollment",
    "nts-business-verification": "nts_business_verification",
    "pps-narajangteo": "pps_narajangteo",
    "fsc-financial-info": "fsc_financial_info",
    "presidential-speeches": "presidential_speeches",
    "msds-chemical-info": "msds_chemical_info",
}


def _type_name(prop: dict[str, Any]) -> str:
    if "type" in prop:
        return str(prop["type"])
    if "anyOf" in prop:
        names = [str(p.get("type", "?")) for p in prop["anyOf"] if p.get("type") != "null"]
        return " | ".join(names) + " (optional)"
    return "?"


def render(tools: list[Any]) -> str:
    """툴 목록을 마크다운 섹션으로."""
    lines: list[str] = []
    for tool in sorted(tools, key=lambda t: t.name):
        schema = tool.input_schema
        required = set(schema.get("required") or [])
        lines.append(f"### `{tool.name}`\n")
        lines.append((tool.description or "").strip() + "\n")
        props = schema.get("properties") or {}
        if props:
            lines.append("| 파라미터 | 타입 | 필수 | 기본값 | 설명 |")
            lines.append("|---|---|---|---|---|")
            for name, prop in props.items():
                default = prop.get("default", "")
                default_s = "" if default in ("", None) else f"`{default}`"
                desc = str(prop.get("description", "")).replace("\n", "<br>").replace("|", "\\|")
                lines.append(
                    f"| `{name}` | {_type_name(prop)} | {'예' if name in required else ''} | {default_s} | {desc} |"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


async def collect() -> dict[str, str]:
    """서버별 렌더 결과 {slug: markdown}."""
    out: dict[str, str] = {}
    for slug, module in SERVERS.items():
        mod = importlib.import_module(f"data_go_mcp.{module}.server")
        out[slug] = render(await mod.mcp.list_tools())
    return out


def main() -> int:
    """마커 사이를 갱신하거나(--check 면 검사만) 종료 코드를 돌려준다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = asyncio.run(collect())
    stale: list[str] = []
    for slug, body in rendered.items():
        path = DOCS / f"{slug}.md"
        if not path.exists():
            print(f"missing doc: {path.relative_to(ROOT)}")
            stale.append(slug)
            continue
        text = path.read_text(encoding="utf-8")
        if START not in text or END not in text:
            print(f"missing markers in {path.relative_to(ROOT)}: {START} … {END}")
            stale.append(slug)
            continue
        head, rest = text.split(START, 1)
        _, tail = rest.split(END, 1)
        new = f"{head}{START}\n\n{body}\n{END}{tail}"
        if new != text:
            stale.append(slug)
            if not args.check:
                path.write_text(new, encoding="utf-8", newline="\n")
                print(f"updated: {path.relative_to(ROOT)}")
    if args.check and stale:
        print("tool docs out of date or missing:", ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
