"""근태 주마감 일정 공지 이미지 자동 생성.

- 대상기간 : 직전 주 월요일 ~ 일요일 (한국 시간 기준)
            (월요일에 발행 → 지난 주가 대상)
- 제출기한 : 발행한 주(이번 주)의 화요일. 단, 그 화요일이 한국 공휴일
            (대체공휴일 포함)이면 공휴일/주말이 끝난 다음 평일로 이동.
"""

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


def compute_dates(today):
    """today(한국 날짜) 기준으로 대상기간과 제출기한을 계산."""
    this_monday = today - timedelta(days=today.weekday())   # 이번 주 월요일
    target_monday = this_monday - timedelta(days=7)         # 직전 주 월요일
    target_sunday = target_monday + timedelta(days=6)       # 직전 주 일요일

    kr_holidays = holidays.SouthKorea()
    deadline = this_monday + timedelta(days=1)              # 이번 주 화요일
    # 공휴일 또는 주말이면 다음 평일로 이동
    while deadline in kr_holidays or deadline.weekday() >= 5:
        deadline += timedelta(days=1)

    return target_monday, target_sunday, deadline


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
    target_monday, target_sunday, deadline = compute_dates(today)

    period_text = f"{fmt(target_monday)}~{fmt(target_sunday)}"
    deadline_text = fmt(deadline)

    font_path = get_font_path()
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


if __name__ == "__main__":
    generate("pic.png", "./output_images")
