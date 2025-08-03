import asyncio
from telegram.ext import ApplicationBuilder
import telegram

print("python-telegram-bot version:", telegram.__version__)

async def main():
    app = ApplicationBuilder().token("YOUR_TOKEN_HERE").build()
    print("App created successfully")

asyncio.run(main())