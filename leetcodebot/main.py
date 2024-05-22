import asyncio
import json
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler

from leetcodebot.rank import send_rank
from leetcodebot.today import send_today
from leetcodebot.status import send_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def create_application() -> Application:
    """Create an Application for handling updates."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("rank", send_rank))
    app.add_handler(CommandHandler("today", send_today))
    app.add_handler(CommandHandler("status", send_status))

    return app


application = create_application()


async def process_update(event_body):
    """Process a single update."""
    async with application:
        update = Update.de_json(json.loads(event_body), application.bot)
        await application.process_update(update)


def lambda_handler(event, context):
    """Lambda function handler for processing Telegram updates."""
    try:
        event_body = event.get("body")
        asyncio.run(process_update(event_body))
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return {"statusCode": 200}


if __name__ == '__main__':
    application.run_polling()
