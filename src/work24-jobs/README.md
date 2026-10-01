# 고용24 채용정보 MCP Server

고용24(옛 워크넷) 채용공고를 사업자등록번호·지역·직종으로 조회한다.

사용자 문서: [docs/guide/servers/work24-jobs.md](../../docs/guide/servers/work24-jobs.md)

## 실행

```bash
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/work24-jobs" data-go-mcp.work24-jobs
```

환경변수 `WORK24_API_KEY` ([www.work24.go.kr](https://www.work24.go.kr) 오픈API → 서비스별 신청). data.go.kr 의 공통 `API_KEY` 는 쓰이지 않는다.

## 툴

| 툴 | 하는 일 |
|---|---|
| `search_job_postings` | 채용공고 검색 (사업자번호·검색어·지역·직종·최저임금) |
| `get_job_posting` | 공고 상세 + 기업 정보(종업원 수, 자본금, 매출액) |
