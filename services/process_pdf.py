from environs import Env
from mistralai import Mistral
from reportlab.lib.pagesizes import A4
import asyncio
from reportlab.pdfgen import canvas
from openai import OpenAI
from services.call_model import call_model_for_translations
from services.process_docx import _spinner_edit

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

env = Env()
env.read_env()

TIMES_NEW_ROMAN_PATH = 'C:/Windows/Fonts/times.ttf'

FONT_NAME = 'TimesNewRoman'

if os.path.exists(TIMES_NEW_ROMAN_PATH):
    pdfmetrics.registerFont(TTFont(FONT_NAME, TIMES_NEW_ROMAN_PATH))
else:
    print(f"⚠️ Ошибка: Файл шрифта не найден по пути: {TIMES_NEW_ROMAN_PATH}. Будут использованы стандартные шрифты (вероятно, с квадратиками).")

async def from_eng_to_rus_pdf(path, message, save_path):

    client = Mistral(api_key=env('MISTRAL_API_KEY'))

    uploaded_dpf = client.files.upload(
        file={
            "file_name": path,
            "content": open(path, "rb"),
        },
        purpose="ocr"
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_dpf.id)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True
    )

    pages = ocr_response.pages

    pdf_file = save_path
    c = canvas.Canvas(pdf_file, pagesize=A4)
    width, height = A4

    ai_client = OpenAI(api_key=env('API_KEY'))

    for page in pages:

        text = page.markdown
        lines = [i.replace('|', '').replace('$', '').strip() for i in text.split('\n')]

        c.setFont(FONT_NAME, 14)

        await message.answer(text=f"Собрано {len(lines)} уникальных фрагментов для перевода / замены.")

        status_msg = await message.answer("Отправляю запрос модели")
        spinner_task = asyncio.create_task(_spinner_edit(status_msg, base_text="Отправляю запрос модели"))

        try:

            translate_text = await asyncio.to_thread(call_model_for_translations, ai_client, lines)

            spinner_task.cancel()

            await status_msg.edit_text(f"✅ Получено {len(translate_text)} пар 'оригинал -> перевод'.")

        except Exception as e:
            spinner_task.cancel()
            try:
                await spinner_task
            except asyncio.CancelledError:
                pass
            await status_msg.edit_text("❌ Ошибка при обработке документа.")
            print("[!] Ошибка from_eng_to_rus:", e)

        y = height - 50


        for line in lines:

            translated_line = translate_text.get(line.strip(), "Перевод недоступен")  # Безопасное получение
            c.drawString(50, y, translated_line[:90])
            y -= 12
            if y < 50:
                c.showPage()
                y = height - 50

        c.showPage()

    c.save()

