import json
import os
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackContext, CommandHandler, CallbackQueryHandler
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

with open("tasks.json", "r", encoding="utf-8") as f:
    TASKS = json.load(f)

WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://tg-7day-bot.onrender.com{WEBHOOK_PATH}"

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(f"День {i}", callback_data=f"day_{i}")] for i in range(1, 8)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Нажми на кнопку дня, чтобы получить задание:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    day = query.data.split("_")[1]
    task = TASKS.get(f"day_{day}", "Задание не найдено.")
    await query.edit_message_text(f"🗓 Задание на день {day}:\n\n{task}")

async def webhook_handler(request):
    if request.method == "POST":
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response()
    return web.Response(status=403)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

# 🌐 Запуск Webhook
async def on_startup(app_obj):
    await app.initialize()
    await app.start()
    await app.bot.set_webhook(WEBHOOK_URL)

async def on_cleanup(app_obj):
    await app.stop()

web_app = web.Application()
web_app.router.add_post(WEBHOOK_PATH, webhook_handler)
web_app.on_startup.append(on_startup)
web_app.on_cleanup.append(on_cleanup)

if __name__ == "__main__":
    web.run_app(web_app, host="0.0.0.0", port=10000)