"""쿠키 저장 / 재사용.

캡차로 인해 프로그램 로그인이 막힐 때, 사람이 1회 정상 로그인한 세션의
쿠키를 파일로 저장해 두고 이후 자동화에서 재사용한다.

쿠키는 비밀번호급 민감 정보이므로 cookies.json 은 절대 커밋하지 않는다
(.gitignore 에 포함됨).
"""

import json
import logging
from pathlib import Path

from selenium.common.exceptions import InvalidCookieDomainException, WebDriverException

logger = logging.getLogger(__name__)

# 쿠키를 심기 위해 먼저 방문할 기준 도메인
COOKIE_BASE_URL = "https://www.tistory.com/"


def save_cookies(driver, path: Path) -> int:
    """현재 드라이버 세션의 쿠키를 JSON 으로 저장한다. 저장한 개수를 반환한다."""
    cookies = driver.get_cookies()
    if not cookies:
        raise RuntimeError("저장할 쿠키가 없습니다. 로그인이 완료됐는지 확인하세요.")

    path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("쿠키 %d개 저장: %s", len(cookies), path.name)
    return len(cookies)


def _sanitize(cookie: dict) -> dict:
    """add_cookie 가 거부할 수 있는 필드를 정리한 새 dict 를 반환한다(불변)."""
    cleaned = {
        key: value
        for key, value in cookie.items()
        if key not in ("sameSite", "expiry", "domain")
    }
    expiry = cookie.get("expiry")
    if expiry is not None:
        cleaned["expiry"] = int(expiry)
    return cleaned


def load_cookies(driver, path: Path) -> int:
    """저장된 쿠키를 드라이버에 주입한다. 주입 성공 개수를 반환한다.

    add_cookie 는 현재 도메인에만 가능하므로 먼저 기준 URL 을 방문한다.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"쿠키 파일이 없습니다: {path.name}. 먼저 `python save_cookies.py` 를 실행하세요."
        )

    try:
        cookies = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(f"쿠키 파일을 읽을 수 없습니다: {error}")

    driver.get(COOKIE_BASE_URL)

    injected = 0
    for cookie in cookies:
        try:
            driver.add_cookie(_sanitize(cookie))
            injected += 1
        except (InvalidCookieDomainException, WebDriverException) as error:
            logger.debug("쿠키 주입 건너뜀(%s): %s", cookie.get("name"), error)

    if injected == 0:
        raise RuntimeError("유효한 쿠키를 하나도 주입하지 못했습니다. 쿠키를 다시 저장하세요.")

    driver.get(COOKIE_BASE_URL)  # 쿠키 적용 상태로 새로고침
    logger.info("쿠키 %d개 주입", injected)
    return injected
