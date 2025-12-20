# login.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from dotenv import load_dotenv
from pathlib import Path
import os

def login():

    load_dotenv(dotenv_path=Path(".env"))
    load_dotenv(dotenv_path=Path(".env.private"), override=True)

    USERNAME = os.getenv("VISANG_USERNAME")
    PASSWORD = os.getenv("VISANG_PASSWORD")

    ID_INPUT_ID = os.getenv("SELECTOR_INPUT_ID")
    ID_INPUT_PW = os.getenv("SELECTOR_INPUT_PW")
    ID_BTN_LOGIN = os.getenv("SELECTOR_BTN_LOGIN")

    options = webdriver.ChromeOptions()
    # 크롬 자동화 티 내지 않기(선택)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,  # 사이트 알림 차단                 
    }
    options.add_experimental_option("prefs", prefs)

    # "safebrowsing.enabled": True,                   # Safe Browsing ON
    # "safebrowsing.protection_level": 1              # 1 = 표준, 2 = 향상된 보호

    options.add_argument("--disable-features=PasswordManagerOnboarding,PasswordLeakDetection,NotificationTriggers,AutofillServerCommunication")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-save-password-bubble")
    
    # 기타 옵션
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")

    options.set_capability("unhandledPromptBehavior", "accept")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://ehr.visang.com")

    # 로그인 수행
    import time
    try:
        print("[*] 로그인 시도 중...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, ID_INPUT_ID))).send_keys(USERNAME)
        driver.find_element(By.ID, ID_INPUT_PW).send_keys(PASSWORD)
        driver.find_element(By.ID, ID_BTN_LOGIN).click()
        print("[OK] 로그인 버튼 클릭 완료")
    except Exception as e:
        print(f"[ERROR] 로그인 폼 입력 실패: {e}")
        driver.save_screenshot("login_error.png")
        raise

    # 로그인 후 다음 페이지 로딩 대기
    time.sleep(3)

    try:
        # tamInfo 요소 대기
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "tamInfo")))
        print("[OK] 로그인 성공 - 메인 페이지 로드됨")
    except Exception as e:
        print(f"[WARN] tamInfo 요소를 찾을 수 없음. 다른 방법으로 확인 중...")
        try:
            current_url = driver.current_url
            print(f"현재 URL: {current_url}")
            print(f"페이지 제목: {driver.title}")
            
            driver.save_screenshot("after_login.png")
            print("[INFO] 로그인 후 스크린샷 저장됨: after_login.png")
            
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("[OK] 페이지 로드 완료 (tamInfo 없이 진행)")
        except Exception as e2:
            print(f"[ERROR] 로그인 후 페이지 로드 실패: {e2}")
            driver.save_screenshot("login_failed.png")
            raise

    return driver
