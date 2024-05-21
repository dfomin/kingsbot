import asyncio
import json
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("today")
    """Send a message when the command /help is issued."""
    await update.message.reply_text("TODAY!")


def create_application() -> Application:
    """Create an Application for handling updates."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("today", today_command))

    return app


application = create_application()


async def process_update(event_body):
    """Process a single update."""
    async with application:
        update = Update.de_json(json.loads(event_body), application.bot)
        await application.process_update(update)


def lambda_handler(event, context):
    print(event)
    """Lambda function handler for processing Telegram updates."""
    try:
        event_body = event.get("body")
        print(event_body)
        asyncio.run(process_update(event_body))
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return {"statusCode": 200}
