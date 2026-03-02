"""
Telegram bot command handlers
"""
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.error import RetryAfter, TimedOut, NetworkError
from telegram.ext import ContextTypes

from src.services.food_service import FoodService
from src.services.database_service import DatabaseService
from src.services.graph_service import GraphService

logger = logging.getLogger(__name__)

# Initialize services
food_service = FoodService()
storage_service = DatabaseService()  # Using persistent database storage
graph_service = GraphService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    user = update.effective_user
    user_id = user.id
    
    # Create or update user
    storage_service.create_user(
        telegram_user_id=user_id,
        name=user.first_name,
        username=user.username
    )
    
    welcome_message = f"""
👋 Welcome to Calorie Tracker Bot, {user.first_name}!

I'll help you track your daily calories and macros effortlessly.

📝 **Available Commands:**

/log <food> - Log your food intake
   Example: /log 2 eggs and 1 dosa

/today - View today's total calories and macros

/history - See your last 7 days summary

/graph - Get a visual calorie trend graph

/reset - Clear today's entries

💡 **Quick Tips:**
• Be specific with quantities (e.g., "2 eggs", "1 cup rice")
• You can log multiple items at once
• Use /today anytime to check your progress

Let's start tracking! Try: /log 2 eggs and 1 toast
"""
    
    await update.message.reply_text(welcome_message)
    logger.info(f"User {user_id} started the bot")


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /log command"""
    user_id = update.effective_user.id
    
    # Get the food text after /log
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify what you ate!\n\n"
            "Example: /log 2 eggs and 1 dosa"
        )
        return
    
    food_text = ' '.join(context.args)
    
    try:
        # Create food entry using food service
        entry = food_service.create_food_entry(user_id, food_text)
        
        # Store the entry
        storage_service.add_food_entry(entry)
        
        # Get today's total
        today_entries = storage_service.get_today_entries(user_id)
        daily_total = food_service.calculate_daily_total(today_entries)
        
        # Build item breakdown
        items_text = "\n".join([
            f"  • {item.name}: {item.nutrition.calories:.0f} kcal"
            for item in entry.items
        ])
        
        response = f"""
✅ **Logged:** {food_text}

📊 **Nutrition Breakdown:**
{items_text}

**Total for this entry:**
• Calories: {entry.total_nutrition.calories:.0f} kcal
• Protein: {entry.total_nutrition.protein:.1f}g
• Carbs: {entry.total_nutrition.carbs:.1f}g
• Fats: {entry.total_nutrition.fats:.1f}g

📈 **Today's Total:**
• Calories: {daily_total.calories:.0f} kcal
• Protein: {daily_total.protein:.1f}g
• Carbs: {daily_total.carbs:.1f}g
• Fats: {daily_total.fats:.1f}g

Great job tracking! 💪
"""
        
        await update.message.reply_text(response)
        logger.info(f"User {user_id} logged: {food_text}")
        
    except Exception as e:
        logger.error(f"Error logging food for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, I couldn't process that food entry.\n"
            "Please try again with a different format."
        )


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /today command"""
    user_id = update.effective_user.id
    
    try:
        # Get today's entries
        today_entries = storage_service.get_today_entries(user_id)
        
        if not today_entries:
            await update.message.reply_text(
                "📭 No entries logged today!\n\n"
                "Start tracking with: /log <food>"
            )
            return
        
        # Calculate totals
        daily_total = food_service.calculate_daily_total(today_entries)
        
        # Build entry list
        entry_list = "\n".join([
            f"• {e.food_text} ({e.total_nutrition.calories:.0f} kcal)"
            for e in today_entries
        ])
        
        response = f"""
📅 **Today's Summary** ({datetime.now().strftime('%B %d, %Y')})

🍽️ **Meals Logged ({len(today_entries)}):**
{entry_list}

📊 **Total Nutrition:**
• Calories: {daily_total.calories:.0f} kcal
• Protein: {daily_total.protein:.1f}g
• Carbs: {daily_total.carbs:.1f}g
• Fats: {daily_total.fats:.1f}g

💡 Keep up the great work! 🎯
"""
        
        await update.message.reply_text(response)
        logger.info(f"User {user_id} checked today's summary")
        
    except Exception as e:
        logger.error(f"Error getting today's summary for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Sorry, I couldn't retrieve today's summary.\n"
            "Please try again."
        )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /history command"""
    user_id = update.effective_user.id
    
    try:
        # Get 7-day history
        history = storage_service.get_history(user_id, days=7)
        
        if not history or all(h.entry_count == 0 for h in history):
            await update.message.reply_text(
                "📭 No history available yet!\n\n"
                "Start tracking with: /log <food>"
            )
            return
        
        # Build history message
        history_lines = []
        total_calories = 0
        days_with_data = 0
        
        for day in history:
            if day.entry_count > 0:
                date_str = day.date.strftime('%b %d')
                if day.date.date() == datetime.now().date():
                    date_str += " (Today)"
                
                history_lines.append(
                    f"📅 {date_str}: {day.calories:.0f} kcal | "
                    f"P: {day.protein:.0f}g | C: {day.carbs:.0f}g | F: {day.fats:.0f}g"
                )
                total_calories += day.calories
                days_with_data += 1
        
        if days_with_data == 0:
            await update.message.reply_text(
                "📭 No history available yet!\n\n"
                "Start tracking with: /log <food>"
            )
            return
        
        avg_calories = total_calories / days_with_data if days_with_data > 0 else 0
        
        response = f"""
📊 **7-Day History**

{chr(10).join(history_lines)}

📈 **Average:** {avg_calories:.0f} kcal/day ({days_with_data} days tracked)

💡 Use /graph to see your calorie trend!
"""
        
        await update.message.reply_text(response)
        logger.info(f"User {user_id} viewed history")
        
    except Exception as e:
        logger.error(f"Error getting history for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Sorry, I couldn't retrieve your history.\n"
            "Please try again."
        )


async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /graph command"""
    user_id = update.effective_user.id
    
    try:
        # Get history data
        history = storage_service.get_history(user_id, days=7)
        
        if not history or all(h.entry_count == 0 for h in history):
            await update.message.reply_text(
                "📭 Not enough data to generate a graph!\n\n"
                "Start tracking with: /log <food>"
            )
            return
        
        # Send "generating" message
        status_message = await update.message.reply_text(
            "📊 Generating your calorie trend graph...\n"
            "Please wait a moment..."
        )
        
        # Generate the graph
        graph_buffer = graph_service.generate_calorie_trend_graph(
            history=history,
            title=f"Calorie Trend - Last 7 Days"
        )
        
        if graph_buffer:
            # Send the graph as a photo
            await update.message.reply_photo(
                photo=graph_buffer,
                caption=f"""
📊 **Your Calorie Trend**

📈 **Summary:**
• Days tracked: {len([h for h in history if h.entry_count > 0])}
• Total entries: {sum(h.entry_count for h in history)}
• Average: {sum(h.calories for h in history if h.entry_count > 0) / len([h for h in history if h.entry_count > 0]):.0f} kcal/day

💡 Keep tracking to see your progress!
"""
            )
            
            # Delete status message
            await status_message.delete()
            
            logger.info(f"User {user_id} received graph")
        else:
            await status_message.edit_text(
                "❌ Could not generate graph. Not enough data."
            )
        
    except Exception as e:
        logger.error(f"Error generating graph for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Sorry, I couldn't generate the graph.\n"
            "Please try again or check if matplotlib is installed."
        )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /reset command"""
    user_id = update.effective_user.id
    
    try:
        # Get today's entries count
        today_entries = storage_service.get_today_entries(user_id)
        
        if not today_entries:
            await update.message.reply_text(
                "📭 No entries logged today to reset!"
            )
            return
        
        # Delete today's entries
        deleted_count = storage_service.delete_today_entries(user_id)
        
        response = f"""
🗑️ **Reset Complete!**

Cleared {deleted_count} entries from today.

Your history from previous days is still intact.

Ready to start fresh! Use /log to track your meals.
"""
        
        await update.message.reply_text(response)
        logger.info(f"User {user_id} reset today's entries ({deleted_count} deleted)")
        
    except Exception as e:
        logger.error(f"Error resetting entries for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Sorry, I couldn't reset today's entries.\n"
            "Please try again."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command"""
    help_text = """
📚 **Calorie Tracker Bot - Help**

**Available Commands:**

/start - Initialize and see welcome message
/log <food> - Log your food intake
/today - View today's summary
/history - See last 7 days
/graph - Get calorie trend graph
/reset - Clear today's entries
/help - Show this help message

**Usage Examples:**

✅ /log 2 eggs and 1 toast
✅ /log 1 cup rice with dal
✅ /log chicken breast 150g
✅ /log apple and banana

**Supported Foods:**
Indian: dosa, idli, roti, chapati, dal, rice, paratha, upma, samosa
Proteins: eggs, chicken, paneer, milk
Fruits: banana, apple
Others: bread, toast, butter, ghee

**Tips:**
• Be specific with quantities
• You can log multiple items at once
• Check /today regularly to track progress
• Use /history to see trends

Need more help? Contact support!
"""
    
    await update.message.reply_text(help_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages (non-commands)"""
    message_text = update.message.text
    
    response = f"""
💬 I received: "{message_text}"

To log this as food, use:
/log {message_text}

Or try these commands:
• /today - View today's summary
• /history - See your 7-day history
• /help - Get help
"""
    
    await update.message.reply_text(response)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler.

    Handles Telegram-specific errors gracefully:
    - RetryAfter : Telegram rate-limit — wait the requested seconds, then
                   silently drop the update (the user can retry).
    - TimedOut   : transient network timeout — log and ignore.
    - NetworkError: transient connectivity issue — log and ignore.
    - Everything else: log and notify the user if possible.
    """
    error = context.error

    if isinstance(error, RetryAfter):
        retry_after = int(error.retry_after)
        logger.warning(
            "Telegram rate-limit hit (RetryAfter %ds) — waiting before next request",
            retry_after,
        )
        await asyncio.sleep(retry_after)
        # Do NOT reply to the user — the update is dropped after the wait.
        return

    if isinstance(error, TimedOut):
        logger.warning("Telegram request timed out — ignoring: %s", error)
        return

    if isinstance(error, NetworkError):
        logger.warning("Telegram network error — ignoring: %s", error)
        return

    # Unexpected error — log with full traceback and notify user if possible
    logger.error("Unhandled error for update %s: %s", update, error, exc_info=error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Oops! Something went wrong.\n\n"
                "Please try again or use /help for assistance."
            )
        except Exception:
            pass  # don't let the reply itself cause another error

# Made with Bob
