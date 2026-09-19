# 문제 해결

툴이 실패하면 클라이언트에 **오류 결과(isError)** 로 전달된다. Claude 는 이를 실패로 인식하고 메시지를 보여준다. 메시지 앞머리로 원인을 구분한다.

| 메시지 | 뜻 | 조치 |
|---|---|---|
| `입력값 오류: API key is required …` | 키가 없음 | 클라이언트 설정 `env.API_KEY` 확인 (dart-disclosure 는 `DART_DISCLOSURE_API_KEY`) |
| `data.go.kr 오류 [30] SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | 키는 있으나 그 API 에 활용신청이 안 됨, 또는 Encoding 키를 넣음. nps(사업장, 법정동코드, 고용산재보험)·fsc(재무정보, 기업기본정보, 주식시세)는 API 가 여럿이라 전부 신청 | [api-keys.md](api-keys.md) 2·1 절 |
| `data.go.kr 오류 [-401] 유효하지 않은 인증키` | odcloud 계열(nts, presidential) 미신청 | 활용신청 |
| `data.go.kr 오류 [22] …EXCEEDS` | 일일 트래픽 초과 | 다음 날 또는 운영계정 신청 |
| `data.go.kr 오류 [12] …` | 서비스가 폐기됨 | 이슈 등록 |
| `data.go.kr 오류 [07] 입력범위값 초과` (나라장터) | 조회 기간이 제한(입찰공고 1개월, 계약 7일, 낙찰 하루)을 넘음 | 기간을 줄인다 |
| `OpenDART 오류 [010]` / `[011]` | DART 키가 미등록/사용 제한 | [api-keys.md](api-keys.md) 4절 |
| `OpenDART 오류 [020]` | DART 일일 한도(20,000건) 초과 | 다음 날 |
| `OpenDART 오류 [100] corp_code가 없는 경우 검색기간은 3개월만` | `list_disclosures` 를 회사 없이 긴 기간으로 호출 | `corp_code` 를 주거나 기간을 줄인다 |
| `입력값 오류: …` | 파라미터 형식 문제 (자리수, 날짜 형식, 범위) | 메시지대로 수정 |
| `HTTP 5xx: …` | 기관 서버 장애 | 잠시 후 재시도 |
| `네트워크 오류: …` | DNS/방화벽/프록시 | 회사망이면 `apis.data.go.kr`, `api.odcloud.kr`, `msds.kosha.or.kr`, `opendart.fss.or.kr` 허용 |

## 서버가 아예 뜨지 않을 때

- **`uvx` 를 찾을 수 없음**: uv 설치 후 터미널을 다시 열거나 `command` 에 전체 경로를 쓴다.
- **첫 실행이 오래 걸림**: git clone + 빌드 때문. 이후는 캐시.
- **Claude Desktop 로그**: macOS `~/Library/Logs/Claude/mcp*.log`, Windows `%APPDATA%\Claude\logs\mcp*.log`. 서버의 stderr 가 여기 찍힌다.
- 서버는 키가 없어도 뜬다. 키 문제는 툴 호출 시점에 오류로 나온다.

## 결과가 비어 있을 때 (오류는 아님)

- nps: 사업장명은 부분 일치지만 법인명 표기(㈜, (주))에 따라 다를 수 있다. 사업자번호 앞 6자리로 시도. 지역 코드는 시군구만 주면 무시된다 — `find_region_code` 의 `nps_params` 처럼 시도부터 함께 준다.
- fsc: 법인등록번호(13자리)를 사업자등록번호(10자리)와 혼동하지 않았는지 — `find_corp_number` 로 변환. 해당 연도에 공시가 없을 수 있다.
- pps: 날짜 범위가 주말/공휴일만 포함하면 0건일 수 있다.
- presidential: 대통령 이름은 정확히 일치해야 한다 ("문재인 대통령" ✗, "문재인" ○).
- nps `get_insurance_status`: 사업자등록번호 **10자리 전체**가 필요하다 (`search_business` 의 앞 6자리와 다름). 가입 사업장이 없는 법인은 0건이 정상.
- dart `list_disclosures`: 접수일 기준이라 `bgn_de` 를 너무 최근으로 주면 0건. 재무제표 툴은 2015년 이후 상장사만 — 비상장·그 이전은 0건이 정상. `find_corp_code` 0건이면 약칭 대신 등기명(`(주)` 없이)으로.
- fsc `find_corp_number`: 회사명은 부분 일치라 흔한 이름은 페이지가 넘친다 — `(주)` 를 붙이거나 사업자번호로. `get_stock_price`: 종목명은 정확히 일치(`search_stock_items` 로 확인), 날짜를 지정했는데 0건이면 휴장일이거나 아직 발행 전(전 거래일까지 제공).

## 직접 점검

```bash
git clone https://github.com/hichang4u/data-go-mcp-servers && cd data-go-mcp-servers
uv sync --dev --all-packages
cp .env.example .env                    # API_KEY, (DART 를 쓰면) DART_DISCLOSURE_API_KEY 채우기
uv run python scripts/check_apis.py     # 11개 API 생존·권한 확인 (키 없는 항목은 SKIP)
uv run pytest -m integration            # 서버당 실호출 1건
```
