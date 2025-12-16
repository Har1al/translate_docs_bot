from aiogram import Router
from lexicon.lexicon import LEXICON_RU

other_router = Router()

@other_router.message()
async def send_answer(message):
    await message.answer(
        text=LEXICON_RU['other_answer']
    )