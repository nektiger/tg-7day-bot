import logging
import json
import os
from aiohttp import web
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("TOKEN")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(level=logging.INFO)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"День {i}", callback_data=str(i))] for i in range(1, 8)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Выбери день, чтобы получить задание:", reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(task, parse_mode=ParseMode.HTML)

# Инициализация приложения
application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

async def handle_webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        # Инициализация вручную, чтобы избежать ошибки
        if not application.is_initialized:
            await application.initialize()
            await application.start()
        await application.process_update(update)
        return web.Response(text="ok")
    except Exception as e:
        logging.error("Ошибка обработки запроса", exc_info=e)
        return web.Response(status=500, text="error")

# Создаём aiohttp сервер
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)

async def on_startup(app):
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"
    await application.bot.set_webhook(webhook_url)
    logging.info(f"Webhook установлен: {webhook_url}")

app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, port=PORT)