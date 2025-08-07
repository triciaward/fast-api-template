#!/bin/bash

# GlitchTip Setup Script
# This script helps set up GlitchTip error monitoring for the FastAPI template

set -e

echo "🚀 Setting up GlitchTip Error Monitoring..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"
    else
        print_error ".env.example not found. Please create a .env file manually."
        exit 1
    fi
fi

# Generate a secure secret key for GlitchTip
GLITCHTIP_SECRET_KEY=$(openssl rand -hex 32)

print_status "Generated GlitchTip secret key"

# Update .env file with GlitchTip configuration
print_status "Updating .env file with GlitchTip configuration..."

# Add GlitchTip environment variables if they don't exist
if ! grep -q "GLITCHTIP_SECRET_KEY" .env; then
    echo "" >> .env
    echo "# GlitchTip Error Monitoring" >> .env
    echo "GLITCHTIP_SECRET_KEY=$GLITCHTIP_SECRET_KEY" >> .env
    echo "GLITCHTIP_PORT=8001" >> .env
    echo "ENABLE_SENTRY=true" >> .env
    echo "SENTRY_DSN=http://localhost:8001/1/" >> .env
    echo "SENTRY_ENVIRONMENT=development" >> .env
    print_success "Added GlitchTip configuration to .env"
else
    print_warning "GlitchTip configuration already exists in .env"
fi

# Start GlitchTip with Docker Compose
print_status "Starting GlitchTip with Docker Compose..."

# Start required services (postgres, redis) if not running
if ! docker-compose ps postgres | grep -q "Up"; then
    print_status "Starting PostgreSQL..."
    docker-compose up -d postgres
fi

if ! docker-compose ps redis | grep -q "Up"; then
    print_status "Starting Redis..."
    docker-compose up -d redis
fi

# Start GlitchTip
print_status "Starting GlitchTip..."
docker-compose --profile monitoring up -d glitchtip

# Wait for GlitchTip to be ready
print_status "Waiting for GlitchTip to be ready..."
sleep 30

# Check if GlitchTip is running
if docker-compose ps glitchtip | grep -q "Up"; then
    print_success "GlitchTip is running!"
    echo ""
    echo "🌐 GlitchTip Dashboard: http://localhost:8001"
    echo "🔑 Default admin credentials:"
    echo "   Username: admin"
    echo "   Password: admin"
    echo ""
    echo "📊 Sentry DSN for your app: http://localhost:8001/1/"
    echo ""
    echo "🚀 To start your FastAPI app with Sentry monitoring:"
    echo "   docker-compose up api"
    echo ""
    echo "🧪 To test error monitoring:"
    echo "   curl http://localhost:8000/health/test-sentry"
    echo ""
else
    print_error "Failed to start GlitchTip. Check the logs:"
    echo "docker-compose logs glitchtip"
    exit 1
fi

print_success "GlitchTip setup complete! 🎉" 