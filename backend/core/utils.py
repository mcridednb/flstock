import io
from io import BytesIO

import pdfkit
import requests
from PIL import Image, ImageFont
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


def create_infographic(title, price_text, source, offers, minutes_ago):
    font_path = FONT_PATH
    title_font_size = 85
    title_font = ImageFont.truetype(font_path, title_font_size)
    price_font = ImageFont.truetype(font_path, 45)
    logo_font = ImageFont.truetype(font_path, 50)
    text_font = ImageFont.truetype(font_path, 35)

    max_title_width = 1100
    wrapped_title = wrap_text(title, title_font, max_title_width)
    title_height = len(wrapped_title) * (title_font_size + 10)
    img_height = 630 - 85 + title_height

    img = Image.new('RGB', (1200, img_height), color=(0, 0, 0))

    with Pilmoji(img, source=AppleEmojiSource) as pilmoji:
        pilmoji.text((50, 50), source, (255, 255, 255), font=logo_font)
        pilmoji.text((1150, 50), "Фрилансер", (255, 255, 255), font=logo_font, anchor="ra")

        current_height = 250
        for line in wrapped_title:
            pilmoji.text((50, current_height), line, (255, 255, 255), font=title_font)
            current_height += title_font_size + 10

        pilmoji.text((50, current_height + 50), f"💰 {price_text}", (255, 255, 255), font=price_font)

        pilmoji.text((50, current_height + 150), f"💼 Откликов: {offers}", (255, 255, 255), font=text_font)
        pilmoji.text((50, current_height + 200), f"⏱️ {minutes_ago} минут назад", (255, 255, 255), font=text_font)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def create_pdf_file(response, template_name):
    html_content = render_to_string(template_name, {'response': response})
    options = {
        'encoding': 'UTF-8'
    }
    pdf_buffer = pdfkit.from_string(html_content, False, options=options)
    buffer = io.BytesIO(pdf_buffer)
    buffer.seek(0)
    return buffer


def send_html_to_telegram(chat_id, message_id, response, template_name):
    pdf_buffer = create_pdf_file(response, template_name)
    files = {
        'document': (f'report.pdf', pdf_buffer, 'application/pdf')
    }
    data = {
        'chat_id': chat_id,
        'text': response["response"],
        'parse_mode': 'Markdown',
        'reply_to_message_id': message_id,
    }
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    response = requests.post(url, data=data, files=files)
    return response.json()


def send_limit_exceeded_message(chat_id, message_id, is_pro: bool):
    text = (
        "🚫 Дневной лимит на анализ данного типа превышен.\n"
        "Лимиты сбрасываются каждый день в 00:00 по МСК."
    )
    # keyboard = []
    # if not is_pro:
    #     keyboard.append([
    #         {
    #             'text': '🛒 Купить подписку',
    #             'callback_data': 'get_subscribe'
    #         }
    #     ])
    # else:
    #     keyboard.append([
    #         {
    #             'text': 'ℹ️ Подробнее о лимитах',
    #             'callback_data': 'limit_info'
    #         }
    #     ])
    # keyboard = {
    #     'inline_keyboard': keyboard
    # }
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'reply_to_message_id': message_id,
        # 'reply_markup': keyboard
    }
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(url, json=data)
    return response.json()
