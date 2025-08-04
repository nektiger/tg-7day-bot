import json
from aiohttp import web
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

TOKEN = "8467489835:AAF09FNV4dW1DVAMikyZeq1eIRu7oZgabws"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://tgbot-zaxn.onrender.com{WEBHOOK_PATH}"  # ← твой домен

app = Application.builder().token(TOKEN).build()
tasks = {}

# Загрузка заданий из tasks.json
def load_tasks():
    global tasks
    with open("tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"День {i}", callback_data=f"day_{i}")]
        for i in range(1, 8)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выбери день:", reply_markup=reply_markup)

# Обработка нажатий кнопок
async def handle_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    if day in tasks:
        text = f"<b>Задание на {day.replace('_', ' ')}</b>\n\n" + "\n".join(f"• {t}" for t in tasks[day])
        await query.edit_message_text(text=text, parse_mode="HTML")
    else:
        await query.edit_message_text("Задание не найдено.")

# Webhook обработчик
async def handler(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.initialize()  # ← это обязательная строка!
    await app.process_update(update)
    return web.Response()

# Запуск aiohttp сервера
async def main():
    load_tasks()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_day))
    await app.initialize()
    await app.start()
    await app.bot.set_webhook(url=WEBHOOK_URL)
    web_app = web.Application()
    web_app.router.add_post(WEBHOOK_PATH, handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()
    print("Бот запущен и webhook настроен.")
    await app.updater.wait()  # блокировка

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())