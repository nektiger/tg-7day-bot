import os
import json
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка заданий
def load_tasks():
    try:
        with open("tasks.json", "r", encoding="utf-8") as f:
            tasks = json.load(f)
            if not isinstance(tasks, dict):
                raise ValueError("Файл tasks.json должен содержать объект JSON (словарь)")
            return tasks
    except Exception as e:
        logger.error(f"Ошибка при загрузке tasks.json: {e}")
        return {}

tasks = load_tasks()

# Создание клавиатуры
def get_keyboard():
    buttons = [
        [InlineKeyboardButton(f"День {i}", callback_data=str(i))]
        for i in range(1, 8)
    ]
    return InlineKeyboardMarkup(buttons)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Нажми на день, чтобы получить задание.",
        reply_markup=get_keyboard()
    )

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(text=task, reply_markup=get_keyboard())

# Webhook обработчик
async def handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.initialize()
        await application.process_update(update)
        return web.Response(text="ok")
    except Exception as e:
        logger.error("Ошибка обработки запроса", exc_info=e)
        return web.Response(status=500, text="error")

# Инициализация
TOKEN = os.getenv("TOKEN")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://tg-7day-bot.onrender.com{WEBHOOK_PATH}"

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

# Запуск Aiohttp-сервера
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handler)

if __name__ == "__main__":
    web.run_app(app, port=10000)