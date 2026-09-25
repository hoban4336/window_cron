# holiday_checker.py
"""공휴일·연차 ICS를 조회해 오늘 출퇴근 체크를 건너뛸지 확인한다."""
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
HOLIDAY_CACHE_FILE = BASE_DIR / ".holiday_cache.ics"
LEAVE_CACHE_FILE = BASE_DIR / ".leave_cache.ics"
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60

DEFAULT_ICS_URL = (
    "https://calendar.google.com/calendar/ical/"
    "ko.south_korea%23holiday%40group.v.calendar.google.com/public/basic.ics"
)


def safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        sys.stdout.buffer.write((message + "\n").encode(encoding, errors="replace"))


def _load_env():
    load_dotenv(dotenv_path=BASE_DIR / ".env")
    load_dotenv(dotenv_path=BASE_DIR / ".env.private", override=True)


def _unfold_ics(text):
    return (
        text.replace("\r\n ", "")
        .replace("\r\n\t", "")
        .replace("\n ", "")
        .replace("\n\t", "")
    )


def _parse_ics_date(raw):
    raw = raw.strip()
    if not raw:
        return None
    if "T" in raw:
        stamp = raw.replace("Z", "")[:15]
        return datetime.strptime(stamp, "%Y%m%dT%H%M%S").date()
    return datetime.strptime(raw[:8], "%Y%m%d").date()


def _event_blocks(ics_text):
    block = []
    in_event = False
    for line in _unfold_ics(ics_text).splitlines():
        if line == "BEGIN:VEVENT":
            in_event = True
            block = []
            continue
        if line == "END:VEVENT":
            if in_event:
                yield block
            in_event = False
            block = []
            continue
        if in_event:
            block.append(line)


def _event_props(lines):
    props = {}
    for line in lines:
        name_params, sep, value = line.partition(":")
        if not sep:
            continue
        name = name_params.split(";", 1)[0].upper()
        props[name] = value.replace("\\n", "\n")
    return props


def _event_title(props):
    return props.get("SUMMARY", "").replace("\\", "")


def _covers_date(props, target):
    start_raw = props.get("DTSTART", "")
    start = _parse_ics_date(start_raw)
    if start is None:
        return False
    end_raw = props.get("DTEND")
    date_only = "T" not in start_raw
    if not end_raw:
        return start == target
    end = _parse_ics_date(end_raw)
    if end is None:
        return False
    if date_only:
        return start <= target < end
    end_is_midnight = "T000000" in end_raw.replace("Z", "")
    last = end - timedelta(days=1) if end_is_midnight and end > start else end
    return start <= target <= last


def _is_cancelled(props):
    return props.get("STATUS", "").upper() == "CANCELLED"


def _is_public_holiday(props, skip_mode):
    if skip_mode == "all":
        return True
    description = props.get("DESCRIPTION", "")
    return "공휴일" in description.split("\n", 1)[0]


def _is_leave_event(props, keywords):
    title = _event_title(props)
    return any(keyword and keyword in title for keyword in keywords)


def _read_cache(cache_file):
    if not cache_file.exists():
        return None
    age = datetime.now().timestamp() - cache_file.stat().st_mtime
    if age > CACHE_MAX_AGE_SECONDS:
        return None
    return cache_file.read_text(encoding="utf-8")


def _write_cache(cache_file, text):
    cache_file.write_text(text, encoding="utf-8")


def _fetch_ics(url, cache_file, label):
    cached = _read_cache(cache_file)
    if cached:
        return cached

    request = Request(
        url,
        headers={"User-Agent": "window_cron-holiday-check/1.0"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            text = response.read().decode("utf-8")
        _write_cache(cache_file, text)
        return text
    except (URLError, TimeoutError, OSError) as exc:
        if cache_file.exists():
            safe_print("⚠️ {} 조회 실패, 캐시를 사용합니다: {}".format(label, exc))
            return cache_file.read_text(encoding="utf-8")
        safe_print("⚠️ {} 조회 실패, 출퇴근 체크를 계속합니다: {}".format(label, exc))
        return None


def today_holiday(target_date=None):
    """오늘이 공휴일이면 일정 제목을 반환하고, 아니면 None."""
    _load_env()
    skip_mode = os.getenv("HOLIDAY_SKIP_MODE", "public").strip().lower()
    url = os.getenv("HOLIDAY_ICS_URL", DEFAULT_ICS_URL).strip() or DEFAULT_ICS_URL
    target = target_date or date.today()

    ics_text = _fetch_ics(url, HOLIDAY_CACHE_FILE, "공휴일 캘린더")
    if not ics_text:
        return None

    for lines in _event_blocks(ics_text):
        props = _event_props(lines)
        if _is_cancelled(props) or not _covers_date(props, target):
            continue
        if not _is_public_holiday(props, skip_mode):
            continue
        return _event_title(props) or "공휴일"
    return None


def today_leave(target_date=None):
    """오늘 제목에 '연차'가 있는 일정이 있으면 그 제목을 반환한다."""
    _load_env()
    url = os.getenv("LEAVE_ICS_URL", "").strip()
    if not url:
        return None

    keywords = [
        item.strip()
        for item in os.getenv("LEAVE_KEYWORDS", "연차").split(",")
        if item.strip()
    ]
    target = target_date or date.today()

    ics_text = _fetch_ics(url, LEAVE_CACHE_FILE, "연차 캘린더")
    if not ics_text:
        return None

    for lines in _event_blocks(ics_text):
        props = _event_props(lines)
        if _is_cancelled(props) or not _covers_date(props, target):
            continue
        if _is_leave_event(props, keywords):
            return _event_title(props) or "연차"
    return None


if __name__ == "__main__":
    today = date.today().isoformat()
    holiday_name = today_holiday()
    leave_name = today_leave()
    if holiday_name:
        safe_print("📅 {} 은(는) 공휴일입니다: {}".format(today, holiday_name))
    else:
        safe_print("📅 {} 은(는) 공휴일이 아닙니다.".format(today))
    if not os.getenv("LEAVE_ICS_URL", "").strip():
        safe_print("📅 LEAVE_ICS_URL 이 없어 연차 캘린더는 확인하지 않습니다.")
    elif leave_name:
        safe_print("📅 {} 은(는) 연차입니다: {}".format(today, leave_name))
    else:
        safe_print("📅 {} 은(는) 연차가 아닙니다.".format(today))
