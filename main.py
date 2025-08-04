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
    update = Update.de_json(data, bot)
    await app.process_update(update)
    return web.Response()

async def main():
    load_tasks()

    global app, bot
    app = Application.builder().token(TOKEN).build()
    bot = app.bot

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("day", show_task))

    app.add_handler(CommandHandler(str(i), show_task) for i in range(1, 8))

    # Настройка webhook
    await bot.set_webhook(WEBHOOK_URL)

    # Запуск aiohttp-сервера
    runner = web.AppRunner(web.Application())
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"Webhook установлен: {WEBHOOK_URL}")

    # Бесконечный цикл
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())