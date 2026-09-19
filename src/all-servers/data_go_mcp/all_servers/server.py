"""모든 서버의 툴을 한 프로세스로 합친 통합 MCP 서버.

Smithery 같은 "리스팅 하나 = 프로세스 하나" 인 레지스트리용. 서버 목록은
``data_go_mcp`` 네임스페이스에서 자동 탐색하므로 새 서버는 ``pyproject.toml``
의존성에만 추가하면 된다.
"""

import importlib
import pkgutil
from collections.abc import Iterable
from types import ModuleType

from mcp.server.mcpserver import MCPServer

import data_go_mcp
from data_go_mcp.core import BaseDataGoClient, configure_logging, load_api_key


NOT_SERVERS = {"core", "all_servers"}

INSTRUCTIONS = (
    "한국 공공데이터 통합 서버. 국세청 사업자등록 진위·상태, 국민연금 사업장 가입내역, "
    "나라장터 입찰·낙찰·계약, 금융위원회 기업 재무·주식시세, 대통령기록관 연설문, "
    "안전보건공단 MSDS, 금융감독원 DART 전자공시를 한 곳에서 조회한다."
)


def discover() -> list[ModuleType]:
    """``data_go_mcp.<server>.server`` 모듈을 이름순으로 찾아 돌려준다."""
    modules: list[ModuleType] = []
    for info in sorted(pkgutil.iter_modules(data_go_mcp.__path__), key=lambda i: i.name):
        if info.name in NOT_SERVERS:
            continue
        modules.append(importlib.import_module(f"data_go_mcp.{info.name}.server"))
    return modules


def build(servers: Iterable[MCPServer], name: str = "Korea Public Data") -> MCPServer:
    """여러 ``MCPServer`` 의 툴을 새 서버 하나에 옮겨 담는다. 이름이 겹치면 ``ValueError``."""
    merged = MCPServer(name, instructions=INSTRUCTIONS)
    target = merged._tool_manager._tools
    for server in servers:
        for tool_name, tool in server._tool_manager._tools.items():
            if tool_name in target:
                raise ValueError(f"duplicate tool name across servers: {tool_name}")
            target[tool_name] = tool
    return merged


def _client_classes(server_module: ModuleType) -> list[type[BaseDataGoClient]]:
    package = server_module.__name__.rsplit(".", 1)[0]
    api_client = importlib.import_module(f"{package}.api_client")
    return [
        obj
        for obj in vars(api_client).values()
        if isinstance(obj, type)
        and issubclass(obj, BaseDataGoClient)
        and obj is not BaseDataGoClient
        and obj.key_env_prefix
    ]


def missing_key_messages() -> list[str]:
    """키가 없는 서버를 경고 문장으로. 공통 ``API_KEY`` 를 쓰는 서버들은 한 문장으로 묶는다."""
    shared_missing: list[str] = []
    shared_url = ""
    messages: list[str] = []
    seen: set[str] = set()
    for module in discover():
        for cls in _client_classes(module):
            if cls.key_env_prefix in seen:
                continue
            seen.add(cls.key_env_prefix)
            try:
                load_api_key(cls.key_env_prefix, shared=cls.shared_key, key_url=cls.key_url)
            except ValueError:
                if cls.shared_key:
                    shared_missing.append(cls.key_env_prefix)
                    shared_url = cls.key_url
                else:
                    messages.append(
                        f"{cls.key_env_prefix}_API_KEY is not set — its tools will fail. "
                        f"Get a key from {cls.key_url}"
                    )
    if shared_missing:
        messages.insert(
            0,
            f"API_KEY is not set — data.go.kr tools will fail ({', '.join(shared_missing)}). "
            f"Get a key from {shared_url}",
        )
    return messages


mcp = build(m.mcp for m in discover())


def main() -> None:
    """Run the merged MCP server over stdio."""
    logger = configure_logging(__name__)
    for message in missing_key_messages():
        logger.warning(message)
    mcp.run()


if __name__ == "__main__":
    main()
