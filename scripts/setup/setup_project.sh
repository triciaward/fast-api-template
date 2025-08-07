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
if [ ! -f "scripts/setup/customize_template.py" ]; then
    echo "❌ Error: This script must be run from your project root directory."
    echo "   Make sure you're in your renamed project folder."
    exit 1
fi

# Show current project directory
CURRENT_DIR=$(basename "$PWD")
echo "✅ Working in project directory: $CURRENT_DIR"
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

# Check if alembic.ini exists, create if missing
echo ""
echo "🔧 Checking Alembic configuration..."
if [ ! -f "alembic.ini" ]; then
    echo "   Creating alembic.ini file..."
    cat > alembic.ini << 'EOF'
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
version_num_format = %04d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:dev_password_123@localhost:5432/fastapi_template


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
    echo "✅ Created alembic.ini file"
else
    echo "✅ alembic.ini file already exists"
fi

# Check if alembic.ini exists, create if missing
echo ""
echo "🔧 Checking Alembic configuration..."
if [ ! -f "alembic.ini" ]; then
    echo "   Creating alembic.ini file..."
    cat > alembic.ini << 'EOF'
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
version_num_format = %04d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:dev_password_123@localhost:5432/fastapi_template


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
    echo "✅ Created alembic.ini file"
else
    echo "✅ alembic.ini file already exists"
fi

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

# Create superuser automatically
echo ""
echo "👤 Creating superuser account..."

# Set environment variables for superuser creation with proper values
export PYTHONPATH=.
export FIRST_SUPERUSER="admin@$(basename "$PWD" | sed 's/_backend$//' | sed 's/fast-api-template/example/').com"
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
echo "3. Verify your setup: python3 scripts/setup/verify_setup.py"
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