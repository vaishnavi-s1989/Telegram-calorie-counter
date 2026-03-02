"""
FastAPI Backend Application

Serves two purposes:
  1. REST API for calorie tracking (all environments)
  2. Telegram webhook receiver (IBM Code Engine / production)

On IBM Code Engine:
  - The container simply exposes POST /webhook.
  - The webhook URL is registered with Telegram ONCE manually (see
    IBM_CLOUD_DEPLOYMENT.md Step 10).  The app never calls set_webhook
    or delete_webhook at startup/shutdown — this avoids Telegram API
    rate-limit errors (RetryAfter) during container restarts.

Local development:
  - WEBHOOK_MODE=false (default) -> run_bot.py handles polling separately.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Request, Header, status
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update

from config import config
from src.models.schemas import (
    LogFoodRequest,
    LogFoodResponse,
    FoodEntry,
    DailySummary,
    HistoryEntry,
)
from src.services.food_service import FoodService
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Webhook mode: initialise the bot Application so it is ready to process
    updates forwarded by POST /webhook.  The webhook URL itself is registered
    with Telegram once manually — NOT at every container startup — to avoid
    Telegram API rate-limit (RetryAfter) errors during rolling restarts.

    Polling mode: nothing to do here; run_bot.py manages the bot process.
    """
    if config.WEBHOOK_MODE:
        from src.bot.bot_app import get_bot_application

        bot_app = get_bot_application()
        await bot_app.initialize()
        logger.info("Bot application initialised — ready to receive webhook updates")

        yield  # application is running

        await bot_app.shutdown()
        logger.info("Bot application shut down")
    else:
        logger.info("Webhook mode disabled — bot runs via polling (run_bot.py)")
        yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Calorie Tracker API",
    description=(
        "Backend API for Telegram Calorie Tracker Bot. "
        "Deployed on IBM Code Engine."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — restrict origins in production via environment variable if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Service singletons
# ---------------------------------------------------------------------------
food_service    = FoodService()
storage_service = DatabaseService()


# ---------------------------------------------------------------------------
# Health / root endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Root endpoint — useful for IBM Code Engine health probes."""
    return {
        "message": "Calorie Tracker API",
        "version": "1.0.0",
        "status":  "running",
        "env":     config.APP_ENV,
        "mode":    "webhook" if config.WEBHOOK_MODE else "polling",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    IBM Code Engine uses this for liveness / readiness probes.
    Must return HTTP 200 within the probe timeout.
    """
    return {
        "status":    "healthy",
        "timestamp": datetime.now().isoformat(),
        "db":        "postgresql" if config.is_postgres() else "sqlite",
    }


# ---------------------------------------------------------------------------
# Telegram Webhook endpoint
# ---------------------------------------------------------------------------

@app.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=None),
):
    """
    Receive Telegram updates via webhook.

    Security: Telegram sends the WEBHOOK_SECRET in the
    X-Telegram-Bot-Api-Secret-Token header.  We reject requests that
    don't carry the correct token to prevent spoofed updates.

    This endpoint is only active when WEBHOOK_MODE=true (IBM Code Engine).
    """
    # Validate secret token
    if config.WEBHOOK_SECRET and x_telegram_bot_api_secret_token != config.WEBHOOK_SECRET:
        logger.warning("Webhook received with invalid secret token — rejected")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token",
        )

    # Parse the incoming update
    try:
        data = await request.json()
        update = Update.de_json(data, None)  # bot set below
    except Exception as e:
        logger.error("Failed to parse Telegram update: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid update payload",
        )

    # Forward to the bot application for processing
    try:
        from src.bot.bot_app import get_bot_application
        bot_app = get_bot_application()

        # Attach the bot instance to the update (required by PTB)
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
    except Exception as e:
        logger.error("Error processing Telegram update: %s", e, exc_info=True)
        # Always return 200 to Telegram — otherwise it will retry indefinitely
        return {"status": "error", "detail": str(e)}

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Food logging API
# ---------------------------------------------------------------------------

@app.post("/api/log", response_model=LogFoodResponse)
async def log_food(request: LogFoodRequest):
    """Log a food entry for a user."""
    try:
        entry        = food_service.create_food_entry(
            telegram_user_id=request.telegram_user_id,
            food_text=request.food_text,
        )
        stored_entry = storage_service.add_food_entry(entry)
        today_entries = storage_service.get_today_entries(request.telegram_user_id)
        daily_total  = food_service.calculate_daily_total(today_entries)

        return LogFoodResponse(
            success=True,
            message="Food logged successfully",
            entry=stored_entry,
            daily_total=daily_total,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging food: {e}",
        )


@app.get("/api/user/{telegram_user_id}/today", response_model=DailySummary)
async def get_today_summary(telegram_user_id: int):
    """Get today's nutrition summary for a user."""
    try:
        return storage_service.get_daily_summary(telegram_user_id, datetime.now())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting summary: {e}",
        )


@app.get("/api/user/{telegram_user_id}/entries", response_model=List[FoodEntry])
async def get_user_entries(telegram_user_id: int, date: str | None = None):
    """Get food entries for a user (today or a specific ISO date)."""
    try:
        if date:
            target_date = datetime.fromisoformat(date)
            return storage_service.get_entries_by_date(telegram_user_id, target_date)
        return storage_service.get_today_entries(telegram_user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting entries: {e}",
        )


@app.get("/api/user/{telegram_user_id}/history", response_model=List[HistoryEntry])
async def get_user_history(telegram_user_id: int, days: int = 7):
    """Get the last N days of history for a user."""
    try:
        return storage_service.get_history(telegram_user_id, days)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting history: {e}",
        )


@app.delete("/api/user/{telegram_user_id}/today")
async def reset_today(telegram_user_id: int):
    """Delete all of today's entries for a user."""
    try:
        deleted_count = storage_service.delete_today_entries(telegram_user_id)
        return {
            "success":       True,
            "message":       f"Deleted {deleted_count} entries",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting entries: {e}",
        )


@app.delete("/api/user/{telegram_user_id}/entry/{entry_id}")
async def delete_entry(telegram_user_id: int, entry_id: int):
    """Delete a specific food entry."""
    try:
        success = storage_service.delete_entry(telegram_user_id, entry_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry not found",
            )
        return {"success": True, "message": "Entry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting entry: {e}",
        )


# ---------------------------------------------------------------------------
# Local dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)

# Made with Bob
