# 나라장터 공공데이터개방표준서비스 MCP Server

[English Documentation](#english-documentation)

조달청 나라장터(G2B)의 입찰공고, 낙찰정보, 계약정보를 조회할 수 있는 MCP 서버입니다.

## 주요 기능

- 🔍 **입찰공고 검색**: 날짜별 입찰공고 정보 조회
- 🏆 **낙찰정보 검색**: 업무구분별 낙찰 정보 조회
- 📋 **계약정보 검색**: 기관별 계약 정보 조회
- 📊 **상세정보 조회**: 특정 입찰공고의 상세 정보 확인

## 설치 방법

### PyPI를 통한 설치 (권장)

```bash
pip install data-go-mcp.pps-narajangteo
```

또는 `uvx`를 사용하여 직접 실행:

```bash
uvx data-go-mcp.pps-narajangteo@latest
```

### 소스 코드로부터 설치

```bash
git clone https://github.com/yourusername/data-go-mcp-servers
cd data-go-mcp-servers/src/pps-narajangteo
pip install -e .
```

## 환경 설정

### API 키 발급

1. [data.go.kr](https://www.data.go.kr) 회원가입
2. '나라장터 공공데이터개방표준서비스' 검색 및 활용신청
3. 발급받은 API 키를 환경변수로 설정

### 환경변수 설정

```bash
export API_KEY="your-api-key-here"
```

### Claude Desktop 설정

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pps-narajangteo": {
      "command": "uvx",
      "args": ["data-go-mcp.pps-narajangteo@latest"],
      "env": {
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## 사용 가능한 Tools

### 1. search_bid_announcements
입찰공고 정보를 검색합니다.

**파라미터:**
- `start_date` (선택): 검색 시작일 (YYYY-MM-DD 또는 YYYYMMDD)
- `end_date` (선택): 검색 종료일 (YYYY-MM-DD 또는 YYYYMMDD)
- `num_of_rows` (기본값: 10): 페이지당 결과 수 (최대: 999)
- `page_no` (기본값: 1): 페이지 번호

**예시:**
```python
# 오늘 공고된 입찰정보
result = await search_bid_announcements()

# 특정 기간 입찰공고
result = await search_bid_announcements(start_date="2025-07-01", end_date="2025-07-31")
```

**Claude에서 사용 예시:**
- "오늘 공고된 입찰정보를 보여줘"
- "2025년 7월 입찰공고를 검색해줘"
- "최근 입찰공고 100건을 조회해줘"

### 2. search_successful_bids
낙찰정보를 검색합니다.

**파라미터:**
- `business_type` (필수): 업무구분
  - "1" 또는 "물품": 물품
  - "2" 또는 "외자": 외자
  - "3" 또는 "공사": 공사
  - "5" 또는 "용역": 용역
- `start_date` (선택): 개찰 시작일
- `end_date` (선택): 개찰 종료일
- `num_of_rows` (기본값: 10): 페이지당 결과 수
- `page_no` (기본값: 1): 페이지 번호

**예시:**
```python
# 최근 7일간 공사 낙찰정보
result = await search_successful_bids(business_type="공사")

# 특정 기간 물품 낙찰정보
result = await search_successful_bids(
    business_type="1", start_date="2025-07-01", end_date="2025-07-07"
)
```

**Claude에서 사용 예시:**
- "최근 공사 낙찰 정보를 알려줘"
- "이번 주 물품 낙찰 현황을 조회해줘"
- "용역 분야 낙찰 결과를 검색해줘"

### 3. search_contracts
계약정보를 검색합니다.

**파라미터:**
- `start_date` (선택): 계약체결 시작일 (YYYY-MM-DD 또는 YYYYMMDD)
- `end_date` (선택): 계약체결 종료일
- `institution_type` (선택): 기관구분
  - "1": 계약기관
  - "2": 수요기관
- `institution_code` (선택): 기관코드 (7자리)
- `num_of_rows` (기본값: 10): 페이지당 결과 수
- `page_no` (기본값: 1): 페이지 번호

**예시:**
```python
# 오늘 체결된 계약
result = await search_contracts()

# 특정 기관의 계약정보
result = await search_contracts(
    start_date="2025-03-01",
    end_date="2025-03-31",
    institution_type="1",
    institution_code="4490000",  # 천안시
)
```

**Claude에서 사용 예시:**
- "오늘 체결된 계약 정보를 보여줘"
- "3월 한 달간 계약 현황을 조회해줘"
- "천안시의 최근 계약을 검색해줘"

### 4. get_bid_detail
특정 입찰공고의 상세정보를 조회합니다.

**파라미터:**
- `bid_notice_no` (필수): 입찰공고번호 (예: R25BK00933743)

**예시:**
```python
result = await get_bid_detail("R25BK00933743")
```

**Claude에서 사용 예시:**
- "입찰공고번호 R25BK00933743의 상세정보를 알려줘"
- "R25BK00933743 입찰공고 내용을 확인해줘"

## 응답 형식

모든 도구는 다음과 같은 형식으로 응답합니다:

```json
{
  "success": true,
  "items": [...],  // 검색 결과 배열
  "total_count": 100,  // 전체 결과 수
  "page_no": 1,  // 현재 페이지
  "num_of_rows": 10,  // 페이지당 결과 수
  "search_period": "20250701 ~ 20250731"  // 검색 기간
}
```

오류 발생 시:
```json
{
  "success": false,
  "error": "오류 메시지",
  "items": [],
  "total_count": 0
}
```

## 제약사항

- **입찰공고 및 계약정보**: 검색 기간 최대 1개월
- **낙찰정보**: 검색 기간 최대 1주일
- **API 호출 제한**: 30 TPS (초당 30회)
- **응답 크기**: 최대 4000 bytes

## 에러 코드

| 코드 | 설명 | 해결방법 |
|------|------|----------|
| 01 | Application Error | 서비스 제공기관 문의 |
| 03 | No Data - 데이터 없음 | 검색 조건 확인 |
| 06 | 날짜 형식 오류 | YYYYMMDD 형식으로 입력 |
| 07 | 입력값 범위 초과 | 검색 기간 축소 (1개월/1주일 이내) |
| 08 | 필수값 누락 | 필수 파라미터 확인 |
| 22 | 일일 트래픽 초과 | 다음날 재시도 |
| 30 | 등록되지 않은 서비스키 | API 키 확인 |
| 31 | 기한 만료된 서비스키 | API 키 갱신 필요 |

## 개발

### 환경 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/data-go-mcp-servers.git
cd data-go-mcp-servers/src/pps-narajangteo

# 의존성 설치
uv sync
```

### 테스트

```bash
# 테스트 실행
uv run pytest tests/

# 커버리지 포함 테스트
uv run pytest tests/ --cov=data_go_mcp.pps_narajangteo
```

### 로컬 실행

```bash
# API 키 설정
export API_KEY="your-api-key"

# 서버 실행
uv run python -m data_go_mcp.pps_narajangteo.server
```

---

## English Documentation

MCP server for accessing Public Procurement Service (G2B) bid announcements, successful bid information, and contract information.

## Features

- 🔍 **Bid Announcement Search**: Search bid announcements by date
- 🏆 **Successful Bid Search**: Search successful bids by business type
- 📋 **Contract Search**: Search contracts by institution
- 📊 **Detail View**: Get detailed information for specific bid

## Installation

### Via PyPI (Recommended)

```bash
pip install data-go-mcp.pps-narajangteo
```

Or run directly with `uvx`:

```bash
uvx data-go-mcp.pps-narajangteo@latest
```

## Configuration

### Getting API Key

1. Sign up at [data.go.kr](https://www.data.go.kr)
2. Search and apply for '나라장터 공공데이터개방표준서비스' API
3. Set the API key as an environment variable

### Claude Desktop Setup

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pps-narajangteo": {
      "command": "uvx",
      "args": ["data-go-mcp.pps-narajangteo@latest"],
      "env": {
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Available Tools

### 1. search_bid_announcements
Search for bid announcements.

**Parameters:**
- `start_date`: Search start date (YYYY-MM-DD)
- `end_date`: Search end date
- `num_of_rows`: Results per page (max: 999)
- `page_no`: Page number

### 2. search_successful_bids
Search for successful bid information.

**Parameters:**
- `business_type`: Business type (1:Goods, 2:Foreign, 3:Construction, 5:Service)
- `start_date`: Opening start date
- `end_date`: Opening end date
- `num_of_rows`: Results per page
- `page_no`: Page number

### 3. search_contracts
Search for contract information.

**Parameters:**
- `start_date`: Contract start date
- `end_date`: Contract end date
- `institution_type`: Institution type (1:Contract agency, 2:Demand agency)
- `institution_code`: Institution code (7 digits)
- `num_of_rows`: Results per page
- `page_no`: Page number

### 4. get_bid_detail
Get detailed information for a specific bid announcement.

**Parameters:**
- `bid_notice_no`: Bid announcement number (e.g., R25BK00933743)

## Limitations

- Bid announcements & contracts: Maximum 1 month search period
- Successful bids: Maximum 1 week search period
- API rate limit: 30 TPS (30 requests per second)

## API Documentation

For detailed API documentation, visit:
- Service URL: http://apis.data.go.kr/1230000/ao/PubDataOpnStdService
- data.go.kr: https://www.data.go.kr

## License

Apache License 2.0

## Contributing

Contributions are welcome! Please see the [main repository](https://github.com/yourusername/data-go-mcp-servers) for contribution guidelines.

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/data-go-mcp-servers/issues
- Documentation: https://github.com/yourusername/data-go-mcp-servers