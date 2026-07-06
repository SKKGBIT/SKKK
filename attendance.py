"""근태 주마감 일정 공지 이미지 자동 생성.

- 대상기간 : 직전 주 월요일 ~ 일요일 (한국 시간 기준)
            (월요일에 발행 → 지난 주가 대상)
- 제출기한 : 발행한 주(이번 주)의 화요일. 단, 그 화요일이 한국 공휴일
            (대체공휴일 포함)이면 공휴일/주말이 끝난 다음 평일로 이동.
"""

import calendar
import os
from datetime import datetime, timedelta, timezone

import holidays
from PIL import Image, ImageDraw, ImageFont

# ── 이미지 위 텍스트를 덮을 영역(흰 배경) 과 그리기 기준점 ────────────────
# (pic.png 분석값. 좌표는 좌상단/우하단)
PERIOD_BOX = (553, 566, 1035, 618)      # 대상기간 날짜 덮을 영역(콜론 x≈545~549 보존)
DEADLINE_BOX = (645, 722, 905, 774)     # 제출기한 날짜 덮을 영역(콜론 x≈615~629 보존)
PERIOD_LEFT = 566                        # 대상기간 날짜 시작 x
DEADLINE_LEFT = 648                      # 제출기한 날짜 시작 x
PERIOD_TARGET_W = 455                    # 원본 대상기간 날짜 너비(px)
DEADLINE_TARGET_W = 244                  # 원본 제출기한 날짜 너비(px)

BG_COLOR = (254, 254, 253)               # 카드 배경(흰색)
PERIOD_COLOR = (31, 42, 68)              # 대상기간: 어두운 네이비
DEADLINE_COLOR = (0, 112, 192)           # 제출기한: 파란색 #0070C0

KST = timezone(timedelta(hours=9))
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def get_font_path():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        r"C:\Windows\Fonts\malgunbd.ttf",   # 로컬(Windows) 미리보기용
        r"C:\Windows\Fonts\malgun.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("NotoSansCJK font not found")


def fmt(d):
    return f"{d.year}/{d.month:02d}/{d.day:02d}({WEEKDAY_KR[d.weekday()]})"


STATE_FILE = "attendance_state.txt"   # 마지막 대상기간 종료일(ISO)만 한 줄 저장


def last_day_of_month(d):
    """d가 속한 달의 말일."""
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def recent_sunday(today):
    """today 기준 가장 최근 완료된 일요일(= 직전 주 일요일)."""
    return today - timedelta(days=today.weekday() + 1)


def compute_deadline(today):
    """제출기한 = 이번 주 화요일. 공휴일/주말이면 다음 평일로 이동."""
    this_monday = today - timedelta(days=today.weekday())
    kr_holidays = holidays.SouthKorea()
    deadline = this_monday + timedelta(days=1)              # 이번 주 화요일
    while deadline in kr_holidays or deadline.weekday() >= 5:
        deadline += timedelta(days=1)
    return deadline


def read_last_end():
    """마지막으로 마감한 종료일을 상태 파일에서 읽는다(없으면 None)."""
    if os.path.exists(STATE_FILE):
        text = open(STATE_FILE, encoding="utf-8").read().strip()
        if text:
            return datetime.strptime(text, "%Y-%m-%d").date()
    return None


def write_last_end(d):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(d.isoformat())


def compute_period(today, mode, last_end):
    """대상기간(시작, 종료)을 계산. 마지막 마감일 다음 날부터 이어서 잡는다.

    - weekly      : (지난 종료일+1 | 직전 주 월요일) ~ 직전 주 일요일
    - month_end   : (지난 종료일+1 | 직전 주 월요일) ~ 그 달 말일   (조기 마감용)
    - month_start : 오늘이 속한 달 1일 ~ 직전 주 일요일             (다음달 시작용)
    종료 < 시작 이면 아직 마감할 새 기간이 없다는 뜻이라 종료를 None 으로 반환.
    """
    if last_end:
        start = last_end + timedelta(days=1)
    else:
        start = recent_sunday(today) - timedelta(days=6)   # 직전 주 월요일

    if mode == "month_end":
        # 조기 마감: 시작일이 속한 달의 막날까지 (언제 돌리든 항상 막날). 다음은 자동으로 1일부터.
        end = last_day_of_month(start)
    elif mode == "month_start":
        # 다음달 시작: 오늘이 속한 달 1일부터 직전 주 일요일까지.
        start = today.replace(day=1)
        end = recent_sunday(today)
    else:  # weekly
        end = recent_sunday(today)

    if end < start:
        return start, None
    return start, end


def fit_font(font_path, text, target_w):
    """문자열 너비가 target_w 에 맞도록 폰트 크기를 찾는다."""
    size = 50
    font = ImageFont.truetype(font_path, size)
    w = font.getlength(text)
    if w == 0:
        return font
    size = max(8, int(size * target_w / w))
    font = ImageFont.truetype(font_path, size)
    # 미세 보정
    for _ in range(6):
        w = font.getlength(text)
        if abs(w - target_w) <= 2:
            break
        size = max(8, size + (1 if w < target_w else -1))
        font = ImageFont.truetype(font_path, size)
    return font


def draw_field(draw, font_path, text, box, left, target_w, color):
    # 기존 텍스트 덮기
    draw.rectangle(box, fill=BG_COLOR)
    font = fit_font(font_path, text, target_w)
    # 박스 세로 중앙에 정렬
    bbox = font.getbbox(text)
    text_h = bbox[3] - bbox[1]
    cy = (box[1] + box[3]) / 2
    y = cy - text_h / 2 - bbox[1]
    draw.text((left, y), text, fill=color, font=font)


def generate(base_image_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    today = datetime.now(KST).date()
    # MODE: weekly(자동 주간, 기본) / month_end(월말끊기 - 시작일 달의 말일까지 마감)
    mode = (os.environ.get("MODE") or "weekly").strip()

    last_end = read_last_end()
    start, end = compute_period(today, mode, last_end)
    if end is None:
        print("새로 마감할 기간 없음 (시작=%s, 오늘=%s) → 이미지 유지하고 종료" % (start, today))
        return

    # 제출기한: DEADLINE 입력값이 있으면 그대로(조기 마감용), 없으면 자동(이번 주 화요일).
    deadline_input = (os.environ.get("DEADLINE") or "").strip()
    if deadline_input:
        deadline = datetime.strptime(deadline_input, "%Y-%m-%d").date()
    else:
        deadline = compute_deadline(today)

    period_text = f"{fmt(start)}~{fmt(end)}"
    deadline_text = fmt(deadline)

    font_path = get_font_path()
    print("모드:", mode, "| 지난 종료일:", last_end, "| 제출기한 입력:", deadline_input or "(자동)")
    print("font:", font_path)
    print("대상기간:", period_text)
    print("제출기한:", deadline_text)

    img = Image.open(base_image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    draw_field(draw, font_path, period_text,
               PERIOD_BOX, PERIOD_LEFT, PERIOD_TARGET_W, PERIOD_COLOR)
    draw_field(draw, font_path, deadline_text,
               DEADLINE_BOX, DEADLINE_LEFT, DEADLINE_TARGET_W, DEADLINE_COLOR)

    out = os.path.join(output_folder, "attendance.png")
    img.convert("RGB").save(out)
    print("저장 완료:", out)

    # 이번에 마감한 종료일을 기록 → 다음 실행은 그 다음 날부터 이어서 잡는다.
    write_last_end(end)
    print("상태 저장:", STATE_FILE, "→", end.isoformat())


if __name__ == "__main__":
    generate("pic.png", "./output_images")
