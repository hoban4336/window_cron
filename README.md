# Visang EHR Auto Clock-In Script

자동으로 Visang EHR 시스템에 출퇴근을 체크하는 Python Selenium 스크립트입니다.

## 📋 Requirements

- Python 3.7+
- Chrome Browser
- Required Python packages (자동 설치됨):
  - selenium
  - webdriver-manager
  - python-dotenv

## 🚀 Quick Start

### 1. Python 설치 (Windows)
```bash
choco install python --force
```

### 2. 저장소 설정
```bash
git clone <repository-url>
cd window_cron
```

### 3. 로그인 정보 설정
`.env.private` 파일 생성:
```env
VISANG_USERNAME=your_username
VISANG_PASSWORD=your_password
```

### 4. 실행
```bash
python install.py
```

의존성(requirements.txt)은 자동으로 설치됩니다.

## 📁 Project Structure

```
window_cron/
├── install.py              # 메인 실행 파일
├── login.py                # 로그인 처리
├── check_work.py           # 출퇴근 체크 로직 + 팝업 처리
├── popup_handler.py        # Value-Up 모달 팝업 처리 유틸리티
├── .env                    # 기본 설정
├── .env.private            # 개인 로그인 정보 (gitignore)
├── requirements.txt        # Python 의존성
└── screenshots/            # 스크린샷 저장 (자동 생성)
```

## 🎯 Features

### 1. 자동 로그인
- Chrome WebDriver 자동 설정
- Visang EHR 로그인 자동화

### 2. 스마트 팝업 처리 ✨ NEW!
로그인 후 나타나는 다양한 팝업을 자동으로 처리합니다:

#### **Value-Up 마케팅 모달** (새로 추가!)
- 여러 전략으로 닫기 버튼 자동 탐색:
  - Value-Up 텍스트로 찾기
  - close 클래스명으로 찾기
  - "닫기", "×" 텍스트로 찾기
  - "다시 보지 않기" 주변 버튼 찾기
- 최대 3회 재시도
- 다중 팝업 연속 처리

#### **기타 팝업**
- 비밀번호 변경 안내 팝업
- 근태 기준 미준수 안내 팝업

### 3. 자동 출퇴근 체크
시간대별 자동 출퇴근:
- **출근**: 8시~12시 사이 실행 시 자동 출근
- **퇴근**: 18시~22시 사이 실행 시 자동 퇴근

전체 프로세스:
1. 출근/퇴근 버튼 클릭
2. 팝업 iframe 진입
3. "저장" 버튼 클릭
4. "자료를 저장하시겠습니까?" 확인 다이얼로그 처리
5. 스크린샷 자동 저장

### 4. 스크린샷 기록
- 모든 주요 단계에서 자동 저장
- `screenshots/` 폴더에 타임스탬프와 함께 저장
- 디버깅 및 로그 확인에 유용

## ⚙️ Configuration

`.env` 파일에서 설정 변경 가능:

```env
# 출퇴근 시간 범위
START_HOUR_MIN=8    # 출근 시작 시간
START_HOUR_MAX=12   # 출근 종료 시간
END_HOUR_MIN=18     # 퇴근 시작 시간
END_HOUR_MAX=22     # 퇴근 종료 시간

# UI 셀렉터 (사이트 변경 시 수정)
SELECTOR_BTN_STA=S_WORK_STA_BTN
SELECTOR_BTN_END=S_WORK_END_BTN
# ... 등
```

## 🔧 Automation Setup

### Windows Task Scheduler
1. Task Scheduler 열기
2. "Create Basic Task" 선택
3. Trigger: 매일 오전 9시, 오후 6시
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `install.py`
   - Start in: `C:\Users\...\window_cron`

### Linux Cron
```bash
# crontab -e
0 9 * * 1-5 cd /path/to/window_cron && python install.py
0 18 * * 1-5 cd /path/to/window_cron && python install.py
```

## 🐛 Debugging

### 스크린샷 확인
`screenshots/` 폴더의 이미지로 실행 과정 확인

### 로그 메시지
- 🔍 검색/확인 중
- ✅ 성공
- ❌ 실패
- ⚠️ 경고

### 브라우저 표시
`login.py`에서 headless 옵션 비활성화하여 브라우저 동작 직접 확인 가능

## 🔒 Security

- `.env.private`는 gitignore 처리되어 저장소에 업로드되지 않음
- 로그인 정보는 절대 코드에 하드코딩하지 말 것
- 스크린샷 공유 시 개인정보 주의

## 📝 Changelog

### v2.0 (2025-12-20)
- ✨ Value-Up 모달 팝업 자동 처리 기능 추가
- 🔧 다중 전략 팝업 탐색 시스템 구현
- 📦 popup_handler.py 모듈 분리
- 📚 상세 문서화

### v1.0
- 기본 출퇴근 자동화 기능
- iframe 팝업 처리
- 스크린샷 저장

---

**Note**: Visang EHR UI 변경 시 `.env`의 셀렉터 업데이트 필요