from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime, timedelta

# 상수 정의
DAYS_POSITION = (710, 475)
YEAR_POSITION = (620, 650)
MONTH_POSITION = (867, 650)
DAY_POSITION = (1050, 650)

DAYS_FONT_SIZE = 110
DATE_FONT_SIZE = 65
TEXT_COLOR = "#0A897B"
SPACING = 20


def get_font_path():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("NotoSansCJK font not found")


def generate_safety_images(base_image_path, output_folder, start_date):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    base_image = Image.open(base_image_path).convert("RGBA")
    print("base image size:", base_image.size)

    font_path = get_font_path()
    print("font loaded:", font_path)

    days_font = ImageFont.truetype(font_path, DAYS_FONT_SIZE)
    date_font = ImageFont.truetype(font_path, DATE_FONT_SIZE)

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

    utc_now = datetime.utcnow()
    korea_now = utc_now + timedelta(hours=9)

    days = (korea_now.date() - start_date_obj.date()).days + 1

    img = base_image.copy()
    draw = ImageDraw.Draw(img)

    year = start_date_obj.strftime("%Y")
    month = start_date_obj.strftime("%m")
    day = start_date_obj.strftime("%d")

    draw.text(YEAR_POSITION, year, fill=TEXT_COLOR, font=date_font)
    draw.text(MONTH_POSITION, month, fill=TEXT_COLOR, font=date_font)
    draw.text(DAY_POSITION, day, fill=TEXT_COLOR, font=date_font)

    text = f"{days:04d}"

    total_width = 0
    for i, digit in enumerate(text):
        x = DAYS_POSITION[0] + total_width
        y = DAYS_POSITION[1]

        draw.text((x, y), digit, fill=TEXT_COLOR, font=days_font)

        bbox = days_font.getbbox(digit)
        digit_width = bbox[2] - bbox[0]

        if i < len(text) - 1:
            total_width += digit_width + SPACING

    output_path = os.path.join(output_folder, "safety.png")
    img.save(output_path)
    print(f"저장 완료: {output_path}")

    return days


days = generate_safety_images("untitled.png", "./output_images", "2025-05-07")
print(f"2025년 05월 07일부터 오늘까지 {days}일이 지났습니다.")
