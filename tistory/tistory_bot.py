"""티스토리 자동 로그인 + 글쓰기 + 발행 핵심 로직.

⚠️ 셀렉터 주의:
티스토리/카카오 페이지 구조는 수시로 바뀐다. 동작이 안 되면
브라우저 개발자도구로 실제 셀렉터를 확인해 상수만 교체하면 된다.
(아래 SELECTORS 딕셔너리에 모아 두었다.)
"""

import logging
import time
from pathlib import Path

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import Config
from cookie_store import load_cookies
from post_reader import Post

logger = logging.getLogger(__name__)

# 변경되기 쉬운 셀렉터는 한곳에 모아 둔다.
SELECTORS = {
    "kakao_login_link": (By.CSS_SELECTOR, "a.btn_login.link_kakao_id"),
    "kakao_id": (By.CSS_SELECTOR, "input[name='loginId']"),
    "kakao_pw": (By.CSS_SELECTOR, "input[name='password']"),
    "kakao_submit": (By.CSS_SELECTOR, "button.btn_g.highlight.submit"),
    "editor_iframe": (By.CSS_SELECTOR, "iframe#editor-tistory_ifr"),
    "title_input": (By.CSS_SELECTOR, "textarea#post-title-inp"),
    "publish_layer_btn": (By.CSS_SELECTOR, "button#publish-layer-btn"),
    "publish_btn": (By.CSS_SELECTOR, "button#publish-btn"),
}

LOGIN_URL = "https://www.tistory.com/auth/login"
WAIT_SECONDS = 20


class TistoryBot:
    """드라이버를 받아 티스토리 작업을 수행한다.

    상태(로그인 여부 등)는 외부에서 변경하지 않고 메서드 호출로만 다룬다.
    """

    def __init__(self, driver, config: Config):
        self._driver = driver
        self._config = config
        self._wait = WebDriverWait(driver, WAIT_SECONDS)

    def _click(self, key: str) -> None:
        element = self._wait.until(EC.element_to_be_clickable(SELECTORS[key]))
        element.click()

    def _type(self, key: str, value: str) -> None:
        element = self._wait.until(EC.visibility_of_element_located(SELECTORS[key]))
        element.clear()
        element.send_keys(value)

    def is_logged_in(self) -> bool:
        """글쓰기 관리 페이지 접근 시 로그인 페이지로 튕기지 않는지로 판정한다."""
        manage_url = f"https://{self._config.blog_name}.tistory.com/manage/posts/"
        self._driver.get(manage_url)
        current = self._driver.current_url
        return "auth/login" not in current and "kakao.com" not in current

    def login_with_cookies(self, cookie_path: Path) -> None:
        """저장된 쿠키로 로그인 상태를 복원한다. 무효하면 예외를 던진다."""
        load_cookies(self._driver, cookie_path)
        if not self.is_logged_in():
            raise RuntimeError(
                "쿠키가 만료되었거나 무효합니다. `python save_cookies.py` 로 다시 저장하세요."
            )
        logger.info("쿠키로 로그인 복원 성공")

    def login(self) -> None:
        """카카오 계정으로 티스토리에 로그인한다(비밀번호 방식)."""
        if not self._config.tistory_id or not self._config.tistory_pw:
            raise RuntimeError(
                "TISTORY_ID/PW 가 없어 비밀번호 로그인이 불가합니다. "
                "쿠키 방식을 쓰려면 `python save_cookies.py` 를 먼저 실행하세요."
            )
        try:
            self._driver.get(LOGIN_URL)
            self._click("kakao_login_link")
            self._type("kakao_id", self._config.tistory_id)
            self._type("kakao_pw", self._config.tistory_pw)
            self._click("kakao_submit")
            # 로그인 후 메인으로 리다이렉트될 때까지 대기
            self._wait.until(EC.url_contains("tistory.com"))
            logger.info("로그인 성공")
        except TimeoutException:
            raise RuntimeError(
                "로그인 실패(시간 초과). 캡차가 떴거나 셀렉터가 변경됐을 수 있습니다. "
                "HEADLESS=false 로 직접 확인하거나 쿠키 방식을 사용하세요."
            )

    def ensure_logged_in(self, cookie_path: Path) -> None:
        """쿠키 로그인을 우선 시도하고, 실패하면 비밀번호 로그인으로 폴백한다."""
        try:
            self.login_with_cookies(cookie_path)
            return
        except (FileNotFoundError, RuntimeError) as error:
            logger.warning("쿠키 로그인 실패 → 비밀번호 로그인 시도: %s", error)
        self.login()

    def _open_editor(self) -> None:
        url = f"https://{self._config.blog_name}.tistory.com/manage/newpost/"
        self._driver.get(url)
        self._dismiss_draft_popup()

    def _dismiss_draft_popup(self) -> None:
        """'작성 중인 글 이어쓰기' 팝업이 뜨면 취소한다."""
        try:
            cancel = WebDriverWait(self._driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-default.cancel"))
            )
            cancel.click()
            logger.info("임시저장 팝업 닫음")
        except TimeoutException:
            pass  # 팝업이 없으면 정상

    def _fill_body(self, body: str) -> None:
        """에디터 iframe 으로 전환해 본문을 입력한 뒤 기본 프레임으로 복귀한다."""
        try:
            iframe = self._wait.until(
                EC.presence_of_element_located(SELECTORS["editor_iframe"])
            )
            self._driver.switch_to.frame(iframe)
            editor_body = self._wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            editor_body.click()
            editor_body.send_keys(body)
        except (TimeoutException, NoSuchElementException) as error:
            raise RuntimeError(f"본문 입력 실패(iframe/셀렉터 확인 필요): {error}")
        finally:
            self._driver.switch_to.default_content()

    def publish(self, post: Post) -> None:
        """글 하나를 작성하고 발행한다."""
        self._open_editor()
        self._type("title_input", post.title)
        self._fill_body(post.body)

        # 발행 옵션 레이어 열기 -> 최종 발행
        self._click("publish_layer_btn")
        # TODO: 공개설정/카테고리/태그를 visibility 값에 맞춰 선택하는 로직 추가 지점
        self._click("publish_btn")
        logger.info("발행 완료: %s", post.title)

    def publish_all(self, posts: list[Post], on_done) -> int:
        """여러 글을 발행 간격을 지키며 순서대로 올린다. 성공 개수를 반환한다."""
        published = 0
        for index, post in enumerate(posts):
            try:
                self.publish(post)
                on_done(post)
                published += 1
            except RuntimeError as error:
                logger.error("발행 건너뜀 (%s): %s", post.title, error)
                continue

            is_last = index == len(posts) - 1
            if not is_last and self._config.post_delay_seconds > 0:
                logger.info("%d초 대기 후 다음 글", self._config.post_delay_seconds)
                time.sleep(self._config.post_delay_seconds)

        return published
