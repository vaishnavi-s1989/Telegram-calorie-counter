"""
Telegram Bot Application
Supports two run modes:
  - Polling mode  : local development (default when WEBHOOK_MODE=false)
  - Webhook mode  : IBM Code Engine / production (WEBHOOK_MODE=true)

In webhook mode the bot does NOT start its own server and does NOT
register/deregister the webhook at startup/shutdown.  The webhook URL
is set once manually (see IBM_CLOUD_DEPLOYMENT.md).  The FastAPI app
in src/api/main.py receives updates via POST /webhook and forwards
them to the Application instance returned by get_bot_application().
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import config
from src.bot.handlers import (
    start_command,
    log_command,
    today_command,
    history_command,
    graph_command,
    reset_command,
    help_command,
    handle_message,
    error_handler,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if config.DEBUG else logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level Application instance
# Shared between polling runner and the FastAPI webhook endpoint.
# ---------------------------------------------------------------------------
_application: Application | None = None


def create_bot_application() -> Application:
    """Build and configure the python-telegram-bot Application."""
    try:
        config.validate()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        raise

    builder = Application.builder().token(config.TELEGRAM_BOT_TOKEN)

    # In webhook mode we manage the lifecycle manually (no built-in HTTP
    # server), so disable the default updater.
    if config.WEBHOOK_MODE:
        builder = builder.updater(None)

    application = builder.build()

    # ---- Command handlers ----
    application.add_handler(CommandHandler("start",   start_command))
    application.add_handler(CommandHandler("log",     log_command))
    application.add_handler(CommandHandler("today",   today_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("graph",   graph_command))
    application.add_handler(CommandHandler("reset",   reset_command))
    application.add_handler(CommandHandler("help",    help_command))

    # ---- Free-text message handler ----
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # ---- Error handler ----
    application.add_error_handler(error_handler)

    logger.info(
        "Bot application created | mode=%s",
        "webhook" if config.WEBHOOK_MODE else "polling",
    )
    return application


def get_bot_application() -> Application:
    """
    Return the singleton Application, creating it on first call.
    Used by the FastAPI webhook endpoint to process incoming updates.
    """
    global _application
    if _application is None:
        _application = create_bot_application()
    return _application


def run_bot_polling() -> None:
    """
    Run the bot in long-polling mode.
    Use this for local development only — NOT for IBM Code Engine.
    """
    try:
        application = create_bot_application()

        logger.info("Starting bot in polling mode...")
        print("🤖 Bot is running in polling mode! Press Ctrl+C to stop.")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please set TELEGRAM_BOT_TOKEN (and WEBHOOK_URL if WEBHOOK_MODE=true) in your .env file")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n👋 Bot stopped!")
    except Exception as e:
        logger.error("Error running bot: %s", e, exc_info=True)
        print(f"❌ Error: {e}")
        print("\nTry reinstalling dependencies:")
        print("pip install --upgrade python-telegram-bot")


# ---------------------------------------------------------------------------
# Entry point for local polling (python src/bot/bot_app.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_bot_polling()

# Made with Bob
