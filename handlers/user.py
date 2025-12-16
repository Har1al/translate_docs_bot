from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from lexicon.lexicon import LEXICON_RU
from aiogram.types import FSInputFile
from datetime import datetime
from services.process_docx import from_eng_to_rus_docx
from services.process_pdf import from_eng_to_rus_pdf
import os

user_router = Router()

@user_router.message(CommandStart())
async def process_start_command(message):
    await message.answer(
        text=LEXICON_RU['/start']
    )

@user_router.message(Command(commands=['help']))
async def process_help_command(message):
    await message.answer(
        text=LEXICON_RU['/help']
    )

@user_router.message(F.document)
async def process_docx_file(message):

    print(message.json())

    doc = message.document
    filename = doc.file_name

    if filename.endswith('.docx'):

        uniq_suffix = datetime.now().strftime('%d.%m.%Y_%H-%M-%S') + '_'
        name = f'{uniq_suffix}__{os.path.splitext(filename)[0]}.docx'
        path = os.path.join('downloads', name)

        try:
            await message.bot.download(doc.file_id, destination=path)
        except Exception as ex:
            await message.answer(text='Не удалось обработать документ')
            print(f'[!] Ошибка загрузки файла {ex}')

        save_path = os.path.join('completed_docs', name)

        await from_eng_to_rus_docx(path, message, save_path)

        await message.answer_document(
            document=FSInputFile(save_path),
        )

    elif filename.endswith('.pdf'):
        uniq_suffix = datetime.now().strftime('%d.%m.%Y_%H-%M-%S') + '_'
        name = f'{uniq_suffix}__{os.path.splitext(filename)[0]}.pdf'
        path = os.path.join('downloads', name)

        try:
            await message.bot.download(doc.file_id, destination=path)
        except Exception as ex:
            await message.answer(text='Не удалось обработать документ')
            print(f'[!] Ошибка загрузки файла {ex}')

        save_path = os.path.join('completed_docs', name)

        await from_eng_to_rus_pdf(path, message, save_path)

        await message.answer_document(
            document=FSInputFile(save_path),
        )
    else:
        await message.answer(text=LEXICON_RU['other_answer'])
