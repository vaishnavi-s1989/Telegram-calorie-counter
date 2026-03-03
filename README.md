# Telegram Calorie Tracker Bot

A lightweight, conversational Telegram bot for tracking calories and macronutrients with a modular architecture.

## Features

- 📝 Log food intake via simple text commands
- 📊 Track calories, protein, carbs, and fats
- 📅 View daily summaries and 7-day history
- 📈 Generate calorie trend graphs (coming soon)
- 💬 Conversational interface - no app installation needed
- 🏗️ Modular architecture with separate API and bot components
- 🌐 **USDA FoodData Central API integration** - Access to 300,000+ foods
- 🍛 Fallback database for Indian foods and common items

## Architecture

This project uses a modular architecture:
- **Bot Layer** - Telegram bot interface
- **API Layer** - FastAPI REST endpoints
- **Services Layer** - Business logic (food parsing, storage)
- **Models Layer** - Data schemas

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed architecture documentation.

## Quick Start

### Prerequisites

- Python 3.9 or higher
- A Telegram account
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a Telegram Bot**
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow the instructions
   - Copy the bot token you receive

4. **Get a USDA API Key (Required)**
   - Visit: https://fdc.nal.usda.gov/api-key-signup.html
   - Sign up for a free API key (instant approval)
   - You'll receive the key via email

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   USDA_API_KEY=your_usda_api_key_here
   ```

6. **Test the USDA API integration**
   ```bash
   python test_usda_integration.py
   ```
   
   You should see successful test results for food lookups.

7. **Run the bot**
   ```bash
   python run_bot.py
   ```

   You should see:
   ```
   🤖 Bot is running! Press Ctrl+C to stop.
   ```

8. **Start chatting with your bot**
   - Open Telegram
   - Search for your bot by username
   - Send `/start` to begin!

### Optional: Run the API Server

```bash
# In a separate terminal
python run_api.py

# Access API documentation
open http://localhost:8000/docs
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot and see welcome message | `/start` |
| `/log` | Log food intake | `/log 2 eggs and 1 dosa` |
| `/today` | View today's calorie and macro summary | `/today` |
| `/history` | See last 7 days summary | `/history` |
| `/graph` | Get calorie trend graph | `/graph` |
| `/reset` | Clear today's entries | `/reset` |
| `/help` | Show help message | `/help` |

## Usage Examples

### Logging Food

```
/log 2 eggs and 1 toast
/log 1 cup rice with dal
/log chicken breast 150g
/log apple and banana
```

### Checking Progress

```
/today          # See today's total
/history        # View 7-day summary
/graph          # Get visual trend
```

## Project Structure

```
calorie-tracker/
├── src/
│   ├── api/                  # FastAPI backend
│   │   └── main.py
│   ├── bot/                  # Telegram bot
│   │   ├── bot_app.py
│   │   └── handlers.py
│   ├── services/             # Business logic
│   │   ├── food_service.py   # Food parsing & nutrition
│   │   ├── usda_service.py   # USDA API integration
│   │   └── storage_service.py
│   └── models/               # Data schemas
│       └── schemas.py
├── config.py                 # Configuration
├── run_bot.py               # Bot entry point
├── run_api.py               # API entry point
├── test_usda_integration.py # USDA API test script
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
├── DESIGN_DOCUMENTATION.md  # Design specs
├── PROJECT_STRUCTURE.md     # Architecture docs
├── USDA_API_INTEGRATION.md  # USDA API documentation
└── README.md                # This file
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed architecture documentation.
See [USDA_API_INTEGRATION.md](USDA_API_INTEGRATION.md) for USDA API integration details.

## Current Status

### ✅ Implemented

- ✅ Modular architecture (API, Bot, Services, Models)
- ✅ All command handlers (`/start`, `/log`, `/today`, `/history`, `/graph`, `/reset`)
- ✅ Food parsing with regex
- ✅ **USDA FoodData Central API integration** (300,000+ foods)
- ✅ Fallback database for Indian foods (20+ items: dosa, idli, roti, dal, etc.)
- ✅ In-memory data storage
- ✅ REST API endpoints
- ✅ Nutrition calculations
- ✅ User-friendly responses
- ✅ Error handling and logging
- ✅ Database integration (SQLite/PostgreSQL)
- ✅ Graph generation with matplotlib
- ✅ Webhook mode for production deployment

### 🚧 Coming Soon

- Edit/delete specific entries
- Weekly PDF reports
- Goal tracking
- Meal planning suggestions

## Development

### Running in Development Mode

```bash
# Set debug mode in .env
DEBUG=True

# Run the bot
python run_bot.py

# Or run the API
python run_api.py
```

### Testing Commands

Once the bot is running, test each command:

1. `/start` - Should show welcome message
2. `/log 2 eggs and 1 dosa` - Should log food with real nutrition data
3. `/today` - Should show today's summary
4. `/history` - Should show 7-day history
5. `/graph` - Should show text-based graph
6. `/reset` - Should clear today's entries

### Testing API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Log food
curl -X POST http://localhost:8000/api/log \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id": 123, "food_text": "2 eggs and 1 dosa"}'

# Get today's summary
curl http://localhost:8000/api/user/123/today

# Get history
curl http://localhost:8000/api/user/123/history?days=7
```

### API Documentation

When running the API, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Bot doesn't respond

- Check if `bot.py` is running
- Verify your bot token in `.env`
- Ensure you're messaging the correct bot

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Configuration errors

```bash
# Check your .env file
cat .env

# Make sure TELEGRAM_BOT_TOKEN is set
```

## Next Steps

1. **Test the mock bot** - Verify all commands work
2. **Add database** - Implement SQLite for persistent storage
3. **Food parsing** - Add real food text parsing logic
4. **Nutrition API** - Integrate Open Food Facts API
5. **Graph generation** - Implement matplotlib charts
6. **Deploy** - Deploy to IBM Code Engine

## Contributing

This is a personal project, but suggestions are welcome!

## License

MIT License - Feel free to use and modify

## Support

For issues or questions:
- Check the `/help` command in the bot
- Review `DESIGN_DOCUMENTATION.md` for architecture details
- Open an issue in the repository

---

**Happy Tracking! 🎯💪**