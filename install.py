# exec.py
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"

# requirements 설치 함수
def install_requirements():
    try:
        import selenium
        import dotenv
        import webdriver_manager
    except ImportError:
        print("🔧 Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])

install_requirements()

# ✅ 오늘이 주말이면 종료
today = datetime.today()
if today.weekday() >= 5:  # 5 = 토요일, 6 = 일요일
    print("📅 주말(토/일)은 실행하지 않습니다.")
    sys.exit(0)

from holiday_checker import today_holiday, today_leave, safe_print

holiday_name = today_holiday()
if holiday_name:
    safe_print("📅 공휴일({})은 실행하지 않습니다.".format(holiday_name))
    sys.exit(0)

leave_name = today_leave()
if leave_name:
    safe_print("📅 연차({})은 실행하지 않습니다.".format(leave_name))
    sys.exit(0)

from login import login
from check_work import check_and_click_work

from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.common.exceptions import WebDriverException
import time

def smash_browser_warning(driver):
    """크롬 보안/비밀번호 경고 같은 브라우저 UI를 키로 닫는다."""
    try:
        ActionChains(driver).pause(0.1).send_keys(Keys.ENTER).perform()
        time.sleep(0.2)
        ActionChains(driver).pause(0.1).send_keys(Keys.ESCAPE).perform()
    except WebDriverException:
        pass

driver = login()
smash_browser_warning(driver)
check_and_click_work(driver)

# print("⏳ 10분 대기 중...")
# time.sleep(600)

driver.quit()
