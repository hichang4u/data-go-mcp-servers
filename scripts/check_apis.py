"""각 서버가 사용하는 공공 API(7개)가 살아 있는지 최소 요청으로 확인한다.

사용법:
    API_KEY=... uv run python scripts/check_apis.py

각 엔드포인트에 가장 가벼운 조회를 한 번 보내고 HTTP 상태와 resultCode를 출력한다.
resultCode 30/31/32 는 키 문제, 12 는 서비스 폐기, HTTP 404 는 엔드포인트 변경을 뜻한다.
"""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv


load_dotenv()

# (서버명, 메서드, URL, 추가 파라미터/바디)
TARGETS = [
    (
        "nps-business-enrollment",
        "GET",
        "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2/getBassInfoSearchV2",
        {"wkplNm": "삼성전자", "numOfRows": 1, "pageNo": 1, "dataType": "json"},
    ),
    (
        "nps-business-enrollment (법정동코드)",
        "GET",
        "https://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList",
        {"locatadd_nm": "강남구", "numOfRows": 1, "pageNo": 1, "type": "json"},
    ),
    (
        "nts-business-verification",
        "POST",
        "https://api.odcloud.kr/api/nts-businessman/v1/status",
        {"b_no": ["1208800767"]},
    ),
    (
        "pps-narajangteo",
        "GET",
        "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService/getDataSetOpnStdBidPblancInfo",
        {
            "numOfRows": 1,
            "pageNo": 1,
            "type": "json",
            "bidNtceBgnDt": "202501010000",
            "bidNtceEndDt": "202501020000",
        },
    ),
    (
        "fsc-financial-info",
        "GET",
        "https://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2/getSummFinaStat_V2",
        {
            "numOfRows": 1,
            "pageNo": 1,
            "resultType": "json",
            "bizYear": "2023",
            "crno": "1301110006246",
        },
    ),
    (
        "presidential-speeches",
        "GET",
        "https://api.odcloud.kr/api/15084167/v1/uddi:1c8b5454-bd4e-45db-98f7-fe94d71f271b",
        {"page": 1, "perPage": 1},
    ),
    (
        "msds-chemical-info",
        "GET",
        "https://msds.kosha.or.kr/openapi/service/msdschem/chemlist",
        {"searchWrd": "benzene", "searchCnd": 0, "numOfRows": 1, "pageNo": 1},
    ),
]


async def check(client: httpx.AsyncClient, name: str, method: str, url: str, extra: dict) -> str:
    """엔드포인트 하나를 호출하고 한 줄 요약을 돌려준다."""
    key = os.environ["API_KEY"]
    try:
        if method == "POST":
            r = await client.post(
                url, params={"serviceKey": key, "returnType": "JSON"}, json=extra
            )
        else:
            r = await client.get(url, params={"serviceKey": key, **extra})
    except httpx.HTTPError as e:
        return f"{name:36s} NETWORK ERROR {e}"

    body = r.text[:200].replace("\n", " ")
    code = ""
    try:
        data = r.json()
        header = data.get("response", {}).get("header", {})
        code = header.get("resultCode", "") or str(data.get("status_code", ""))
        if not code and "StanReginCd" in data:  # 법정동코드: head 배열 안의 RESULT
            for entry in data["StanReginCd"][0].get("head", []):
                code = code or entry.get("RESULT", {}).get("resultCode", "")
        if not code and "RESULT" in data:  # 법정동코드: 결과 없음/오류는 최상위 RESULT
            code = data["RESULT"].get("resultCode", "")
    except (ValueError, LookupError, AttributeError, TypeError):
        pass
    return f"{name:36s} HTTP {r.status_code}  resultCode={code or '-':4s}  {body}"


async def main() -> int:
    """모든 대상을 병렬로 확인하고 결과를 출력한다."""
    if not os.getenv("API_KEY"):
        print("API_KEY 환경변수가 필요합니다 (.env 또는 export)", file=sys.stderr)
        return 1
    async with httpx.AsyncClient(timeout=20.0) as client:
        for line in await asyncio.gather(*(check(client, *t) for t in TARGETS)):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
