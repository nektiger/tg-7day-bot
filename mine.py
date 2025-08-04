import asyncio
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8467489835:AAF09FNV4dW1DVAMikyZeq1eIRu7oZgabws"

# Загружаем задания
def load_tasks():
    with open("TgBot/tasks.json", "r", encoding="utf-8") as f:
        return json.load(f)

tasks = load_tasks()

# Приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"День {i}", callback_data=f"day_{i}")]
        for i in range(1, 8)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Это твой бот с заданиями на 7 дней. Выбери день:", reply_markup=reply_markup
    )

# Обработка нажатий
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data.split("_")[1]
    task = tasks.get(day)
    if task:
        await query.edit_message_text(f"📅 День {day}:\n\n{task}")
    else:
        await query.edit_message_text("❌ Задание не найдено.")

# Главная асинхронная функция
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    await app.initialize()
    await app.start()
    print("✅ Бот запущен")
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())