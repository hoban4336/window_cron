from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import time
import os
import re

# .env 불러오기
load_dotenv(dotenv_path=Path(".env"))
load_dotenv(dotenv_path=Path(".env.private"), override=True)

SELECTOR_IN_TIME = os.getenv("SELECTOR_IN_TIME")
SELECTOR_OUT_TIME = os.getenv("SELECTOR_OUT_TIME")
SELECTOR_BTN_STA = os.getenv("SELECTOR_BTN_STA")
SELECTOR_BTN_END = os.getenv("SELECTOR_BTN_END")
SELECTOR_POPUP_SAVE_BTN = os.getenv("SELECTOR_POPUP_SAVE_BTN")

START_HOUR_MIN = int(os.getenv("START_HOUR_MIN", 8))
START_HOUR_MAX = int(os.getenv("START_HOUR_MAX", 10))
END_HOUR_MIN = int(os.getenv("END_HOUR_MIN", 18))
END_HOUR_MAX = int(os.getenv("END_HOUR_MAX", 22))

def is_time(value):
    return bool(re.match(r"^\d{2}:\d{2}$", value))

def get_time_text(driver, element_id):
    try:
        el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, element_id)))
        return el.text.strip()
    except Exception:
        return ""

def save_screenshot(driver, filename_prefix):
    now = datetime.now()
    folder = Path("screenshots")
    folder.mkdir(exist_ok=True)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filepath = folder / f"{timestamp}_{filename_prefix}.png"
    driver.save_screenshot(str(filepath))
    print(f"📸 스크린샷 저장됨: {filepath}")

def click_button(driver, button_id, label):
    try :
        clickable_a = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[@id='{button_id}']/parent::a"))
        )
        driver.execute_script("arguments[0].click();", clickable_a)

        time.sleep(1)
        save_screenshot(driver, f"{label}")
        print(f"✅ {label} 버튼 클릭 성공")
    except Exception as e:
        print(f"❌ {label} 버튼 클릭 실패:", e)    

def capture_popup_and_save(driver, label):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTOR_POPUP_SAVE_BTN))
        )
        driver.find_element(By.CSS_SELECTOR, SELECTOR_POPUP_SAVE_BTN).click()

        time.sleep(1)
        save_screenshot(driver, f"{label}_결과")
    except Exception as e:
        print(f"❌ {label} 저장 실패:", e)

def check_and_click_work(driver):

    now = datetime.now()
    current_hour = now.hour

    should_click_sta = START_HOUR_MIN <= current_hour < START_HOUR_MAX
    should_click_end = END_HOUR_MIN <= current_hour < END_HOUR_MAX

    in_time = get_time_text(driver, SELECTOR_IN_TIME)
    out_time = get_time_text(driver, SELECTOR_OUT_TIME)

    print(f"출근 시각: {in_time}, 퇴근 시각: {out_time}")

    try:
        if should_click_sta and not is_time(in_time):
            print("🔔 출근 시간 조건 만족 → 출근 시도")
            click_button(driver, SELECTOR_BTN_STA, "출근")
            time.sleep(2)
            capture_popup_and_save(driver, "출근")
        elif should_click_end and is_time(in_time) and not is_time(out_time):
            print("🔔 퇴근 시간 조건 만족 → 퇴근 시도")
            click_button(driver, SELECTOR_BTN_END, "퇴근")
            time.sleep(2)            
            capture_popup_and_save(driver, "퇴근")
        else:
            print("✅  조건 불충족 또는 이미 완료됨")
    except Exception as e:
        print("❌ 버튼 클릭 중 오류:", e)