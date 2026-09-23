# 시작하기 — Claude 에서 공공데이터 조회하기

Claude Desktop 에 확장 프로그램 하나를 설치하면 Claude 에게 "이 사업자번호 폐업했는지 봐줘", "삼성전자 작년 매출 알려줘" 처럼 물어볼 수 있게 된다. 프로그램 설치나 코드 작성은 필요 없다. 10분 정도 걸린다.

준비물: [Claude Desktop](https://claude.ai/download) (Windows / macOS), 이메일 주소.

## 1단계. 공공데이터포털 인증키 받기

1. [data.go.kr](https://www.data.go.kr) 에 회원가입하고 로그인한다.
2. 오른쪽 위 **마이페이지** → **일반 인증키** 에서 **Decoding** 값을 복사해 메모장에 붙여 둔다.
   - 인증키는 두 줄(Encoding / Decoding)로 보인다. **Decoding** 쪽이다 — 보통 `==` 로 끝난다.

## 2단계. 쓸 서비스에 "활용신청" 하기

인증키만으로는 안 되고, 조회할 서비스마다 **활용신청** 버튼을 한 번씩 눌러야 한다. 모두 자동 승인이라 누르면 바로 쓸 수 있다. 신청서의 활용목적은 "참고자료", 상세 기능은 "업무 참고용 조회" 정도로 쓰면 된다.

필요한 것만 신청하면 된다:

| 이런 걸 물어보고 싶다면 | 신청할 서비스 |
|---|---|
| 사업자번호가 진짜인지, 휴·폐업했는지 | 포털 검색창에 "국세청_사업자등록정보 진위확인 및 상태조회 서비스" |
| 회사의 국민연금 가입자 수, 고용·산재보험 | [국민연금 가입 사업장 내역](https://www.data.go.kr/data/3046071/openapi.do), [법정동코드](https://www.data.go.kr/data/15077871/openapi.do), [고용/산재보험 현황](https://www.data.go.kr/data/15059256/openapi.do) |
| 나라장터 입찰공고·낙찰·계약 | 포털 검색창에 "조달청_나라장터 공공데이터개방표준서비스" |
| 회사 재무제표, 법인번호, 주가 | [기업 재무정보](https://www.data.go.kr/data/15043459/openapi.do), [기업기본정보](https://www.data.go.kr/data/15043184/openapi.do), [주식시세정보](https://www.data.go.kr/data/15094808/openapi.do) |
| 대통령 연설문 | [대통령연설기록](https://www.data.go.kr/data/15084167/fileData.do) → "오픈API" 탭 |
| 화학물질 안전정보(MSDS) | 신청 없이 된다 |

**전자공시(DART)** 까지 쓰려면 키가 하나 더 필요하다: [opendart.fss.or.kr](https://opendart.fss.or.kr) 회원가입 → **인증키 신청/관리** → 인증키 신청. 바로 발급된다. 안 쓸 거면 건너뛴다.

## 3단계. Claude Desktop 에 설치하기

1. **[data-go-mcp-desktop.mcpb 내려받기](https://github.com/hichang4u/data-go-mcp-servers/releases/latest/download/data-go-mcp-desktop.mcpb)**
2. Claude Desktop 을 열고 **설정 → 확장 프로그램** 으로 간다.
3. 내려받은 파일을 그 창에 끌어다 놓고 **설치** 를 누른다.
4. 입력란이 나오면:
   - **data.go.kr 인증키** — 1단계에서 복사한 Decoding 값
   - **OpenDART 인증키** — 받았으면 넣고, 아니면 비워 둔다
5. 확장 프로그램이 **켜짐** 상태인지 확인한다.

처음 켤 때 필요한 구성요소를 내려받느라 1~2분 걸릴 수 있다.

## 4단계. 물어보기

새 대화를 열고 평소처럼 묻는다. Claude 가 처음 조회할 때 "이 도구를 사용할까요?" 라고 물으면 **허용** 을 누른다. 모든 기능이 조회만 하므로 무언가를 바꾸거나 신청하지 않는다.

- 사업자등록번호 120-88-00767 이 지금 영업 중인지 확인해줘
- 삼성전자 2024년 매출액과 영업이익 알려줘
- 어제 나라장터에 올라온 소프트웨어 개발 입찰공고 찾아줘
- ㈜○○의 국민연금 가입자 수 추이 보여줘
- 벤젠 MSDS 에서 응급조치 요령 알려줘
- 카카오 최근 한 달 공시 목록 보여줘 (OpenDART 키 필요)

## 안 될 때

Claude 가 보여주는 오류 문구로 원인을 알 수 있다.

| 오류에 이런 말이 있으면 | 해결 |
|---|---|
| `API key is required` | 인증키를 안 넣었다. 설정 → 확장 프로그램 → 이 확장의 설정에서 넣는다 |
| `SERVICE_KEY_IS_NOT_REGISTERED` 또는 `[30]` | 그 서비스에 활용신청을 안 했거나, Encoding 키를 넣었다. 2단계 표에서 신청하고 키가 Decoding 값인지 확인 |
| `유효하지 않은 인증키` 또는 `[-401]` | 사업자등록·연설문 서비스 활용신청이 안 됐다 |
| `OpenDART 오류 [010]` | OpenDART 키가 틀렸다 |
| `[07] 입력범위값 초과` | 나라장터 조회 기간이 너무 길다. "지난 7일" 처럼 줄여서 다시 묻는다 |

확장 프로그램 목록에 오류 표시가 있거나 Claude 가 도구를 아예 못 찾으면 Claude Desktop 을 완전히 종료(작업 표시줄/메뉴 막대의 아이콘에서 종료)했다가 다시 연다. 그래도 안 되면 [문제 해결](troubleshooting.md) 을 본다.

## Claude Code 를 쓴다면

[uv](https://docs.astral.sh/uv/getting-started/installation/) 를 설치한 뒤 터미널에서 한 줄:

```
claude mcp add data-go -s user -e API_KEY=<data.go.kr 인증키> -e DART_DISCLOSURE_API_KEY=<OpenDART 인증키> -- uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/all-servers" data-go-mcp.all-servers
```

OpenDART 키가 없으면 `-e DART_DISCLOSURE_API_KEY=…` 부분을 뺀다. 필요한 서버만 따로 설치하는 방법, 다른 MCP 클라이언트(Cursor, Cline 등) 설정은 [설치와 클라이언트 설정](installation.md).
