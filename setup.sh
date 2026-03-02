#!/bin/bash

# Setup script for Telegram Calorie Tracker Bot

echo "🚀 Setting up Telegram Calorie Tracker Bot..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your TELEGRAM_BOT_TOKEN"
    echo ""
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Edit .env file and add your bot token:"
echo "   nano .env"
echo ""
echo "3. Run the bot:"
echo "   python run_bot.py"
echo ""

# Made with Bob
