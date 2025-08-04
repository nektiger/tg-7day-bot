import os
import json
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")
PORT = int(os.environ.get("PORT", "8080"))

# Загружаем задания из файла
with open("tasks.json", "r", encoding="utf-8") as f:
    TASKS = json.load(f)

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 8)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Выбери день от 1 до 7, чтобы получить задание на этот день:", reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    task = TASKS.get(day, "Задание не найдено.")
    await query.edit_message_text(text=f"Задание на день {day}:\n{task}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

async def handle(request):
    if request.method == "POST":
        try:
            data = await request.json()
            update = Update.de_json(data, application.bot)
            await application.process_update(update)
            return web.Response(text="OK")
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            return web.Response(status=500, text=str(e))
    else:
        return web.Response(text="Hello! This is Telegram bot webhook server.")

app = web.Application()
app.router.add_post(f"/webhook/{TOKEN}", handle)
app.router.add_get("/", lambda request: web.Response(text="Bot is running."))

if __name__ == "__main__":
    logger.info(f"Starting server on port {PORT}...")
    web.run_app(app, port=PORT)