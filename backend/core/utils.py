import io
import json
from io import BytesIO

import pdfkit
import requests
from PIL import Image, ImageFont, ImageDraw
from django.conf import settings
from django.template.loader import render_to_string
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource

FONT_PATH = "./fonts/Roboto/Roboto-Regular.ttf"


def wrap_text(text, font, max_width):
    """Wrap text to fit within a specified width when rendered."""
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and font.getbbox(line + words[0])[2] <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line)
    return lines


def create_infographic(title, price_text, source, offers, minutes_ago, subcategory):
    font_path = FONT_PATH
    title_font_size = 75
    title_font = ImageFont.truetype(font_path, title_font_size)
    price_font = ImageFont.truetype(font_path, 36)
    logo_font = ImageFont.truetype(font_path, 50)
    text_font = ImageFont.truetype(font_path, 30)
    breadcrumbs = ImageFont.truetype(font_path, 30)

    max_title_width = 1100
    wrapped_title = wrap_text(title, title_font, max_title_width)
    title_height = len(wrapped_title) * (title_font_size + 10)
    img_height = 630 - 85 + title_height

    img = Image.new('RGB', (1200, img_height), color=(0, 0, 0))

    temp_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text((1150, 50), "Фрилансер", font=logo_font, fill=(255, 255, 255, 90), anchor="ra")
    current_height = 250
    for line in wrapped_title:
        temp_draw.text((50, current_height), line, (255, 255, 255), font=title_font)
        current_height += title_font_size + 10
    temp_draw.text((1150, current_height + 200), "@freelancerai_bot", (255, 255, 255, 90), font=text_font, anchor="ra")

    img = Image.alpha_composite(img.convert('RGBA'), temp_img)

    with Pilmoji(img, source=AppleEmojiSource) as pilmoji:
        pilmoji.text((50, 50), source, (160, 225, 68), font=logo_font)

        pilmoji.text((55, 200), f"> {subcategory}", (255, 255, 255), font=breadcrumbs)

        pilmoji.text((50, current_height + 20), f"💰{price_text}", (255, 255, 255), font=price_font)

        pilmoji.text((55, current_height + 150), f"💼 Откликов: {offers}", (255, 255, 255), font=text_font)
        pilmoji.text(
            (55, current_height + 200), f"⏱️ {minutes_ago} минут назад", (255, 255, 255), font=text_font
        )

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()
