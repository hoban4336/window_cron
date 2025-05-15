# login.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
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
    prefs = {
        "safebrowsing.enabled": True,                   # Safe Browsing ON
        "safebrowsing.protection_level": 1              # 1 = 표준, 2 = 향상된 보호
    }
    options.add_experimental_option("prefs", prefs)

    options.add_argument("--disable-features=PasswordLeakDetection")
    options.add_argument("--disable-features=SafeBrowsingEnhancedProtection")

    # 기타 옵션
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://ehr.visang.com")

    # 로그인 수행
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, ID_INPUT_ID))).send_keys(USERNAME)
    driver.find_element(By.ID, ID_INPUT_PW).send_keys(PASSWORD)
    driver.find_element(By.ID, ID_BTN_LOGIN).click()

    # 로그인 후 다음 페이지 로딩 대기
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tamInfo")))

    return driver
