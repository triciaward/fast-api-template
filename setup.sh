#!/bin/bash

echo "🚀 Setting up FastAPI Template Development Environment"
echo "=================================================="

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "🐍 Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Copy .env.example to .env and update your environment variables"
echo "2. Ensure PostgreSQL is running (via Docker): docker-compose up postgres -d"
echo "3. Run database migrations: alembic upgrade head"
echo "4. Start the development server: uvicorn app.main:app --reload"
echo ""
echo "💡 To activate the virtual environment later, run: source venv/bin/activate" 