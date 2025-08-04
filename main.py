import os
import json
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка заданий
def load_tasks():
    try:
        with open("tasks.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("tasks.json должен содержать объект (словарь)")
            return data
    except Exception as e:
        logger.error(f"Ошибка загрузки tasks.json: {e}")
        return {}

tasks = load_tasks()

# Клавиатура
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"День {i}", callback_data=str(i))] for i in range(1, 8)
    ])

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выбери день:", reply_markup=get_keyboard())

# Обработка нажатий
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(text=task, reply_markup=get_keyboard())

# Webhook-обработчик
async def handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(text="ok")
    except Exception as e:
        logger.error("Ошибка обработки запроса", exc_info=e)
        return web.Response(status=500, text="error")

# Настройки
TOKEN = os.environ.get("TOKEN")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
PORT = int(os.environ.get("PORT", 10000))

application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

# AIOHTTP-сервер
web_app = web.Application()
web_app.router.add_post(WEBHOOK_PATH, handler)

if __name__ == "__main__":
    web.run_app(web_app, port=PORT)