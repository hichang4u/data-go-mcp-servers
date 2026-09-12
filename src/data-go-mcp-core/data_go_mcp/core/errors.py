"""data.go.kr 응답 오류."""

# data.go.kr 공통 resultCode. 원래 fsc-financial-info 에만 있던 표를 공통으로 옮긴 것.
RESULT_CODES: dict[str, str] = {
    "00": "정상처리",
    "01": "APPLICATION_ERROR - 어플리케이션 에러",
    "10": "INVALID_REQUEST_PARAMETER_ERROR - 잘못된 요청 파라메터 에러",
    "12": "NO_OPENAPI_SERVICE_ERROR - 해당 오픈API서비스가 없거나 폐기됨",
    "20": "SERVICE_ACCESS_DENIED_ERROR - 서비스 접근거부",
    "22": "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR - 서비스 요청제한횟수 초과에러",
    "30": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR - 등록되지 않은 서비스키",
    "31": "DEADLINE_HAS_EXPIRED_ERROR - 기한만료된 서비스키",
    "32": "UNREGISTERED_IP_ERROR - 등록되지 않은 IP",
    "99": "UNKNOWN_ERROR - 기타에러",
}


class DataGoAPIError(Exception):
    """API가 HTTP 200으로 응답했지만 ``resultCode`` 가 정상(00)이 아닐 때."""

    def __init__(self, result_code: str, result_msg: str) -> None:
        self.result_code = result_code
        self.result_msg = result_msg
        super().__init__(self._format())

    def _format(self) -> str:
        text = f"[{self.result_code}] {self.result_msg}"
        desc = RESULT_CODES.get(self.result_code)
        if desc and " - " in desc:
            text += f" ({desc.split(' - ', 1)[1]})"
        return text
