import asyncio
import logging
import json
import os

from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8467489835:AAF09FNV4dW1DVAMikyZeq1eIRu7oZgabws"
WEBHOOK_URL = f"https://tg-7day-bot.onrender.com/webhook/{TOKEN}"

PORT = int(os.environ.get("PORT", 10000))  # вот тут просто слушаем порт из окружения

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
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return web.Response()

async def main():
    load_tasks()

    global app
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    for i in range(1, 8):
        app.add_handler(CommandHandler(str(i), show_task))

    # Устанавливаем webhook
    await app.bot.set_webhook(WEBHOOK_URL)

    # Запускаем aiohttp-сервер и регистрируем путь webhook
    web_app = web.Application()
    web_app.router.add_post(f"/webhook/{TOKEN}", handler)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"Webhook установлен: {WEBHOOK_URL}")

    # Ждем бесконечно
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())