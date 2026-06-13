"""사람이 직접 1회 로그인하여 쿠키를 저장하는 도우미 스크립트.

캡차/2단계 인증은 사람이 브라우저에서 직접 통과시키고,
완료 후 터미널에서 Enter 를 누르면 현재 세션 쿠키를 cookies.json 에 저장한다.

실행:
    python save_cookies.py
주의: 반드시 화면이 보이는 모드로 실행해야 하므로 HEADLESS 설정은 무시한다.
"""

import logging
import sys

from config import load_config
from cookie_store import COOKIE_BASE_URL, save_cookies
from driver_factory import create_driver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("save_cookies")

LOGIN_URL = "https://www.tistory.com/auth/login"


def main() -> int:
    try:
        config = load_config()
    except ValueError as error:
        logger.error("설정 오류: %s", error)
        return 1

    # 캡차/2FA 를 사람이 풀어야 하므로 항상 화면 표시 모드.
    driver = None
    try:
        driver = create_driver(headless=False)
        driver.get(LOGIN_URL)

        print("\n" + "=" * 60)
        print(" 브라우저에서 티스토리(카카오) 로그인을 끝까지 완료하세요.")
        print(" 캡차/2단계 인증이 있으면 직접 통과시키면 됩니다.")
        print(" 로그인이 끝나면 이 창으로 돌아와 Enter 를 누르세요.")
        print("=" * 60)
        input(" 로그인 완료 후 Enter ▶ ")

        # 쿠키는 기준 도메인 기준으로 저장한다.
        driver.get(COOKIE_BASE_URL)
        count = save_cookies(driver, config.cookie_path)
        print(f"\n✅ 쿠키 {count}개를 {config.cookie_path.name} 에 저장했습니다.")
        print("   이제 `python main.py` 가 쿠키로 자동 로그인합니다.")
        return 0
    except (RuntimeError, KeyboardInterrupt) as error:
        logger.error("쿠키 저장 실패: %s", error)
        return 1
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
