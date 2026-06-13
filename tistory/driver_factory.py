"""Selenium 크롬 드라이버 생성.

webdriver-manager 로 드라이버 바이너리를 자동 관리하고,
자동화 탐지를 줄이기 위한 기본 옵션을 적용한다.
"""

import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


def create_driver(headless: bool) -> webdriver.Chrome:
    """설정된 크롬 드라이버를 반환한다."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1280,1000")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=ko-KR")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as error:
        logger.error("크롬 드라이버 생성 실패: %s", error)
        raise RuntimeError("크롬 드라이버를 시작할 수 없습니다. 크롬 설치 여부를 확인하세요.")

    # navigator.webdriver 흔적 제거
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver
