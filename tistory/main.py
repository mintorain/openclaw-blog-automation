"""진입점: 설정 로드 -> 글 읽기 -> 로그인 -> 발행 -> 정리.

실행:
    python main.py
"""

import logging
import sys
from pathlib import Path

from config import load_config
from driver_factory import create_driver
from post_reader import load_posts, mark_done
from tistory_bot import TistoryBot

LOG_DIR = Path(__file__).parent / "logs"


def _setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "tistory.log", encoding="utf-8"),
        ],
    )


def main() -> int:
    _setup_logging()
    logger = logging.getLogger("main")

    try:
        config = load_config()
    except ValueError as error:
        logger.error("설정 오류: %s", error)
        return 1

    posts = load_posts(limit=config.max_posts_per_run)
    if not posts:
        logger.info("발행할 글이 없습니다. posts/*.md 를 확인하세요.")
        return 0

    logger.info("발행 대상 %d개", len(posts))

    driver = None
    try:
        driver = create_driver(headless=config.headless)
        bot = TistoryBot(driver, config)
        # 쿠키 우선 → 실패 시 비밀번호 로그인 폴백
        bot.ensure_logged_in(config.cookie_path)
        count = bot.publish_all(posts, on_done=mark_done)
        logger.info("총 %d개 발행 완료", count)
        return 0
    except RuntimeError as error:
        logger.error("실행 실패: %s", error)
        return 1
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
