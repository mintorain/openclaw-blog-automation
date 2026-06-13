"""환경변수 로딩 및 검증.

비밀번호 등 민감 정보는 코드에 하드코딩하지 않고 .env 에서만 읽는다.
값이 비어 있거나 형식이 잘못되면 즉시 명확한 오류로 중단한다.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

COOKIE_PATH = Path(__file__).parent / "cookies.json"


@dataclass(frozen=True)
class Config:
    """불변 설정 객체. 한 번 만들면 변경하지 않는다."""

    tistory_id: str
    tistory_pw: str
    blog_name: str
    headless: bool
    visibility: int
    post_delay_seconds: int
    max_posts_per_run: int
    cookie_path: Path


def _require(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise ValueError(f"환경변수 {key} 가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return value


def _int_env(key: str, default: int) -> int:
    raw = os.getenv(key, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"환경변수 {key} 는 정수여야 합니다. 현재 값: {raw!r}")


def load_config() -> Config:
    """검증된 불변 Config 를 반환한다."""
    visibility = _int_env("PUBLISH_VISIBILITY", 0)
    if visibility not in (0, 1, 2):
        raise ValueError("PUBLISH_VISIBILITY 는 0(비공개)/1(보호)/2(공개) 중 하나여야 합니다.")

    # 쿠키 재사용 모드에서는 비밀번호가 필요 없으므로 ID/PW 는 선택값으로 둔다.
    return Config(
        tistory_id=os.getenv("TISTORY_ID", "").strip(),
        tistory_pw=os.getenv("TISTORY_PW", "").strip(),
        blog_name=_require("TISTORY_BLOG_NAME"),
        headless=os.getenv("HEADLESS", "false").strip().lower() == "true",
        visibility=visibility,
        post_delay_seconds=_int_env("POST_DELAY_SECONDS", 7200),
        max_posts_per_run=_int_env("MAX_POSTS_PER_RUN", 3),
        cookie_path=COOKIE_PATH,
    )
