from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
import requests
import tempfile

# 상수 정의
DAYS_POSITION = (710, 475)
YEAR_POSITION = (620, 650)
MONTH_POSITION = (867, 650)
DAY_POSITION = (1050, 650)
DAYS_FONT_SIZE = 110
DATE_FONT_SIZE = 65
TEXT_COLOR = "#0A897B"
SPACING = 20

def download_font():
    font_url = "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/OTF/Korean/NotoSansCJKkr-Bold.otf"
    try:
        response = requests.get(font_url)
        if response.status_code == 200:
            temp_font_path = os.path.join(tempfile.gettempdir(), "NotoSansCJKkr-Bold.otf")
            with open(temp_font_path, "wb") as f:
                f.write(response.content)
            return temp_font_path
        else:
            return None
    except:
        return None

def generate_safety_images(base_image_path, output_folder, start_date):
    # 폴더가 없으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 기본 이미지 로드
    base_image = Image.open(base_image_path)
    
    # 폰트 다운로드 및 설정
    font_path = download_font()
    try:
        if font_path:
            days_font = ImageFont.truetype(font_path, DAYS_FONT_SIZE)
            date_font = ImageFont.truetype(font_path, DATE_FONT_SIZE)
        else:
            raise IOError
    except IOError:
        print("폰트 다운로드 실패. 기본 폰트로 대체합니다.")
        days_font = ImageFont.load_default()
        date_font = ImageFont.load_default()
    
    # 날짜 계산
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    today = datetime.now()
    days = (today - start_date_obj).days

    # 이미지 복사
    img = base_image.copy()
    draw = ImageDraw.Draw(img)
    
    # 시작 날짜 표시 (년, 월, 일 따로)
    year = start_date_obj.strftime("%Y")
    month = start_date_obj.strftime("%m")
    day = start_date_obj.strftime("%d")
    
    draw.text(YEAR_POSITION, year, fill=TEXT_COLOR, font=date_font)
    draw.text(MONTH_POSITION, month, fill=TEXT_COLOR, font=date_font)
    draw.text(DAY_POSITION, day, fill=TEXT_COLOR, font=date_font)
    
    # D-day 숫자 적용 (자간 조절)
    text = f"{days:04d}"
    
    # 각 숫자를 개별적으로 그리기
    total_width = 0
    for i, digit in enumerate(text):
        draw.text((DAYS_POSITION[0] + total_width, DAYS_POSITION[1]), digit, fill=TEXT_COLOR, font=days_font)
        if i < len(text) - 1:
            bbox = days_font.getbbox(digit)
            total_width += (bbox[2] - bbox[0]) + SPACING
    
    # 이미지 저장
    output_path = os.path.join(output_folder, f"safety.png")
    img.save(output_path)
    print(f"저장 완료: {output_path}")
    return days

# 사용 예시
days = generate_safety_images("untitled.png", "./output_images", "2024-11-13")
print(f"2024년 11월 13일부터 오늘까지 {days}일이 지났습니다.")