import os
import json
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = "8467489835:AAF09FNV4dW1DVAMikyZeq1eIRu7oZgabws"
PORT = int(os.getenv("PORT", "8080"))  # можно задать через env, иначе 8080
DOMAIN = "tg-7day-bot.onrender.com"

# Загрузим задания из файла tasks.json
with open("tasks.json", encoding="utf-8") as f:
    tasks = json.load(f)

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=str(i))] for i in range(1, 8)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выбери день (1-7):", reply_markup=reply_markup
    )

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    day = query.data
    text = tasks.get(day, "Задание не найдено.")
    await query.edit_message_text(text=text)

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

# aiohttp обработчик webhook
async def handler(request):
    if request.method == "POST":
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(text="ok")
    return web.Response(status=404)

app = web.Application()
app.router.add_post(f"/webhook/{TOKEN}", handler)

if __name__ == "__main__":
    print(f"Starting server on port {PORT}...")
    web.run_app(app, port=PORT)