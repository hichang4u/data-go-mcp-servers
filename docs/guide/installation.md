# 설치와 클라이언트 설정

서버는 PyPI 가 아니라 **이 저장소에서 직접** 설치한다. `uvx`(uv 에 포함)가 git 저장소를 받아 필요한 패키지를 격리 환경에 설치하고 실행한다. 처음 한 번만 빌드하고 이후는 캐시를 쓴다.

## 준비물

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — `uvx` 명령이 여기서 나온다
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- data.go.kr 인증키 → [api-keys.md](api-keys.md)

## 실행 명령

서버 하나는 다음 한 줄로 실행된다 (`<server>` 는 디렉터리명):

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/<server>" data-go-mcp.<server>
```

| `<server>` | 내용 |
|---|---|
| `nps-business-enrollment` | 국민연금 사업장 가입내역 |
| `nts-business-verification` | 국세청 사업자등록 진위확인·상태 |
| `pps-narajangteo` | 나라장터 입찰·낙찰·계약 |
| `fsc-financial-info` | 금융위원회 기업 재무정보 |
| `presidential-speeches` | 대통령기록관 연설문 |
| `msds-chemical-info` | 안전보건공단 MSDS |

특정 커밋/태그에 고정하려면 `data-go-mcp-servers@v0.3.0#subdirectory=…` 처럼 `@` 뒤에 붙인다.

## Claude Desktop

설정 파일:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "nts-business-verification": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification",
        "data-go-mcp.nts-business-verification"
      ],
      "env": { "API_KEY": "<data.go.kr 인증키>" }
    }
  }
}
```

여러 서버를 쓰면 항목을 나란히 추가한다. 키는 하나로 전부 쓸 수 있다. 저장 후 Claude Desktop 을 완전히 종료하고 다시 연다.

Windows 에서 `uvx` 를 못 찾으면 `"command"` 에 전체 경로(`C:\Users\<you>\.local\bin\uvx.exe`)를 쓴다.

## Claude Code

```
claude mcp add nts-business-verification -e API_KEY=<인증키> -- uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification" data-go-mcp.nts-business-verification
```

또는 프로젝트의 `.mcp.json`:

```json
{
  "mcpServers": {
    "nts-business-verification": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification", "data-go-mcp.nts-business-verification"],
      "env": { "API_KEY": "${API_KEY}" }
    }
  }
}
```

## Cline / Cursor / 기타 MCP 클라이언트

stdio 서버를 등록하는 곳에 같은 `command`/`args`/`env` 를 넣으면 된다.

## 저장소를 clone 해서 쓰는 경우

```bash
git clone https://github.com/hichang4u/data-go-mcp-servers
cd data-go-mcp-servers
uv sync --all-packages
uv run python -m data_go_mcp.nts_business_verification.server
```

클라이언트 설정에는 `"command": "uv"`, `"args": ["--directory", "<clone 경로>", "run", "python", "-m", "data_go_mcp.nts_business_verification.server"]` 를 쓴다.

## 동작 확인

MCP Inspector 로 툴 목록과 호출을 눈으로 확인할 수 있다:

```
npx @modelcontextprotocol/inspector uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification" data-go-mcp.nts-business-verification
```

키를 안 넣으면 서버는 뜨지만 툴 호출이 "API key is required …" 오류로 실패한다.
