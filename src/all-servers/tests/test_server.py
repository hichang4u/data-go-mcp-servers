"""통합 서버 — 개별 서버의 툴이 빠짐없이, 겹침 없이 한 프로세스에 실린다."""

import os
import re
from pathlib import Path

import httpx
import pytest
import respx
from mcp import Client
from mcp.server.mcpserver import MCPServer
from mcp.types import TextContent

from data_go_mcp.all_servers.server import build, discover, mcp, missing_key_messages


SRC = Path(__file__).resolve().parents[2]
NOT_SERVERS = {"data-go-mcp-core", "all-servers"}


def _server_dirs() -> set[str]:
    return {p.name for p in SRC.iterdir() if p.is_dir() and p.name not in NOT_SERVERS}


async def test_discovers_every_server_package():
    """src/ 의 서버 디렉터리와 자동 탐색 결과가 일치한다."""
    expected = {d.replace("-", "_") for d in _server_dirs()}
    found = {m.__name__.split(".")[1] for m in discover()}
    assert found == expected


async def test_discovery_skips_namespace_packages_that_are_not_servers(monkeypatch, tmp_path):
    """같은 data_go_mcp 네임스페이스에 서버가 아닌 패키지가 있어도 import 시점에 죽지 않는다."""
    import data_go_mcp

    extra = tmp_path / "data_go_mcp"
    (extra / "no_server_here").mkdir(parents=True)
    (extra / "no_server_here" / "__init__.py").write_text("")
    (extra / "wrong_server").mkdir()
    (extra / "wrong_server" / "__init__.py").write_text("")
    (extra / "wrong_server" / "server.py").write_text("mcp = None")
    monkeypatch.setattr(data_go_mcp, "__path__", [*data_go_mcp.__path__, str(extra)])

    found = {m.__name__.split(".")[1] for m in discover()}
    assert "no_server_here" not in found and "wrong_server" not in found
    assert "nts_business_verification" in found


async def test_every_server_package_is_a_dependency():
    """uvx 는 선언된 의존성만 설치한다 — 서버를 추가하면 pyproject 에도 넣어야 한다."""
    text = (SRC / "all-servers" / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"^dependencies = \[(.*?)^\]", text, re.S | re.M)
    assert block
    deps = set(re.findall(r'"data-go-mcp\.([a-z0-9-]+)"', block.group(1)))
    assert deps == _server_dirs()


async def test_exposes_union_of_all_server_tools():
    names = [t.name for t in await mcp.list_tools()]
    expected: list[str] = []
    for mod in discover():
        expected += [t.name for t in await mod.mcp.list_tools()]
    assert sorted(names) == sorted(expected)
    assert len(names) == len(set(names))
    assert len(names) >= 36


async def test_tools_keep_annotations_and_descriptions():
    for tool in await mcp.list_tools():
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


async def test_duplicate_tool_name_is_rejected():
    a, b = MCPServer("a"), MCPServer("b")

    @a.tool(name="ping")
    def ping_a() -> str:
        """A."""
        return "a"

    @b.tool(name="ping")
    def ping_b() -> str:
        """B."""
        return "b"

    with pytest.raises(ValueError, match="ping"):
        build([a, b])


@respx.mock
async def test_call_routes_to_origin_server(monkeypatch):
    """nts 의 툴을 통합 서버로 호출하면 nts 클라이언트가 실제 요청을 보낸다."""
    route = respx.post("https://api.odcloud.kr/api/nts-businessman/v1/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "request_cnt": 1,
                "match_cnt": 1,
                "status_code": "OK",
                "data": [{"b_no": "1208800767", "b_stt": "계속사업자", "b_stt_cd": "01"}],
            },
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_business_status", {"business_numbers": "120-88-00767"}
        )
    assert not result.is_error
    (content,) = result.content
    assert isinstance(content, TextContent) and "계속사업자" in content.text
    assert route.called


def test_missing_key_messages_cover_both_key_families(monkeypatch):
    # 루트 conftest 가 .env 를 읽는다 — 서버별 <PREFIX>_API_KEY 까지 전부 지운다
    for name in list(os.environ):
        if name.endswith("API_KEY"):
            monkeypatch.delenv(name)
    messages = missing_key_messages()
    assert any("API_KEY" in m and "data.go.kr" in m for m in messages)
    assert any("DART_DISCLOSURE_API_KEY" in m for m in messages)
    # data.go.kr 서버 6개가 공통 키 하나로 뭉쳐 경고가 두 종류만 나온다
    assert len(messages) == 2


def test_no_messages_when_keys_present():
    assert missing_key_messages() == []


async def test_mcpb_manifest_lists_every_tool():
    """Smithery 페이지는 manifest 의 tools 만 보여준다 — 서버 툴과 이름·설명이 어긋나면 실패."""
    import json

    manifest = json.loads((SRC.parent / "mcpb" / "manifest.json").read_text(encoding="utf-8"))
    listed = {t["name"]: t["description"] for t in manifest["tools"]}
    expected = {
        t.name: (t.description or "").strip().splitlines()[0] for t in await mcp.list_tools()
    }
    assert listed == expected
    assert manifest["server"]["type"] == "python"  # smithery CLI 1.2.0 은 "uv" 를 모른다
