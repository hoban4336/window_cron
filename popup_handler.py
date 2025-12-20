"""
popup_handler.py
================
추가적인 팝업 처리 함수들을 포함합니다.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def dismiss_value_up_modal(driver, max_attempts=3):
    """
    Value-Up 마감 안내 등 마케팅/안내 모달 팝업을 닫습니다.
    여러 전략을 사용하여 X 버튼이나 닫기 버튼을 찾아 클릭합니다.

    Args:
        driver: Selenium WebDriver 인스턴스
        max_attempts: 최대 시도 횟수 (기본값: 3)
    """
    print("🔍 Value-Up 및 마케팅 모달 팝업 확인 중...")

    for attempt in range(max_attempts):
        try:
            # 전략 1: Value-Up 안내 모달의 X 버튼 찾기
            close_buttons = driver.find_elements(By.XPATH,
                "//div[contains(text(), 'Value-Up') or contains(text(), '안내')]"
                "/ancestor::*[contains(@class, 'modal') or contains(@class, 'popup') or contains(@class, 'layer')]"
                "//button[contains(@class, 'close') or @aria-label='Close' or contains(@title, '닫기')]"
            )

            # 전략 2: 일반적인 모달 닫기 버튼 (X 모양 버튼들)
            if not close_buttons:
                close_buttons = driver.find_elements(By.CSS_SELECTOR,
                    "button.close, button[class*='close'], button[class*='Close'], "
                    "a.close, a[class*='close'], span.close, span[class*='close'], "
                    "div[class*='close-btn'], button[aria-label='Close']"
                )

            # 전략 3: XPath로 "닫기", "확인", "X" 텍스트 버튼 찾기
            if not close_buttons:
                close_buttons = driver.find_elements(By.XPATH,
                    "//button[contains(text(), '닫기')] | "
                    "//button[contains(text(), '확인')] | "
                    "//a[contains(text(), '닫기')] | "
                    "//button[text()='×'] | "
                    "//button[text()='✕']"
                )

            # 전략 4: "다시 보지 않기" 체크박스와 함께 있는 닫기 버튼
            if not close_buttons:
                close_buttons = driver.find_elements(By.XPATH,
                    "//*[contains(text(), '다시 보지 않기')]"
                    "/ancestor::*[contains(@class, 'modal') or contains(@class, 'popup')]"
                    "//button | "
                    "//*[contains(text(), '다시 보지 않기')]"
                    "/following::button[1]"
                )

            # 보이는 버튼 중 하나를 클릭
            clicked = False
            for btn in close_buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print(f"   ✖️  모달 닫기 버튼 발견 → 클릭 시도")

                        # 스크롤하여 버튼을 화면에 표시
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        time.sleep(0.3)

                        # 클릭 시도 (일반 클릭 → JavaScript 클릭)
                        try:
                            btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", btn)

                        time.sleep(1)
                        print("   ✅ 모달 팝업 닫기 성공")
                        clicked = True
                        break
                except Exception as e:
                    continue

            if clicked:
                # 닫은 후 추가 팝업이 있을 수 있으므로 다시 확인
                time.sleep(0.5)
                continue
            else:
                # 더 이상 닫을 팝업이 없음
                print("✅ 모달 팝업 없음 또는 모두 닫힘")
                break

        except Exception as e:
            print(f"   ℹ️  모달 확인 시도 {attempt + 1}/{max_attempts}: {e}")
            time.sleep(0.5)

    print("✅ 모달 팝업 처리 완료")
