# Project Structure

This document describes the modular architecture of the Telegram Calorie Tracker Bot.

## Directory Structure

```
calorie-tracker/
├── src/                          # Source code
│   ├── __init__.py
│   ├── api/                      # FastAPI Backend
│   │   ├── __init__.py
│   │   └── main.py              # REST API endpoints
│   ├── bot/                      # Telegram Bot
│   │   ├── __init__.py
│   │   ├── bot_app.py           # Bot application setup
│   │   └── handlers.py          # Command handlers
│   ├── services/                 # Business Logic
│   │   ├── __init__.py
│   │   ├── food_service.py      # Food parsing & nutrition
│   │   └── storage_service.py   # Data storage
│   ├── models/                   # Data Models
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic schemas
│   └── utils/                    # Utilities
│       └── __init__.py
├── config.py                     # Configuration management
├── run_bot.py                    # Bot entry point
├── run_api.py                    # API entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── README.md                     # User documentation
├── DESIGN_DOCUMENTATION.md       # Design specs
└── PROJECT_STRUCTURE.md          # This file
```

## Component Overview

### 1. API Layer (`src/api/`)

**Purpose:** REST API backend for webhook integration and external access

**Files:**
- `main.py` - FastAPI application with endpoints

**Key Endpoints:**
- `POST /api/log` - Log food entry
- `GET /api/user/{id}/today` - Get today's summary
- `GET /api/user/{id}/entries` - Get user entries
- `GET /api/user/{id}/history` - Get history
- `DELETE /api/user/{id}/today` - Reset today
- `POST /webhook` - Telegram webhook (future)

**Usage:**
```bash
python run_api.py
# API runs on http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 2. Bot Layer (`src/bot/`)

**Purpose:** Telegram bot interface and command handling

**Files:**
- `bot_app.py` - Bot initialization and configuration
- `handlers.py` - Command handlers for all bot commands

**Commands Implemented:**
- `/start` - Welcome message
- `/log <food>` - Log food intake
- `/today` - Today's summary
- `/history` - 7-day history
- `/graph` - Calorie trend
- `/reset` - Clear today's entries
- `/help` - Help message

**Usage:**
```bash
python run_bot.py
# Bot runs in polling mode
```

### 3. Services Layer (`src/services/`)

**Purpose:** Business logic and data operations

**Files:**

#### `food_service.py`
- Food text parsing
- Nutrition lookup
- Macro calculations
- Food entry creation

**Key Methods:**
```python
parse_food_text(text) -> List[Tuple[quantity, food_name]]
get_nutrition(food_name, quantity) -> Dict
create_food_entry(user_id, text) -> FoodEntry
calculate_daily_total(entries) -> NutritionInfo
```

#### `storage_service.py`
- In-memory data storage
- User management
- Entry CRUD operations
- History retrieval

**Key Methods:**
```python
create_user(user_id, name) -> User
add_food_entry(entry) -> FoodEntry
get_today_entries(user_id) -> List[FoodEntry]
get_history(user_id, days) -> List[HistoryEntry]
delete_today_entries(user_id) -> int
```

### 4. Models Layer (`src/models/`)

**Purpose:** Data structures and schemas

**Files:**
- `schemas.py` - Pydantic models for data validation

**Key Models:**
```python
NutritionInfo      # Calories, protein, carbs, fats
FoodItem           # Individual food item
FoodEntry          # Complete food entry
DailySummary       # Daily totals
User               # User information
HistoryEntry       # Historical data point
```

### 5. Configuration (`config.py`)

**Purpose:** Centralized configuration management

**Features:**
- Environment variable loading
- Configuration validation
- Default values

**Usage:**
```python
from config import config
token = config.TELEGRAM_BOT_TOKEN
```

## Data Flow

### Logging Food (Bot → Services → Storage)

```
User sends: /log 2 eggs and 1 dosa
    ↓
handlers.log_command()
    ↓
food_service.create_food_entry()
    ├─ parse_food_text() → [(2, 'eggs'), (1, 'dosa')]
    ├─ get_nutrition() → nutrition data
    └─ create FoodEntry object
    ↓
storage_service.add_food_entry()
    ↓
Response sent to user
```

### Getting Summary (Bot → Storage → Services)

```
User sends: /today
    ↓
handlers.today_command()
    ↓
storage_service.get_today_entries()
    ↓
food_service.calculate_daily_total()
    ↓
Response sent to user
```

## Running the Application

### Option 1: Bot Only (Polling Mode)
```bash
# Set up environment
cp .env.example .env
# Edit .env with your bot token

# Install dependencies
pip install -r requirements.txt

# Run bot
python run_bot.py
```

### Option 2: API Only
```bash
# Run API server
python run_api.py

# Access API docs
open http://localhost:8000/docs
```

### Option 3: Both (Development)
```bash
# Terminal 1: Run bot
python run_bot.py

# Terminal 2: Run API
python run_api.py
```

## Key Features

### ✅ Implemented
- Modular architecture
- Separation of concerns
- Food parsing with regex
- Indian food database (20+ items)
- In-memory storage
- All bot commands
- REST API endpoints
- Error handling
- Logging

### 🚧 Future Enhancements
- Database integration (SQLite/PostgreSQL)
- Graph generation with matplotlib
- Webhook mode for production
- External nutrition API integration
- User preferences
- Goal tracking
- Export functionality

## Development Guidelines

### Adding a New Food Item
Edit `src/services/food_service.py`:
```python
self.nutrition_db = {
    'new_food': {
        'calories': 100,
        'protein': 5,
        'carbs': 15,
        'fats': 3,
        'unit': 'piece'
    }
}
```

### Adding a New Command
1. Add handler in `src/bot/handlers.py`
2. Register in `src/bot/bot_app.py`
3. Add API endpoint in `src/api/main.py` (if needed)

### Adding a New Service
1. Create file in `src/services/`
2. Import in handlers/API as needed
3. Follow existing patterns

## Testing

### Manual Testing
```bash
# Test bot commands
/start
/log 2 eggs
/today
/history
/reset

# Test API endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/log \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id": 123, "food_text": "2 eggs"}'
```

## Deployment

### Bot Deployment
- Use webhook mode for production
- Deploy to IBM Code Engine
- Set environment variables
- Configure webhook URL

### API Deployment
- Deploy FastAPI to IBM Code Engine
- Set up database connection
- Configure CORS
- Enable monitoring

## Architecture Benefits

1. **Modularity** - Each component has a single responsibility
2. **Testability** - Services can be tested independently
3. **Scalability** - Easy to add new features
4. **Maintainability** - Clear structure and separation
5. **Flexibility** - Can run bot and API separately or together

## Migration Notes

The old `bot.py` file has been replaced with the modular structure. To migrate:

1. Delete old `bot.py`
2. Use `run_bot.py` instead
3. All functionality is preserved
4. New features available via API

---

**Last Updated:** 2026-02-27
**Version:** 2.0 (Modular Architecture)