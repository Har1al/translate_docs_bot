from docx import Document
import asyncio
from openai import OpenAI
from environs import Env
from services.call_model import call_model_for_translations

env = Env()
env.read_env()


async def _spinner_edit(status_message, base_text="Отправляю запрос модели"):

    dots = 0
    try:
        while True:
            dots = (dots % 3) + 1
            suffix = "." * dots
            try:
                await status_message.edit_text(f"{base_text}{suffix}")
            except Exception:
                pass
            await asyncio.sleep(0.7)
    except asyncio.CancelledError:
        # при отмене просто выходим
        raise

def collect_texts(doc):

    texts = []

    for p in doc.paragraphs:
        if p.text and p.text.strip():
            texts.append(p.text)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text and p.text.strip():
                        texts.append(p.text)

    for section in doc.sections:
        hdr = section.header
        for p in hdr.paragraphs:
            if p.text and p.text.strip():
                texts.append(p.text)
        ftr = section.footer
        for p in ftr.paragraphs:
            if p.text and p.text.strip():
                texts.append(p.text)

    seen = set()
    unique_texts = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            unique_texts.append(t)
    return unique_texts


def copy_font_attributes(src_run, dst_run):
    try:
        s = src_run.font
        d = dst_run.font
        if s.name: d.name = s.name
        if s.size: d.size = s.size
        if s.bold is not None: d.bold = s.bold
        if s.italic is not None: d.italic = s.italic
        if s.underline is not None: d.underline = s.underline
    except Exception:
        pass

def replace_in_paragraph(par, mapping):

    for run in par.runs:
        try:
            if run._element.xpath('.//w:drawing'):
                return
        except Exception:
            pass

    full = par.text

    if not full:
        return

    new_full = full
    for k, v in mapping.items():
        if k and k in new_full:
            new_full = new_full.replace(k, v)

    if new_full == full:
        return

    first_run = par.runs[0] if par.runs else None

    for r in list(par.runs):
        try:
            r._element.getparent().remove(r._element)
        except Exception:
            try:
                r.text = ""
            except Exception:
                pass

    newr = par.add_run(new_full)
    if first_run is not None:
        copy_font_attributes(first_run, newr)

def process_document(doc, mapping):

    for p in doc.paragraphs:
        replace_in_paragraph(p, mapping)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_in_paragraph(p, mapping)

    for section in doc.sections:
        hdr = section.header
        for p in hdr.paragraphs:
            replace_in_paragraph(p, mapping)
        ftr = section.footer
        for p in ftr.paragraphs:
            replace_in_paragraph(p, mapping)

async def from_eng_to_rus_docx(path, message, save_path):
    doc = Document(path)
    texts = collect_texts(doc)
    if not texts:
        await message.answer(text="В документе нет текстовых фрагментов для обработки.")
        return

    await message.answer(text=f"Собрано {len(texts)} уникальных фрагментов для перевода / замены.")

    client = OpenAI(api_key=env('API_KEY'))

    status_msg = await message.answer("Отправляю запрос модели")
    spinner_task = asyncio.create_task(_spinner_edit(status_msg, base_text="Отправляю запрос модели"))

    try:
        mapping = await asyncio.to_thread(call_model_for_translations, client, texts)

        if not isinstance(mapping, dict):
            await message.answer(text="Ответ модели не является словарём. Отбой.")
            return

        spinner_task.cancel()
        try:
            await spinner_task
        except asyncio.CancelledError:
            pass

        await status_msg.edit_text(f"✅ Получено {len(mapping)} пар 'оригинал -> перевод'.")

        process_document(doc, mapping)
        doc.save(save_path)

    except Exception as e:
        spinner_task.cancel()
        try:
            await spinner_task
        except asyncio.CancelledError:
            pass
        await status_msg.edit_text("❌ Ошибка при обработке документа.")
        print("[!] Ошибка from_eng_to_rus:", e)

