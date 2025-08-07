#!/bin/bash

# FastAPI Template Development Script
# This script sets up the environment for working with the template itself
# (NOT for creating new projects from the template)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🚀 FastAPI Template Development Setup"
echo "====================================="
echo ""
echo "This script sets up the environment for working with the template itself."
echo "This is for template development, NOT for creating new projects."
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/customize_template.py" ]; then
    print_error "This script must be run from the template root directory."
    print_info "Make sure you're in the 'fast-api-template' folder."
    exit 1
fi

# Check if we're in the template directory
if [ "$(basename "$PWD")" != "fast-api-template" ]; then
    print_error "You're not in the 'fast-api-template' directory."
    print_info "Current directory: $(basename "$PWD")"
    print_info "Expected directory: fast-api-template"
    echo ""
    print_info "If you want to create a new project from this template, use:"
    print_info "  ./scripts/rename_template.sh"
    echo ""
    print_info "If you want to work with the template itself, navigate to the template directory."
    exit 1
fi

print_success "You're in the template directory. Setting up development environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_info "Creating .env file from example..."
    cp .env.example .env
    print_success "Created .env file"
else
    print_success ".env file already exists"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Created virtual environment"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_info "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt
print_success "Dependencies installed"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running or not accessible."
    print_info "Please start Docker and try again."
    exit 1
fi

print_success "Docker is running"

# Start database services
print_info "Starting database services..."
docker-compose up -d postgres redis
print_success "Database services started"

# Wait for PostgreSQL to be ready
print_info "Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    sleep 1
done
print_success "PostgreSQL is ready"

# Run database migrations
print_info "Running database migrations..."
alembic upgrade head
print_success "Database migrations completed"

# Create a test superuser for development
print_info "Creating test superuser for development..."
python app/bootstrap_superuser.py
print_success "Test superuser created"

# Run tests to verify everything is working
print_info "Running tests to verify setup..."
pytest tests/ -v --tb=short
print_success "Tests passed"

echo ""
print_success "🎉 Template development environment is ready!"
echo ""
echo "📋 What's been set up:"
echo "  ✅ Python virtual environment"
echo "  ✅ All dependencies installed"
echo "  ✅ PostgreSQL database running"
echo "  ✅ Redis running (for caching/background tasks)"
echo "  ✅ Database migrations applied"
echo "  ✅ Test superuser created"
echo "  ✅ All tests passing"
echo ""
echo "🚀 Next Steps:"
echo "  1. Start the FastAPI application: docker-compose up -d"
echo "  2. View API docs: http://localhost:8000/docs"
echo "  3. View admin panel: http://localhost:8000/admin"
echo "  4. Run tests: pytest"
echo "  5. Start developing the template!"
echo ""
echo "💡 Useful Commands:"
echo "  docker-compose up -d          # Start all services"
echo "  docker-compose logs -f        # View logs"
echo "  docker-compose down           # Stop all services"
echo "  pytest                        # Run tests"
echo "  alembic revision --autogenerate -m 'description'  # Create migration"
echo "  alembic upgrade head          # Apply migrations"
echo ""
echo "🔧 For Template Development:"
echo "  - Edit files in the app/ directory to modify the template"
echo "  - Update tests in tests/ directory"
echo "  - Modify scripts/ directory for new functionality"
echo "  - Update documentation in docs/ directory"
echo ""
print_success "Happy template development! 🚀" 