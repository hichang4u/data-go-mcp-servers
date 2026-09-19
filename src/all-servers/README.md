# data-go-mcp.all-servers

저장소의 모든 서버(data.go.kr 6종 + OpenDART)의 툴을 **한 프로세스**로 내놓는 통합 서버. Smithery 등 "리스팅 하나 = 서버 하나" 인 레지스트리에 올리기 위한 것이다. 개별 서버를 골라 쓰려면 [installation.md](../../docs/guide/installation.md) 의 서버별 명령을 쓴다.

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/all-servers" data-go-mcp.all-servers
```

환경변수: `API_KEY` (data.go.kr 6종 공통), `DART_DISCLOSURE_API_KEY` (OpenDART, 선택). 키가 없는 쪽의 툴만 실패한다.

서버 목록은 `data_go_mcp` 네임스페이스에서 자동 탐색한다. 새 서버를 추가하면 `pyproject.toml` 의존성에만 넣으면 된다 (`tests/test_server.py` 가 누락을 잡는다).
