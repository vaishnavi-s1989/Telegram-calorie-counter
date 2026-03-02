# Setup Guide - Telegram Calorie Tracker Bot

## The Error You're Seeing

The error `'Updater' object has no attribute '_Updater__polling_cleanup_cb'` occurs because:
1. Your system Python is externally managed (macOS protection)
2. You need to use a virtual environment

## Quick Fix - Setup Virtual Environment

### Step 1: Create Virtual Environment

```bash
# Navigate to project directory
cd "/Users/vaishnavi/Desktop/Whatsupp calorie counter"

# Create virtual environment
python3 -m venv venv
```

### Step 2: Activate Virtual Environment

```bash
# Activate (you'll see (venv) in your prompt)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Step 4: Configure Bot Token

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your bot token
nano .env
# or
open .env
```

Add your token:
```
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
```

### Step 5: Run the Bot

```bash
# Make sure virtual environment is activated (you should see (venv) in prompt)
python run_bot.py
```

## Alternative: Use the Setup Script

```bash
# Make script executable
chmod +x setup.sh

# Run setup script
./setup.sh

# Then activate venv and run
source venv/bin/activate
python run_bot.py
```

## Troubleshooting

### Issue: "Import telegram could not be resolved"

**Solution:** Make sure virtual environment is activated
```bash
source venv/bin/activate
pip list | grep telegram  # Should show python-telegram-bot
```

### Issue: "TELEGRAM_BOT_TOKEN is required"

**Solution:** Add your bot token to .env file
```bash
# Get token from @BotFather on Telegram
# Add to .env file:
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Issue: Virtual environment not activating

**Solution:** Use full path
```bash
source "/Users/vaishnavi/Desktop/Whatsupp calorie counter/venv/bin/activate"
```

## Verifying Installation

After setup, verify everything works:

```bash
# Check Python is from venv
which python
# Should show: .../venv/bin/python

# Check packages installed
pip list

# Should see:
# python-telegram-bot  20.7
# fastapi             0.109.0
# pydantic            (latest)
# etc.
```

## Running the Bot

### Option 1: Bot Only (Recommended for testing)

```bash
source venv/bin/activate
python run_bot.py
```

### Option 2: API Only

```bash
source venv/bin/activate
python run_api.py
```

### Option 3: Both (Two terminals)

**Terminal 1:**
```bash
source venv/bin/activate
python run_bot.py
```

**Terminal 2:**
```bash
source venv/bin/activate
python run_api.py
```

## Testing the Bot

Once running, open Telegram and:

1. Search for your bot by username
2. Send `/start`
3. Try logging food: `/log 2 eggs and 1 dosa`
4. Check today's summary: `/today`
5. View history: `/history`

## Deactivating Virtual Environment

When done:
```bash
deactivate
```

## Next Time You Want to Run

```bash
# Navigate to project
cd "/Users/vaishnavi/Desktop/Whatsupp calorie counter"

# Activate venv
source venv/bin/activate

# Run bot
python run_bot.py
```

## Common Commands Reference

```bash
# Create venv
python3 -m venv venv

# Activate venv (macOS/Linux)
source venv/bin/activate

# Activate venv (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run bot
python run_bot.py

# Run API
python run_api.py

# Deactivate venv
deactivate

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Getting Your Bot Token

1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Follow instructions to create bot
5. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Add to `.env` file

## Project Structure After Setup

```
calorie-tracker/
├── venv/                     # Virtual environment (created by you)
├── src/                      # Source code
├── .env                      # Your config (created by you)
├── .env.example             # Template
├── requirements.txt          # Dependencies
├── run_bot.py               # Bot entry point
├── run_api.py               # API entry point
├── setup.sh                 # Setup script
└── SETUP_GUIDE.md           # This file
```

## Need Help?

1. Check this guide
2. Review README.md
3. Check PROJECT_STRUCTURE.md for architecture details
4. Ensure virtual environment is activated
5. Verify bot token is correct in .env

---

**Important:** Always activate the virtual environment before running the bot!