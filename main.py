import logging
import json
import os
from aiohttp import web
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    Defaults,
)
from dotenv import load_dotenv

load_dotenv()

# Настройки
TOKEN = os.getenv("TOKEN")
WEBHOOK_SECRET_PATH = f"/webhook/{TOKEN}"
PORT = int(os.environ.get("PORT", "10000"))

# Логгирование
logging.basicConfig(level=logging.INFO)

# Загрузка заданий
def load_tasks():
    try:
        with open("tasks.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                raise ValueError("tasks.json должен содержать словарь")
    except Exception as e:
        logging.error(f"Ошибка загрузки заданий: {e}")
        return {}

tasks = load_tasks()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"День {i}", callback_data=str(i))] for i in range(1, 8)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Выбери день, чтобы получить задание:", reply_markup=reply_markup
    )

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(task)

# Webhook handler
async def handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(text="ok")
    except Exception as e:
        logging.error("Ошибка обработки запроса", exc_info=e)
        return web.Response(status=500, text="error")

# Инициализация
defaults = Defaults(parse_mode=ParseMode.HTML)
application = ApplicationBuilder().token(TOKEN).defaults(defaults).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

# AIOHTTP web-сервер
app = web.Application()
app.router.add_post(WEBHOOK_SECRET_PATH, handler)

# Установка webhook при запуске
async def on_startup(app):
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_SECRET_PATH}"
    await application.bot.set_webhook(webhook_url)

# Запуск
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, port=PORT)