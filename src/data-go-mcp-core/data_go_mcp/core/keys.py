"""API 키 로딩.

우선순위: 명시 인자 > ``<PREFIX>_API_KEY`` > ``API_KEY``.
data.go.kr 인증키 하나로 모든 API를 호출할 수 있으므로 공통 ``API_KEY`` 를 기본으로 하되,
서버별로 다른 키를 써야 할 때 ``<PREFIX>_API_KEY`` 로 덮어쓴다.
"""

import os


def load_api_key(prefix: str, explicit: str | None = None) -> str:
    """API 키를 반환한다. 없으면 ``ValueError``.

    Args:
        prefix: 서버별 환경변수 접두어 (예: ``"NPS_BUSINESS_ENROLLMENT"``)
        explicit: 코드에서 직접 넘긴 키. 환경변수보다 우선한다.
    """
    prefixed = f"{prefix}_API_KEY"
    for candidate in (explicit, os.getenv(prefixed), os.getenv("API_KEY")):
        if candidate and candidate.strip():
            return candidate.strip()
    raise ValueError(
        f"API key is required. Set {prefixed} or API_KEY environment variable, "
        "or pass api_key explicitly. Get a key from https://www.data.go.kr"
    )
