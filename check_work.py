from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import ElementClickInterceptedException

from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import time
import os
import re

BASE_DIR = Path(__file__).resolve().parent

# .env 불러오기
load_dotenv(dotenv_path=BASE_DIR / ".env")
load_dotenv(dotenv_path=BASE_DIR / ".env.private", override=True)

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
    folder = BASE_DIR / "screenshots"
    folder.mkdir(exist_ok=True)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filepath = folder / f"{timestamp}_{filename_prefix}.png"
    driver.save_screenshot(str(filepath))
    print(f"[SCREENSHOT] 스크린샷 저장됨: {filepath}")

def dispatch_custom_click(driver, element):
    """JavaScript로 커스텀 클릭 이벤트 발생"""
    driver.execute_script("""
        var event = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
        });
        arguments[0].dispatchEvent(event);
    """, element)

def click_accept_popup(driver, retries=3, timeout=3):
    """저장하시겠습니까?(팝업) 버튼"""
    for i in range(retries):
        try:
            WebDriverWait(driver, timeout).until(EC.alert_is_present())
            a = driver.switch_to.alert
            msg = a.text
            a.accept()
            print(f"[OK] Alert 수락: {msg}")
            save_screenshot(driver, "수락")
            return True
        except TimeoutException:
            print(f"[INFO] 확인창 없음 (시도 {i + 1})")
            time.sleep(1)

def click_save_popup(driver, element):
    """다양한 방식으로 클릭 시도"""
    try:
        driver.execute_script("$(arguments[0]).trigger('click');", element)
        click_accept_popup(driver)

    except Exception as e:
        print("[ERROR] 클릭 중 오류:", e)

def click_button(driver, button_id, label):
    """출퇴근 버튼"""
    try :
        clickable_a = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[@id='{button_id}']/parent::a"))
        )
        driver.execute_script("arguments[0].click();", clickable_a)

        time.sleep(1)
        save_screenshot(driver, f"{label}")
        print(f"[OK] {label} 버튼 클릭 성공")
    except Exception as e:
        print(f"[ERROR] {label} 버튼 클릭 실패:", e)

def capture_popup_and_save(driver, label):
    try:
        # iframe 진입
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='dialogframe_']"))
        )
        driver.switch_to.frame(iframe)

        # 저장 버튼 클릭 (정상 click 처리)
        save_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_POPUP_SAVE_BTN))
        )
        print("[SEARCH] 저장 버튼 HTML:", save_button.get_attribute("outerHTML"))
        click_save_popup(driver, save_button)

        # 결과 스크린샷
        time.sleep(2)
        save_screenshot(driver, f"{label}_결과")

        # iframe 빠져나오기
        driver.switch_to.default_content()

    except Exception as e:
        print(f"[ERROR] {label} 저장 실패:", e)

def dismiss_attendance_notice(driver):
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "divMainPop2302010120062000"))
        )
        print("[WARN] 근태 기준 미준수 안내 팝업 감지됨")

        close_button = driver.find_element(By.ID, "layerClose")
        close_button.click()
        print("[OK] 팝업 닫기 성공")
    except:
        print("[INFO] 근태 기준 팝업 없음 (정상 진행)")

def dismiss_password_alert(driver):
    try:
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(text(),'비밀번호 변경')]")
            )
        )
        print("[WARN] 비밀번호 변경 팝업 감지됨 → 확인 클릭 시도")
        confirm_btn = driver.find_element(
            By.XPATH, "//button[contains(text(),'확인')]"
        )
        driver.execute_script("arguments[0].click();", confirm_btn)        
        confirm_btn.click()
        time.sleep(0.5)
        print("[OK] 비밀번호 변경 팝업 닫힘")
    except:
        print("[INFO] 비밀번호 변경 팝업 없음 (정상 진행)")


def dismiss_value_up_modal(driver, max_attempts=3):
    """
    Value-Up 마감 안내 등 마케팅/안내 모달 팝업을 닫습니다.
    여러 전략을 사용하여 X 버튼이나 닫기 버튼을 찾아 클릭합니다.

    Args:
        driver: Selenium WebDriver 인스턴스
        max_attempts: 최대 시도 횟수 (기본값: 3)
    """
    print("[SEARCH] Value-Up 및 마케팅 모달 팝업 확인 중...")

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
                        print(f"   [CLOSE]  모달 닫기 버튼 발견 → 클릭 시도")

                        # 스크롤하여 버튼을 화면에 표시
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        time.sleep(0.3)

                        # 클릭 시도 (일반 클릭 → JavaScript 클릭)
                        try:
                            btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", btn)

                        time.sleep(1)
                        print("   [OK] 모달 팝업 닫기 성공")
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
                print("[OK] 모달 팝업 없음 또는 모두 닫힘")
                break

        except Exception as e:
            print(f"   [INFO]  모달 확인 시도 {attempt + 1}/{max_attempts}: {e}")
            time.sleep(0.5)

    print("[OK] 모달 팝업 처리 완료")


def accept_any_confirm(driver, timeout=3):
    """네이티브 alert/confirm 또는 인페이지 모달의 '확인/예' 버튼까지 처리"""
    # 1) 네이티브 alert 먼저
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        a = driver.switch_to.alert
        msg = a.text
        a.accept()  # [OK] 먼저 닫기 (닫기 전에 스샷 찍지 말기)
        print(f"[OK] Alert 수락: {msg}")
        return True
    except TimeoutException:
        pass

    # 2) 현재 컨텍스트(프레임)에서 인페이지 모달 찾기
    def _accept_in_context(ctx):
        try:
            modal = WebDriverWait(ctx, timeout).until(EC.visibility_of_element_located((
                By.XPATH,
                "//*[contains(normalize-space(),'저장하시겠습니까') or "
                "contains(normalize-space(),'자료를 저장') or "
                "contains(normalize-space(),'저장 하시겠습니까')]/ancestor::*"
                "[@role='dialog' or contains(@class,'modal') or contains(@class,'layer')]"
            )))
            ok = modal.find_element(By.XPATH,
                ".//*[self::button or self::a or self::input]"
                "[normalize-space()='확인' or normalize-space()='예' or "
                "@value='확인' or @value='예' or contains(@class,'confirm')]"
            )
            ok.click()
            return True
        except Exception:
            return False

    # 현재 프레임에서 시도
    if _accept_in_context(driver):
        print("[OK] 인페이지 확인 수락(iframe 내부)")
        return True

    # 최상위 문서에서도 한 번 더 시도 (모달이 body 바로 아래에 붙는 경우)
    driver.switch_to.default_content()
    if _accept_in_context(driver):
        print("[OK] 인페이지 확인 수락(최상위 문서)")
        return True

    print("[INFO] 확인창(네이티브/인페이지) 없음")
    return False

def save_inside_popup(driver, *, label=None, timeout=10):
    """보이는 dialogframe_*에 진입 → 저장 클릭 → 확인 수락 → 팝업 닫힘 대기"""
    # 보이는 팝업 iframe 선택
    def visible_frames(d):
        return [f for f in d.find_elements(By.CSS_SELECTOR, "iframe[id^='dialogframe_']") if f.is_displayed()]

    WebDriverWait(driver, timeout).until(lambda d: len(visible_frames(d)) > 0)
    iframe_el = visible_frames(driver)[-1]
    WebDriverWait(driver, timeout).until(EC.frame_to_be_available_and_switch_to_it(iframe_el))

    # 저장 버튼
    save_btn = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((
        By.XPATH, "//input[@type='button' and (@value='저장' or contains(@class,'save') or @ba_type='WRITE')]"
    )))
    print("[SEARCH] 저장 버튼 HTML:", save_btn.get_attribute("outerHTML"))

    # 클릭 시퀀스 (사용자 제스처 + JS 백업)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save_btn)
    try:
        ActionChains(driver).move_to_element(save_btn).pause(0.05).click().perform()
    except UnexpectedAlertPresentException:
        print("[INFO] Alert appeared during ActionChains click, handling it now")
        pass
    except Exception:
        pass
    
    try:
        driver.execute_script("""
          var el=arguments[0];
          el.focus();
          ['mousedown','mouseup','click'].forEach(t=>{
            el.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window}));
          });
          if (typeof el.onclick === 'function') { el.onclick(); }  // doAction 직접 호출 백업
        """, save_btn)
    except UnexpectedAlertPresentException:
        print("[INFO] Alert appeared during JS click, handling it now")
        pass

    # 확인(네이티브/인페이지) 수락
    time.sleep(0.5)  # Give alert time to appear
    accepted = accept_any_confirm(driver, timeout=3)

    # 기본 컨텍스트 복귀 + 해당 팝업 닫힘/숨김 대기
    driver.switch_to.default_content()
    try:
        WebDriverWait(driver, timeout).until(EC.staleness_of(iframe_el))
    except TimeoutException:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, f"#{iframe_el.get_attribute('id')}"))
        )

    if label:
        try: save_screenshot(driver, f"{label}_저장완료")
        except: pass
    print("[OK] 팝업 저장 완료 (확인 처리: {})".format("됨" if accepted else "없음"))

def check_and_click_work(driver):

    now = datetime.now()
    current_hour = now.hour

    should_click_sta = START_HOUR_MIN <= current_hour < START_HOUR_MAX
    should_click_end = END_HOUR_MIN <= current_hour < END_HOUR_MAX

    time.sleep(10) # 가끔 시간을 못읽을 때가 있음. (비동기 로딩이라 그런듯)
    in_time = get_time_text(driver, SELECTOR_IN_TIME)
    out_time = get_time_text(driver, SELECTOR_OUT_TIME)

    print(f"출근 시각: {in_time}, 퇴근 시각: {out_time}")

    try:
        dismiss_password_alert(driver)          # 비밀번호 변경 팝업 처리
        dismiss_attendance_notice(driver)       # 근태 기준 미준수 팝업 처리
        dismiss_value_up_modal(driver)          # Value-Up 모달 팝업 처리
        

        if should_click_sta and not is_time(in_time):
            print("[ALERT] 출근 시간 조건 만족 → 출근 시도")
            click_button(driver, SELECTOR_BTN_STA, "출근")
            time.sleep(2)
            # capture_popup_and_save(driver, "출근")
            save_inside_popup(driver, label="출근")
        elif should_click_end and is_time(in_time) and not is_time(out_time):
            print("[ALERT] 퇴근 시간 조건 만족 → 퇴근 시도")
            click_button(driver, SELECTOR_BTN_END, "퇴근")
            time.sleep(2)            
            capture_popup_and_save(driver, "퇴근")
        else:
            print("[OK]  조건 불충족 또는 이미 완료됨")
    except Exception as e:
        print("[ERROR] 버튼 클릭 중 오류:", e)
