import os
import json
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8467489835:AAF09FNV4dW1DVAMikyZeq1eIRu7oZgabws"

WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", "8443"))

tasks = {
    "1": "🧠 Задание на день 1: Прочитай статью о привычках и напиши 3 свои плохие привычки, которые хочешь изменить.",
    "2": "📖 Задание на день 2: Проведи 15 минут в тишине без телефона. После — запиши, что почувствовал.",
    "3": "📝 Задание на день 3: Составь план на неделю. Укажи 3 важные задачи и 2 второстепенные.",
    "4": "💧 Задание на день 4: Пей воду в течение дня. Минимум 1,5 литра. Запиши, как это повлияло на твоё самочувствие.",
    "5": "🏃 Задание на день 5: Прогуляйся на улице минимум 30 минут. Без телефона и наушников.",
    "6": "📵 Задание на день 6: Устрой цифровой детокс на 2 часа. Никаких экранов. Чем ты занял это время?",
    "7": "🎯 Задание на день 7: Напиши себе письмо в будущее. Расскажи, чего хочешь достичь через 1 месяц."
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 8)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите день, чтобы получить задание:", reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    task = tasks.get(day, "❌ Задание не найдено.")
    await query.edit_message_text(text=task)

async def handler(request: web.Request):
    app = request.app["bot_app"]
    body = await request.text()
    update = Update.de_json(json.loads(body), app.bot)
    await app.process_update(update)
    return web.Response(text="ok")

async def on_startup(app: web.Application):
    webhook_url = f"https://tg-7day-bot.onrender.com{WEBHOOK_PATH}"
    await app["bot_app"].bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

async def on_shutdown(app: web.Application):
    await app["bot_app"].bot.delete_webhook()
    logger.info("Webhook удалён")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    app = web.Application()
    app["bot_app"] = application

    app.router.add_post(WEBHOOK_PATH, handler)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    main()