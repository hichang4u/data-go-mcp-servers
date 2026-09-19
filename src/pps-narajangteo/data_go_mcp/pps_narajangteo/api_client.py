"""API client for 나라장터 공공데이터개방표준서비스 (Public Procurement Service Open Data)."""

from typing import Any, Mapping, Optional

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError


ERROR_WRAPPER = "nkoneps.com.response.ResponseError"


class PpsNarajangteoAPIClient(BaseDataGoClient):
    """나라장터 공공데이터개방표준 API 클라이언트.

    응답 ``body.items`` 는 다른 data.go.kr 서비스와 달리 리스트로 바로 온다
    (``normalize_items`` 가 처리).
    """

    base_url = "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService"
    key_env_prefix = "PPS_NARAJANGTEO"
    default_params = {"type": "json"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """오류는 ``response`` 대신 ``nkoneps.com.response.ResponseError`` 로 온다 (2026-09-20 확인)."""
        error = data.get(ERROR_WRAPPER)
        if isinstance(error, Mapping):
            header = error.get("header") or {}
            raise DataGoAPIError(
                str(header.get("resultCode", "")), str(header.get("resultMsg", ""))
            )
        return super()._check_response(data)

    async def get_bid_announcements(
        self,
        bid_notice_begin_dt: str,
        bid_notice_end_dt: str,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """입찰공고정보 조회. 공고일시 범위는 최대 1개월 (YYYYMMDDHHMM)."""
        return await self.get(
            "getDataSetOpnStdBidPblancInfo",
            {
                "bidNtceBgnDt": bid_notice_begin_dt,
                "bidNtceEndDt": bid_notice_end_dt,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            },
        )

    async def get_successful_bids(
        self,
        business_div_code: str,
        opening_begin_dt: Optional[str] = None,
        opening_end_dt: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """낙찰정보 조회. 업무구분(1:물품, 2:외자, 3:공사, 5:용역), 개찰일시 범위는 하루(2일부터 코드 07)."""
        return await self.get(
            "getDataSetOpnStdScsbidInfo",
            {
                "bsnsDivCd": business_div_code,
                "opengBgnDt": opening_begin_dt,
                "opengEndDt": opening_end_dt,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            },
        )

    async def get_contracts(
        self,
        contract_begin_date: Optional[str] = None,
        contract_end_date: Optional[str] = None,
        institution_div_code: Optional[str] = None,
        institution_code: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """계약정보 조회. 계약체결일자(YYYYMMDD) 범위 최대 1개월."""
        return await self.get(
            "getDataSetOpnStdCntrctInfo",
            {
                "cntrctCnclsBgnDate": contract_begin_date,
                "cntrctCnclsEndDate": contract_end_date,
                "insttDivCd": institution_div_code,
                "insttCd": institution_code,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            },
        )
