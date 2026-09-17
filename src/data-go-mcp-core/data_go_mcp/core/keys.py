"""API 키 로딩.

우선순위: 명시 인자 > ``<PREFIX>_API_KEY`` > ``API_KEY``.
data.go.kr 인증키 하나로 모든 API를 호출할 수 있으므로 공통 ``API_KEY`` 를 기본으로 하되,
서버별로 다른 키를 써야 할 때 ``<PREFIX>_API_KEY`` 로 덮어쓴다.

data.go.kr 이 아닌 포털(OpenDART 등)의 키는 ``API_KEY`` 로 호출하면 조용히 실패하므로
``shared=False`` 로 공통 키 fallback 을 끈다.
"""

import os


DATA_GO_KR_URL = "https://www.data.go.kr"


def load_api_key(
    prefix: str,
    explicit: str | None = None,
    *,
    shared: bool = True,
    key_url: str = DATA_GO_KR_URL,
) -> str:
    """API 키를 반환한다. 없으면 ``ValueError``.

    Args:
        prefix: 서버별 환경변수 접두어 (예: ``"NPS_BUSINESS_ENROLLMENT"``)
        explicit: 코드에서 직접 넘긴 키. 환경변수보다 우선한다.
        shared: ``False`` 면 공통 ``API_KEY`` 를 보지 않는다 (data.go.kr 키가 아닌 API).
        key_url: 오류 메시지에 안내할 키 발급처.
    """
    prefixed = f"{prefix}_API_KEY"
    candidates = [explicit, os.getenv(prefixed)]
    if shared:
        candidates.append(os.getenv("API_KEY"))
    for candidate in candidates:
        if candidate and candidate.strip():
            return candidate.strip()
    env_hint = f"{prefixed} or API_KEY" if shared else prefixed
    raise ValueError(
        f"API key is required. Set {env_hint} environment variable, "
        f"or pass api_key explicitly. Get a key from {key_url}"
    )
