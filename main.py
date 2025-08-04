import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from aiohttp import web

# Загрузка переменных среды
TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# Загрузка заданий из tasks.json
with open("tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Хендлер команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton(f"День {i}", callback_data=str(i))] for i in range(1, 8)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выбери день, чтобы получить задание:", reply_markup=reply_markup)

# Хендлер нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(text=task)

# Обработка входящих запросов от Telegram
async def handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response()
    except Exception as e:
        logging.exception("Ошибка обработки запроса")
        return web.Response(status=500, text=str(e))

# Создание Telegram-приложения
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

# Запуск aiohttp сервера
app = web.Application()
app.router.add_post(f"/webhook/{TOKEN}", handler)

if __name__ == "__main__":
    web.run_app(app, port=PORT)