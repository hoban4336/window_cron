# login.py
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = Path(__file__).resolve().parent
LOGIN_URL = "https://ehr.visang.com/"
LOGIN_PAGE_RETRIES = 3


def load_environment():
    load_dotenv(dotenv_path=BASE_DIR / ".env")
    load_dotenv(dotenv_path=BASE_DIR / ".env.private", override=True)


def require_env(name):
    value = os.getenv(name)
    if value:
        return value
    raise RuntimeError(
        f"필수 환경변수 `{name}` 를 찾지 못했습니다. "
        f"`{BASE_DIR}` 폴더의 `.env` / `.env.private` 파일을 확인하세요."
    )


def open_login_page(driver):
    last_title = ""
    for attempt in range(1, LOGIN_PAGE_RETRIES + 1):
        driver.get(LOGIN_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        last_title = (driver.title or "").strip()
        page_source = driver.page_source or ""
        if "502 Bad Gateway" not in page_source and "bad gateway" not in last_title.lower():
            return

        print(f"[WARN] 로그인 페이지 응답이 비정상입니다 ({attempt}/{LOGIN_PAGE_RETRIES}) - {last_title}")
        if attempt < LOGIN_PAGE_RETRIES:
            time.sleep(2)

    raise RuntimeError(f"로그인 페이지를 열지 못했습니다: {last_title or '응답 없음'}")


def login():
    load_environment()

    username = require_env("VISANG_USERNAME")
    password = require_env("VISANG_PASSWORD")
    input_id = require_env("SELECTOR_INPUT_ID")
    input_pw = require_env("SELECTOR_INPUT_PW")
    login_button = require_env("SELECTOR_BTN_LOGIN")

    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--disable-features=PasswordManagerOnboarding,PasswordLeakDetection,NotificationTriggers,AutofillServerCommunication")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    options.set_capability("unhandledPromptBehavior", "accept")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    open_login_page(driver)

    try:
        print("[*] 로그인 시도 중...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, input_id))
        ).send_keys(username)
        driver.find_element(By.ID, input_pw).send_keys(password)
        driver.find_element(By.ID, login_button).click()
        print("[OK] 로그인 버튼 클릭 완료")
    except Exception as e:
        print(f"[ERROR] 로그인 폼 입력 실패: {e}")
        driver.save_screenshot(str(BASE_DIR / "login_error.png"))
        raise

    time.sleep(3)

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "tamInfo")))
        print("[OK] 로그인 성공 - 메인 페이지 로드 완료")
    except Exception:
        print("[WARN] `tamInfo` 요소를 찾지 못했습니다. 대체 방식으로 로그인 상태를 확인합니다.")
        try:
            print(f"[INFO] 현재 URL: {driver.current_url}")
            print(f"[INFO] 페이지 제목: {driver.title}")
            driver.save_screenshot(str(BASE_DIR / "after_login.png"))
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("[OK] 페이지 본문 로드 확인")
        except Exception as e:
            print(f"[ERROR] 로그인 후 페이지 로드 실패: {e}")
            driver.save_screenshot(str(BASE_DIR / "login_failed.png"))
            raise

    return driver
