# Database Information

## Overview

The application now uses **SQLite** for persistent data storage. All your food entries and user data are saved to a database file and will persist across server restarts.

## Database File

- **Location:** `calorie_tracker.db` (in project root)
- **Type:** SQLite3
- **Created automatically** on first run

## Database Schema

### Tables

#### 1. **users**
Stores user information from Telegram.

| Column | Type | Description |
|--------|------|-------------|
| telegram_user_id | INTEGER (PK) | Telegram user ID |
| name | TEXT | User's first name |
| username | TEXT | Telegram username |
| created_at | TEXT | Account creation timestamp |
| last_active | TEXT | Last activity timestamp |

#### 2. **food_entries**
Stores all food logging entries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment entry ID |
| telegram_user_id | INTEGER (FK) | User who logged the entry |
| date | TEXT | Date of entry (ISO format) |
| food_text | TEXT | Original text input |
| items_json | TEXT | JSON array of food items |
| total_calories | REAL | Total calories |
| total_protein | REAL | Total protein (g) |
| total_carbs | REAL | Total carbs (g) |
| total_fats | REAL | Total fats (g) |
| timestamp | TEXT | Entry timestamp |

### Indexes

- `idx_user_date` - On (telegram_user_id, date) for fast date queries
- `idx_user_timestamp` - On (telegram_user_id, timestamp) for chronological queries

## Features

### ✅ Persistent Storage
- All data survives server restarts
- No data loss when bot is stopped
- Automatic database creation on first run

### ✅ Efficient Queries
- Indexed for fast lookups
- Optimized for date-based queries
- Supports range queries for history

### ✅ Data Integrity
- Foreign key constraints
- Proper data types
- JSON storage for complex data

## Usage

### Automatic Initialization

The database is automatically created when you first run the bot:

```bash
python run_bot.py
```

On first run, you'll see:
```
Database initialized: calorie_tracker.db
Tables created: users, food_entries
```

### Viewing Database

You can view the database using any SQLite client:

```bash
# Using sqlite3 command line
sqlite3 calorie_tracker.db

# View tables
.tables

# View users
SELECT * FROM users;

# View recent entries
SELECT * FROM food_entries ORDER BY timestamp DESC LIMIT 10;

# Exit
.quit
```

### Backup Database

To backup your data:

```bash
# Simple copy
cp calorie_tracker.db calorie_tracker_backup.db

# Or use SQLite backup
sqlite3 calorie_tracker.db ".backup calorie_tracker_backup.db"
```

### Restore Database

To restore from backup:

```bash
# Stop the bot first
# Then copy backup
cp calorie_tracker_backup.db calorie_tracker.db

# Restart bot
python run_bot.py
```

## Migration from In-Memory Storage

If you were using the old in-memory storage:

1. **Old data is lost** - In-memory storage doesn't persist
2. **Start fresh** - New entries will be saved to database
3. **No migration needed** - Just restart the bot

## Database Location

The database file is created in the project root directory:

```
calorie-tracker/
├── calorie_tracker.db    ← Database file
├── src/
├── run_bot.py
└── ...
```

## Troubleshooting

### Database locked error

If you see "database is locked":
- Close any SQLite browser/viewer
- Make sure only one bot instance is running
- Restart the bot

### Database corrupted

If database is corrupted:
1. Stop the bot
2. Delete `calorie_tracker.db`
3. Restart bot (new database will be created)
4. Restore from backup if available

### Reset database

To start fresh:

```bash
# Stop the bot
# Delete database
rm calorie_tracker.db

# Restart bot
python run_bot.py
```

## Advanced Usage

### Custom Database Path

You can specify a custom database path in `config.py`:

```python
DATABASE_URL = "sqlite:///./custom_path/calorie_tracker.db"
```

### Database Statistics

Check database size and entry count:

```bash
# Database file size
ls -lh calorie_tracker.db

# Entry count
sqlite3 calorie_tracker.db "SELECT COUNT(*) FROM food_entries;"

# User count
sqlite3 calorie_tracker.db "SELECT COUNT(*) FROM users;"
```

### Export Data

Export to CSV:

```bash
sqlite3 -header -csv calorie_tracker.db "SELECT * FROM food_entries;" > entries.csv
```

Export to JSON:

```bash
sqlite3 calorie_tracker.db "SELECT json_group_array(json_object(
    'id', id,
    'user_id', telegram_user_id,
    'food', food_text,
    'calories', total_calories,
    'date', date
)) FROM food_entries;" > entries.json
```

## Performance

- **Fast queries** - Indexed for optimal performance
- **Small size** - Efficient storage format
- **Scalable** - Can handle thousands of entries
- **Reliable** - ACID compliant transactions

## Security

- Database file is local only
- Not exposed to network
- Included in `.gitignore` (optional)
- Backup regularly for safety

## Future Enhancements

Planned improvements:
- [ ] PostgreSQL support for production
- [ ] Automatic backups
- [ ] Data export features
- [ ] Database migration tools
- [ ] Analytics queries

---

**Note:** The database file (`calorie_tracker.db`) contains all your data. Keep it safe and backup regularly!