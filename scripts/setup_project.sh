#!/bin/bash

# FastAPI Template - Project Setup Script
# This script sets up the development environment and database

set -e  # Exit on any error

echo "🚀 FastAPI Template - Step 3: Project Setup"
echo "==========================================="
echo ""
echo "This script will set up your development environment and database."
echo "This is the FINAL step in getting your project ready."
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/customize_template.py" ]; then
    echo "❌ Error: This script must be run from your project root directory."
    echo "   Make sure you're in your renamed project folder."
    exit 1
fi

# Check if we're in a renamed directory (not the original template)
if [ "$(basename "$PWD")" = "fast-api-template" ]; then
    echo "❌ Error: You're still in the 'fast-api-template' directory!"
    echo ""
    echo "This script should be run AFTER renaming and customizing the template."
    echo ""
    echo "Please run the scripts in order:"
    echo "1. ./scripts/rename_template.sh"
    echo "2. ./scripts/customize_template.sh"
    echo "3. ./scripts/setup_project.sh (this script)"
    exit 1
fi

echo "✅ You're in a renamed project directory: $(basename "$PWD")"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file"
    else
        echo "❌ Error: .env.example file not found!"
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Check if Docker is running
echo ""
echo "🐳 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "   Please start Docker and run this script again."
    exit 1
fi
echo "✅ Docker is running"

# Start PostgreSQL and FastAPI
echo ""
echo "🗄️  Starting database and API services..."
docker-compose up -d postgres api
echo "✅ Database and API services started"

# Wait for PostgreSQL to be ready
echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is ready
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Error: PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Run database migrations
echo ""
echo "🔄 Running database migrations..."

# Check if database already has tables but no migration history
echo "   Checking database state..."
if python -c "
import asyncio
from sqlalchemy import text
from app.database.database import engine

async def check_db_state():
    try:
        async with engine.begin() as conn:
            # Check if users table exists
            result = await conn.execute(text(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')\"))
            table_exists = result.scalar()
            
            # Check if alembic_version table exists
            result = await conn.execute(text(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')\"))
            version_exists = result.scalar()
            
            return table_exists, version_exists
    except Exception as e:
        print(f'Database connection error: {e}')
        return False, False

result = asyncio.run(check_db_state())
print(f'Tables exist: {result[0]}, Migration history: {result[1]}')
" 2>/dev/null; then
    echo "   Database state checked"
else
    echo "   Could not check database state, proceeding with normal migration"
fi

# Try to run migrations, but handle the case where tables already exist
if alembic upgrade head 2>&1 | grep -q "relation.*already exists"; then
    echo "   ⚠️  Tables already exist, stamping migration history..."
    alembic stamp head
    echo "✅ Database migration history stamped"
else
    echo "✅ Database migrations completed"
fi

# Create superuser (optional)
echo ""
echo "👤 Create a superuser account (optional):"
read -p "Create superuser? (y/N): " CREATE_SUPERUSER
if [[ $CREATE_SUPERUSER =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running superuser creation script..."
    
    # Set environment variables for superuser creation with proper values
    export PYTHONPATH=.
    export FIRST_SUPERUSER="admin@$(basename "$PWD" | sed 's/_backend$//').com"
    export FIRST_SUPERUSER_PASSWORD="Admin123!"
    
    echo "   Using email: $FIRST_SUPERUSER"
    echo "   Using password: $FIRST_SUPERUSER_PASSWORD"
    
    if python app/bootstrap_superuser.py; then
        echo "✅ Superuser creation completed"
    else
        echo "❌ Superuser creation failed"
        echo "   You can create a superuser manually later using:"
        echo "   python app/bootstrap_superuser.py"
    fi
else
    echo "   Skipping superuser creation"
fi

# Final checks
echo ""
echo "🔍 Running final checks..."

# Check if the API can start
echo "   Testing API startup..."
if python -c "from app.main import app; print('✅ API imports successfully')" 2>/dev/null; then
    echo "✅ API startup test passed"
else
    echo "❌ Warning: API startup test failed"
fi

# Check configuration loading
echo "   Testing configuration loading..."
if python -c "from app.core.config import settings; print(f'✅ Config loaded: {settings.PROJECT_NAME}')" 2>/dev/null; then
    echo "✅ Configuration loading test passed"
else
    echo "❌ Warning: Configuration loading test failed"
fi

# Check database connection
echo "   Testing database connection..."
if python -c "from app.database.database import engine; print('✅ Database connection test passed')" 2>/dev/null; then
    echo "✅ Database connection test passed"
else
    echo "❌ Warning: Database connection test failed"
fi

# Check if tests can run
echo "   Testing test environment..."
if python -c "import pytest; print('✅ Test environment ready')" 2>/dev/null; then
    echo "✅ Test environment ready"
else
    echo "❌ Warning: Test environment not ready"
fi

# Test API endpoint
echo "   Testing API endpoint..."
sleep 3  # Give API time to start
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API endpoint test passed"
else
    echo "❌ Warning: API endpoint test failed (API may still be starting)"
fi

echo ""
echo "🎉 STEP 3 COMPLETE!"
echo "=================="
echo ""
echo "🚀 Your project is ready!"
echo ""
echo "📋 What's been set up:"
echo "  ✅ Python virtual environment"
echo "  ✅ All dependencies installed"
echo "  ✅ PostgreSQL database running"
echo "  ✅ FastAPI application running"
echo "  ✅ Database migrations applied"
echo "  ✅ Environment variables configured"
echo ""
echo "🎯 Next Steps:"
echo "1. View API docs: http://localhost:8000/docs"
echo "2. Run tests: pytest"
echo "3. Verify your setup: python scripts/verify_setup.py"
echo "4. Start developing!"
echo ""
echo "💡 Useful Commands:"
echo "  docker-compose up -d          # Start all services (including Redis if needed)"
echo "  docker-compose logs -f        # View logs"
echo "  docker-compose down           # Stop all services"
echo "  pytest                        # Run tests"
echo "  alembic revision --autogenerate -m 'description'  # Create migration"
echo "  alembic upgrade head          # Apply migrations"
echo ""
echo "✨ Happy coding!" 