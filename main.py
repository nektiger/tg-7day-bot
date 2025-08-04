import asyncio
import logging
import json
import os

from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = "8467489835:AAF09FNV4dW1DVAMikyZeq1eIRu7oZgabws"
WEBHOOK_URL = f"https://tg-7day-bot.onrender.com/webhook/{TOKEN}"

PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tasks = {}

def load_tasks():
    global tasks
    with open("tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Выбери день от 1 до 7, чтобы получить задание."
    )

async def show_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text.strip()
    if day in tasks:
        await update.message.reply_text(f"День {day}:\n\n{tasks[day]}")
    else:
        await update.message.reply_text("Пожалуйста, введи число от 1 до 7.")

async def handler(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)  # используй app.bot, а не bot отдельно
    await app.process_update(update)
    return web.Response(text="ok")

async def main():
    load_tasks()

    global app
    app = Application.builder().token(TOKEN).build()

    # Добавляем хэндлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))

    # Команды с цифрами 1-7 — добавим через цикл
    for i in range(1, 8):
        app.add_handler(CommandHandler(str(i), show_task))

    # Инициализируем и запускаем приложение
    await app.initialize()
    await app.start()

    # Устанавливаем webhook
    await app.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook установлен: {WEBHOOK_URL}")

    # Создаем aiohttp приложение и регистрируем обработчик webhook
    aio_app = web.Application()
    aio_app.router.add_post(f"/webhook/{TOKEN}", handler)

    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"Сервер запущен на порту {PORT}")

    # Чтобы приложение не завершилось
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())