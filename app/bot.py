from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BotCommand

from .config import settings

bot: Bot | None = Bot(settings.bot_token) if settings.bot_token else None
dp = Dispatcher()


async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎬 Открыть Tg Cinema", web_app=WebAppInfo(url=settings.webapp_url))
    ]])
    await message.answer(
        "🎬 <b>Tg Cinema</b>\n\nИщи название, выбирай сезон и серию, а источники, озвучки и качество соберутся автоматически.",
        reply_markup=kb,
        parse_mode="HTML",
    )


dp.message.register(start, CommandStart())
dp.message.register(start, F.text == "🎬 Открыть")


async def setup_webhook():
    if not bot or not settings.webhook_enabled:
        return
    await bot.set_my_commands([BotCommand(command="start", description="Открыть Tg Cinema")])
    await bot.set_webhook(
        settings.webhook_url,
        secret_token=settings.telegram_webhook_secret,
        allowed_updates=dp.resolve_used_update_types(),
    )


async def close_bot():
    if bot:
        await bot.session.close()


async def run_polling():
    if not bot:
        raise RuntimeError("BOT_TOKEN is empty")
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.set_my_commands([BotCommand(command="start", description="Открыть Tg Cinema")])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_polling())
