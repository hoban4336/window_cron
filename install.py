# exec.py
import subprocess
import sys
import time

# requirements 설치 함수
def install_requirements():
    try:
        import selenium
        import dotenv
    except ImportError:
        print("🔧 Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

install_requirements()

from login import login
from check_work import check_and_click_work

driver = login()
check_and_click_work(driver)

# print("⏳ 10분 대기 중...")
# time.sleep(600)

driver.quit()
