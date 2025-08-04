import logging import json from aiohttp import web from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update from telegram.ext import ( Application, CallbackContext, CallbackQueryHandler, CommandHandler, ContextTypes )

Замените на ваш токен

TOKEN = "8467489835:AAF09FNV4dW1DVAMikyZeq1eIRu7oZgabws"

Включаем логирование

logging.basicConfig(level=logging.INFO) logger = logging.getLogger(name)

Загрузка заданий из JSON-файла

def load_tasks(): with open("tasks.json", encoding="utf-8") as f: return json.load(f)

TASKS = load_tasks()

Команда /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): keyboard = [[InlineKeyboardButton(f"День {i+1}", callback_data=f"day_{i+1}")] for i in range(7)] reply_markup = InlineKeyboardMarkup(keyboard)

await update.message.reply_text(
    "👋 Привет! Добро пожаловать в тренировочный бот!\nВыбери день, чтобы получить задание:",
    reply_markup=reply_markup
)

Обработка кнопок дней

async def day_callback(update: Update, context: CallbackContext): query = update.callback_query await query.answer()

day_index = int(query.data.split("_")[1]) - 1
day_tasks = TASKS.get(f"day_{day_index+1}", [])

if day_tasks:
    response = f"📅 <b>День {day_index+1}</b>\n\n"
    for idx, task in enumerate(day_tasks, 1):
        response += f"<b>Задание {idx}:</b> {task}\n"
else:
    response = "❌ Заданий на этот день пока нет."

await query.edit_message_text(
    text=response,
    parse_mode="HTML"
)

Webhook обработчик

async def handler(request): data = await request.json() update = Update.de_json(data, application.bot) await application.initialize() await application.process_update(update) return web.Response()

Основной код запуска

app = web.Application() app.router.add_post("/webhook/{token}", handler)

application = Application.builder().token(TOKEN).build() application.add_handler(CommandHandler("start", start)) application.add_handler(CallbackQueryHandler(day_callback))

if name == 'main': web.run_app(app, port=10000)

