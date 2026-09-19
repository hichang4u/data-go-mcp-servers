# 설치와 클라이언트 설정

서버는 PyPI 가 아니라 **이 저장소에서 직접** 설치한다. `uvx`(uv 에 포함)가 git 저장소를 받아 필요한 패키지를 격리 환경에 설치하고 실행한다. 처음 한 번만 빌드하고 이후는 캐시를 쓴다.

## 준비물

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — `uvx` 명령이 여기서 나온다
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- data.go.kr 인증키 → [api-keys.md](api-keys.md). `dart-disclosure` 는 OpenDART 인증키가 따로 필요하다

## 실행 명령

서버 하나는 다음 한 줄로 실행된다 (`<server>` 는 디렉터리명):

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/<server>" data-go-mcp.<server>
```

| `<server>` | 내용 |
|---|---|
| `nps-business-enrollment` | 국민연금 사업장 가입내역, 법정동코드, 고용·산재보험 현황 |
| `nts-business-verification` | 국세청 사업자등록 진위확인·상태 |
| `pps-narajangteo` | 나라장터 입찰·낙찰·계약 |
| `fsc-financial-info` | 금융위원회 기업 재무정보, 법인번호·기업 개요, 주식시세 |
| `presidential-speeches` | 대통령기록관 연설문 |
| `msds-chemical-info` | 안전보건공단 MSDS |
| `dart-disclosure` | 금융감독원 DART 전자공시 — 기업 개황, 공시 목록·원문, 재무제표 (키: `DART_DISCLOSURE_API_KEY`) |
| `all-servers` | 위 7개 전부를 한 프로세스로 ([아래](#통합-서버-all-servers)) |

특정 커밋/태그에 고정하려면 `data-go-mcp-servers@v0.6.0#subdirectory=…` 처럼 `@` 뒤에 붙인다.

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

여러 서버를 쓰면 항목을 나란히 추가한다. 키는 하나로 전부 쓸 수 있다 (`dart-disclosure` 만 `"env": { "DART_DISCLOSURE_API_KEY": "<OpenDART 인증키>" }`). 저장 후 Claude Desktop 을 완전히 종료하고 다시 연다.

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

`dart-disclosure` 는 `-e DART_DISCLOSURE_API_KEY=<OpenDART 인증키>` 로 넘긴다 (`API_KEY` 는 이 서버에 쓰이지 않는다):

```
claude mcp add dart-disclosure -e DART_DISCLOSURE_API_KEY=<OpenDART 인증키> -- uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/dart-disclosure" data-go-mcp.dart-disclosure
```

## Cline / Cursor / 기타 MCP 클라이언트

stdio 서버를 등록하는 곳에 같은 `command`/`args`/`env` 를 넣으면 된다.

## 통합 서버 (all-servers)

서버 7개의 툴 36개를 **한 프로세스**로 띄우는 패키지. 설정 항목 하나로 전부 쓰고 싶을 때, 또는 Smithery 처럼 리스팅 하나에 서버 하나만 올릴 수 있는 곳에 쓴다.

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/all-servers" data-go-mcp.all-servers
```

환경변수는 `API_KEY` (data.go.kr 6종 공통) 와 `DART_DISCLOSURE_API_KEY` (OpenDART, 선택). 없는 키 쪽의 툴만 실패한다. 툴 36개가 한꺼번에 클라이언트에 실리므로 몇 개만 쓴다면 서버별 설치가 낫다.

## Smithery (smithery.ai)

통합 서버가 MCPB 번들로 올라가 있다 — [smithery.ai/servers/hichang4u/data-go-mcp](https://smithery.ai/servers/hichang4u/data-go-mcp). [Smithery CLI](https://smithery.ai/docs/concepts/cli) 로 클라이언트에 추가한다:

```bash
npm install -g smithery@latest
smithery mcp add hichang4u/data-go-mcp --client claude     # Claude Desktop
smithery mcp add hichang4u/data-go-mcp --client cursor
```

설치 때 data.go.kr 인증키(필수)와 OpenDART 인증키(선택)를 묻고, 클라이언트 설정의 `API_KEY` / `DART_DISCLOSURE_API_KEY` 로 넣는다. 번들은 `uv` 로 저장소의 태그 하나에 고정된 패키지를 설치해 실행한다 — 번들 안에 코드는 없다.

배포 절차(번들 만들기·올리기)는 [release.md](../development/release.md).

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

키를 안 넣으면 서버는 뜨지만 툴 호출이 "API key is required …" 오류로 실패한다. 오류 문구에 어떤 변수를 채워야 하는지(`API_KEY` 또는 `DART_DISCLOSURE_API_KEY`)와 발급처가 적혀 있다.
