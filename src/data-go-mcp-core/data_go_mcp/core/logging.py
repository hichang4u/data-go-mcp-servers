"""stdio 전송에서는 stdout이 프로토콜 채널이므로 로그는 반드시 stderr로만 보낸다."""

import logging
import sys


_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """루트 로거에 stderr 핸들러를 한 번만 붙이고 ``name`` 로거를 돌려준다."""
    root = logging.getLogger()
    already = any(getattr(h, "stream", None) is sys.stderr for h in root.handlers)
    if not already:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(handler)
    root.setLevel(min(root.level or level, level))
    # httpx 는 INFO 로 요청 URL(serviceKey 포함)을 남긴다 — 키가 로그에 새지 않도록 올린다
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return logging.getLogger(name)
