# API 키 발급과 활용신청

## 1. 인증키 발급

1. [data.go.kr](https://www.data.go.kr) 회원가입 → 로그인
2. 마이페이지 → **일반 인증키(Decoding)** 값을 복사

키는 하나로 이 저장소의 모든 서버에 쓸 수 있다. 안전보건공단(MSDS)도 같은 키로 호출된다. 예외는 `dart-disclosure` — 아래 4절.

Encoding 값(`%2B`, `%3D` 가 섞인 것)이 아니라 **Decoding 값**(`+`, `=` 가 그대로인 것, 보통 `==` 로 끝남)을 써야 한다. Encoding 값을 넣으면 서버가 한 번 더 인코딩해 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`(코드 30)가 난다.

## 2. API 별 활용신청

키가 있어도 **API 마다 활용신청**을 해야 한다. 미신청 상태면 코드 30(`등록되지 않은 서비스키`) 또는 odcloud 계열은 HTTP 401 이 온다. 전부 자동승인이며 신청 직후부터 쓸 수 있다.

한 서버가 API 여러 개를 쓰면 **그 서버의 모든 API** 에 신청해야 그 서버의 툴이 전부 동작한다. 쓰지 않을 툴의 API 는 건너뛰어도 된다 — 그 툴만 코드 30 으로 실패한다.

| 서버 | API (신청 페이지) | 쓰는 툴 |
|---|---|---|
| nps-business-enrollment | [국민연금공단_국민연금 가입 사업장 내역](https://www.data.go.kr/data/3046071/openapi.do) | `search_business` `get_business_detail` `get_period_status` |
| | [행정안전부_행정표준코드_법정동코드](https://www.data.go.kr/data/15077871/openapi.do) | `find_region_code` |
| | [근로복지공단_고용/산재보험 현황정보](https://www.data.go.kr/data/15059256/openapi.do) | `get_insurance_status` |
| nts-business-verification | 포털에서 "국세청_사업자등록정보 진위확인 및 상태조회 서비스" 검색 | 전체 |
| pps-narajangteo | 포털에서 "조달청_나라장터 공공데이터개방표준서비스" 검색 | 전체 |
| fsc-financial-info | [금융위원회_기업 재무정보](https://www.data.go.kr/data/15043459/openapi.do) | `get_summary_financial_statement` `get_balance_sheet` `get_income_statement` `search_company_financial_info` |
| | [금융위원회_기업기본정보](https://www.data.go.kr/data/15043184/openapi.do) | `find_corp_number` `get_corp_outline` |
| | [금융위원회_주식시세정보](https://www.data.go.kr/data/15094808/openapi.do) | `get_stock_price` `search_stock_items` |
| presidential-speeches | [대통령기록관_대통령연설기록(연설문)](https://www.data.go.kr/data/15084167/fileData.do) → "오픈API" 탭 | 전체 |
| msds-chemical-info | 별도 신청 없이 동작 확인됨 (2026-09) | 전체 |
| dart-disclosure | data.go.kr 아님 — 4절 | 전체 |

활용목적은 "참고자료" 또는 "앱개발" 정도면 되고, 사유는 "OO 조회 서비스에 OO 정보를 함께 제공하는 용도" 한 줄이면 충분하다. 개발계정 일일 트래픽은 대개 10,000건이다.

승인 페이지의 **End Point** 는 서버 코드에 이미 들어 있으니 따로 적어 둘 필요는 없다.

## 3. 키를 서버에 넘기는 방법

우선순위:

1. 서버별 변수 `<SERVER>_API_KEY` — 예: `NPS_BUSINESS_ENROLLMENT_API_KEY`
2. 공통 변수 `API_KEY`

보통 `API_KEY` 하나면 된다. 서버별 변수는 API 마다 다른 계정의 키를 써야 할 때만 쓴다.

MCP 클라이언트 설정의 `"env"` 로 넘기는 것이 기본이고, 저장소를 clone 해서 실행할 때는 루트의 `.env` 파일도 읽는다 (`.env.example` 을 복사해 채운다).

## 4. OpenDART 키 (dart-disclosure)

금융감독원 전자공시는 data.go.kr 을 거치지 않는다. [opendart.fss.or.kr](https://opendart.fss.or.kr) 회원가입 → **인증키 신청/관리** → 인증키 신청. 즉시 발급되고 활용신청 절차는 없다. 한도는 키당 일 20,000건.

서버에는 `DART_DISCLOSURE_API_KEY` 로만 넘긴다. 공통 `API_KEY` 는 이 서버에 쓰이지 않으며, 없으면 `입력값 오류: API key is required. Set DART_DISCLOSURE_API_KEY …` 가 난다. 잘못된 키는 `OpenDART 오류 [010] 등록되지 않은 인증키입니다.`

## 5. 확인

저장소를 clone 했다면 11개 API 를 한 번에 점검할 수 있다 (키가 없는 항목은 SKIP):

```bash
uv run python scripts/check_apis.py
```

각 줄의 `resultCode=00`, `INFO-0` 또는 `status_code OK` 가 정상이다. `30` 이면 그 API 의 활용신청이 안 된 것이다.
