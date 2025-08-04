import os
import json
import logging
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import defaults as tg_defaults
import asyncio

TOKEN = os.getenv("TOKEN")  # обязательно установи переменную окружения
WEBHOOK_PATH = f"/webhook/{TOKEN}"
PORT = int(os.environ.get("PORT", 10000))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем задания
def load_tasks():
    with open("tasks.json", "r", encoding="utf-8") as f:
        return json.load(f)

tasks = load_tasks()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [{"text": f"День {i}", "callback_data": str(i)}] for i in range(1, 8)
    ]
    await update.message.reply_text(
        "Привет! Выбери день, чтобы получить задание.",
        reply_markup={"inline_keyboard": keyboard}
    )

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(task)

# Обработка webhook-запроса
async def handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error("Ошибка обработки запроса", exc_info=e)
        return web.Response(status=500)

# Основная точка входа
async def main():
    global application
    application = Application.builder().token(TOKEN).build()

    # Инициализация бота вручную
    await application.initialize()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Настраиваем aiohttp веб-сервер
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info("✅ Бот запущен")
    await application.start()  # Не забываем стартовать бота
    await application.updater.start_polling()  # Запускаем внутреннюю очередь
    await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())