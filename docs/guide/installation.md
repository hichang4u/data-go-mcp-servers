# 설치와 클라이언트 설정

> Claude Desktop 에 처음 설치한다면 [시작하기](quickstart.md) 가 더 쉽다.

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

특정 커밋/태그에 고정하려면 `data-go-mcp-servers@v0.6.2#subdirectory=…` 처럼 `@` 뒤에 붙인다.

## Claude Desktop

방법이 둘이다. 서버 7개를 다 쓸 거면 **A**, 필요한 서버만 골라 쓸 거면 **B**.

### A. 확장 프로그램(.mcpb)으로 설치 — uv 불필요

1. [data-go-mcp-desktop.mcpb](https://github.com/hichang4u/data-go-mcp-servers/releases/latest/download/data-go-mcp-desktop.mcpb) 를 받는다 (최신 릴리스의 파일로 바로 연결된다).
2. Claude Desktop → 설정 → 확장 프로그램 창에 파일을 끌어다 놓고 설치한다.
3. 설치 창에서 키를 넣는다.
   - **data.go.kr 인증키** (필수) — 마이페이지의 일반 인증키 **Decoding** 값
   - **OpenDART 인증키** (선택) — 비워 두면 DART 툴만 실패한다
4. 확장 프로그램이 켜져 있는지 확인한다.

설치되는 것은 [통합 서버](#통합-서버-all-servers)(툴 36개)다. Claude Desktop 이 자체 uv 로 의존성을 설치하므로 uv 를 따로 깔 필요가 없다. 키를 바꾸려면 확장 프로그램 목록에서 이 확장의 설정을 연다.

`data-go-mcp.mcpb`(이름에 `desktop` 이 없는 것)는 Smithery 용이라 Claude Desktop 에 끌어 놓으면 설치가 거부된다.

### B. 설정 파일에 직접 추가

설정 → 개발자 → 설정 편집, 또는 파일을 직접 연다:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

서버 하나:

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

여러 서버는 `mcpServers` 안에 항목을 나란히 둔다. data.go.kr 키 하나를 서버마다 똑같이 넣고, `dart-disclosure` 에만 OpenDART 키를 넣는다:

```json
{
  "mcpServers": {
    "nps-business-enrollment": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nps-business-enrollment", "data-go-mcp.nps-business-enrollment"],
      "env": { "API_KEY": "<data.go.kr 인증키>" }
    },
    "fsc-financial-info": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/fsc-financial-info", "data-go-mcp.fsc-financial-info"],
      "env": { "API_KEY": "<data.go.kr 인증키>" }
    },
    "dart-disclosure": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/dart-disclosure", "data-go-mcp.dart-disclosure"],
      "env": { "DART_DISCLOSURE_API_KEY": "<OpenDART 인증키>" }
    }
  }
}
```

이미 다른 MCP 서버가 있으면 `mcpServers` 를 새로 만들지 말고 그 안에 항목만 추가한다. 저장한 뒤 Claude Desktop 을 **완전히 종료**(트레이/메뉴 막대에서 종료)하고 다시 연다 — 창만 닫으면 설정을 다시 읽지 않는다.

- Windows 에서 `uvx` 를 못 찾으면 `"command"` 에 전체 경로(`C:\Users\<you>\.local\bin\uvx.exe`, JSON 이라 `\`)를 쓴다.
- 첫 실행은 git clone + 빌드로 시간이 걸려 Claude Desktop 이 연결 실패로 표시할 수 있다. 터미널에서 [실행 명령](#실행-명령)을 한 번 돌려 캐시를 만들어 두면 다음부터 바로 뜬다 (서버가 뜨면 `Ctrl+C` 로 끈다).

### 연결 확인

- 채팅 입력창의 도구(커넥터) 메뉴에 서버 이름과 툴이 보이면 연결된 것이다. 서버가 목록에 없거나 오류 표시가 있으면 [문제 해결](troubleshooting.md#서버가-아예-뜨지-않을-때)의 로그 위치를 본다.
- 툴을 처음 호출할 때 Claude 가 실행 허가를 묻는다. 모든 툴이 조회 전용이라 "항상 허용"해도 데이터가 바뀌지 않는다.
- 질문 예: "사업자등록번호 120-88-00767 상태 조회해줘", "삼성전자 2024년 요약 재무제표 보여줘", "어제 나라장터에 올라온 소프트웨어 입찰공고 찾아줘".

## Claude Code

```
claude mcp add nts-business-verification -e API_KEY=<인증키> -- uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification" data-go-mcp.nts-business-verification
```

`--` 뒤가 서버 실행 명령이고, `-e` 는 `--` 앞에 둔다. 등록 범위는 `-s` 로 정한다:

| `-s` | 적용 범위 | 저장 위치 |
|---|---|---|
| `local` (기본) | 현재 프로젝트, 나만 | `~/.claude.json` 의 프로젝트 항목 |
| `user` | 모든 프로젝트, 나만 | `~/.claude.json` |
| `project` | 현재 프로젝트, 팀 공유 | 프로젝트의 `.mcp.json` (커밋 대상) |

어느 폴더에서든 쓰려면 `-s user`. 서버 전부를 한 번에 등록하려면 통합 서버:

```
claude mcp add data-go -s user -e API_KEY=<data.go.kr 인증키> -e DART_DISCLOSURE_API_KEY=<OpenDART 인증키> -- uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/all-servers" data-go-mcp.all-servers
```

`dart-disclosure` 를 따로 쓸 때는 `-e DART_DISCLOSURE_API_KEY=<OpenDART 인증키>` 로 넘긴다 (`API_KEY` 는 이 서버에 쓰이지 않는다):

```
claude mcp add dart-disclosure -e DART_DISCLOSURE_API_KEY=<OpenDART 인증키> -- uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/dart-disclosure" data-go-mcp.dart-disclosure
```

팀과 설정을 공유할 때는 프로젝트의 `.mcp.json` 에 키 대신 환경변수 참조를 쓴다. `${API_KEY}` 는 Claude Code 를 띄운 셸의 환경변수에서 채워지므로 각자 자기 셸에 `API_KEY` 를 설정해 둔다:

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

`.mcp.json` 의 서버는 처음 열 때 사용 승인을 묻는다.

확인과 관리:

```
claude mcp list                  # 등록된 서버와 연결 상태
claude mcp get data-go           # 한 서버의 명령·환경변수
claude mcp remove data-go -s user
```

세션 안에서는 `/mcp` 로 연결 상태와 툴 목록을 본다. 키를 바꾸려면 `remove` 후 다시 `add` 한다.

## claude.ai (웹·모바일)

지원하지 않는다. 이 서버들은 로컬에서 실행하는 stdio 서버이고, claude.ai 의 커스텀 커넥터는 원격(HTTP) MCP 서버 URL 을 요구한다. 이 저장소는 원격 서버를 운영하지 않는다.

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

설치 때 data.go.kr 인증키(필수)와 OpenDART 인증키(선택)를 묻고, 클라이언트 설정의 `API_KEY` / `DART_DISCLOSURE_API_KEY` 로 넣는다. 번들은 `uv` 로 저장소의 태그 하나에 고정된 패키지를 설치해 실행한다 — 번들 안에 코드는 없고, 이 경로는 PATH 에 `uv` 가 있어야 한다.

Claude Desktop 에 번들을 직접 설치하는 방법은 [위](#a-확장-프로그램mcpb으로-설치--uv-불필요).

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
