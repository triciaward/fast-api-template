#!/bin/bash

# FastAPI Template - Quick Start Script
# This script sets up the development environment and starts the application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
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

print_header() {
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "$1"
    echo "============================================================================="
    echo -e "${NC}"
}

print_header "FastAPI Template - Quick Start"
echo "This script will set up your development environment and start the application."
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/setup/setup.sh" ]; then
    print_error "This script must be run from the project root directory."
    print_info "Please navigate to the project root and try again."
    exit 1
fi

# Check if the project has been customized
if [ "$(basename "$PWD")" = "fast-api-template" ]; then
    print_error "This project hasn't been customized yet!"
    print_info "You must customize the template before starting development:"
    print_info "1. Run: ./scripts/setup/rename_template.sh"
    print_info "2. Restart VS Code and open the renamed directory"
    print_info "3. Run: ./scripts/setup/customize_template.sh"
    print_info "4. Then run this script again"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists, if not copy from example
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env file created"
        print_warning "Please update the .env file with your configuration values"
    else
        print_warning "No .env.example file found. You may need to create a .env file manually."
    fi
fi

# Start Docker services
print_status "Starting Docker services..."
docker-compose up -d

# Wait a moment for services to start
sleep 5

# Check if database is ready
print_status "Checking database connection..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        print_success "Database is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Database failed to start after $max_attempts attempts"
        print_status "You can try starting the services manually: docker-compose up -d"
        exit 1
    fi
    
    print_status "Waiting for database... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

# Run database migrations
print_status "Running database migrations..."
alembic upgrade head

# Check if the API is running
print_status "Checking if API is running..."
sleep 3

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "API is running!"
else
    print_warning "API might not be fully started yet. Please wait a moment and check:"
    print_status "curl http://localhost:8000/health"
fi

echo ""
print_success "🎉 Setup complete!"
echo ""
echo "📋 Your FastAPI application is now running:"
echo "   🌐 API: http://localhost:8000"
echo "   📚 Docs: http://localhost:8000/docs"
echo "   🔍 Health: http://localhost:8000/health"
echo ""
echo "💡 Next steps:"
echo "   1. Open http://localhost:8000/docs to explore the API"
echo "   2. Start building your features!"
echo "   3. Run tests: pytest"
echo "   4. Check logs: docker-compose logs -f"
echo ""
echo "🛠️  Development commands:"
echo "   - Stop services: docker-compose down"
echo "   - View logs: docker-compose logs -f"
echo "   - Run tests: pytest"
echo "   - Format code: black ."
echo ""
print_success "Happy coding! 🚀"
