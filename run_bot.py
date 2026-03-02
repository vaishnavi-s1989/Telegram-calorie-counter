"""
Main entry point for running the Telegram bot in polling mode.
Use this for local development only.
For IBM Code Engine production, the bot runs in webhook mode
via the FastAPI app (src/api/main.py).
"""
from src.bot.bot_app import run_bot_polling

if __name__ == '__main__':
    run_bot_polling()

# Made with Bob
