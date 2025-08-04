import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем задания из файла при старте
with open("tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)  # tasks — словарь { "1": "...", "2": "...", ... }

# Команда /start — выводит меню с кнопками дней
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"День {day}", callback_data=str(day))]
        for day in tasks.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери день для задания:", reply_markup=reply_markup)

# Обработка нажатия на кнопку с днём
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(text=f"Задание на день {day}:\n\n{task}")

# HTTP обработчик для webhook
async def handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data)
        await application.process_update(update)
        return web.Response(text="ok")
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}")
        return web.Response(status=500, text="Internal Server Error")

async def main():
    global application
    application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Запуск aiohttp веб-сервера для вебхука
    app = web.Application()
    app.router.add_post("/webhook/YOUR_BOT_TOKEN", handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logger.info("Бот запущен и слушает вебхук...")
    # Просто держим приложение в работе
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

import asyncio
if __name__ == "__main__":
    asyncio.run(main())