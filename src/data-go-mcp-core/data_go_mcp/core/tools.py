"""MCP 툴 공통: 예외 → ToolError 변환, 조회 전용 annotation."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from .errors import DataGoAPIError


# 이 프로젝트의 툴은 전부 외부 공공 API 조회다.
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=True)


@asynccontextmanager
async def tool_errors() -> AsyncIterator[None]:
    """툴 본문을 감싸 실패를 ``ToolError`` 로 바꾼다 → 클라이언트에 ``isError=True`` 로 전달."""
    try:
        yield
    except ToolError:
        raise
    except DataGoAPIError as e:
        raise ToolError(f"{e.source} 오류 {e}") from e
    except httpx.HTTPStatusError as e:
        body = e.response.text[:200]
        raise ToolError(f"HTTP {e.response.status_code}: {body}") from e
    except httpx.HTTPError as e:
        raise ToolError(f"네트워크 오류: {e}") from e
    except ValueError as e:
        raise ToolError(f"입력값 오류: {e}") from e
