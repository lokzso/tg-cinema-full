import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BotCommand
from .config import settings

async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎬 Открыть кинотеатр", web_app=WebAppInfo(url=settings.webapp_url))
    ]])
    await message.answer(
        "🎬 <b>Cinema Bot</b>\n\nПоиск, сезоны и серии, источники, качество, озвучки, избранное и продолжение просмотра.",
        reply_markup=kb, parse_mode="HTML"
    )

async def run_bot():
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty")
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    dp.message.register(start, CommandStart())
    dp.message.register(start, F.text == "🎬 Открыть")
    await bot.set_my_commands([BotCommand(command="start", description="Открыть кинотеатр")])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run_bot())
