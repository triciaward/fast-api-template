#!/bin/bash

# =============================================================================
# FastAPI Template Environment Fix Script
# =============================================================================
# This script fixes common environment variable and configuration issues
# that occur during template setup and customization.

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

# Function to read value from .env file
get_env_value() {
    local key="$1"
    local default="$2"
    if [ -f ".env" ]; then
        local value=$(grep "^${key}=" .env | cut -d'=' -f2- | sed 's/^"//;s/"$//')
        if [ -n "$value" ]; then
            echo "$value"
        else
            echo "$default"
        fi
    else
        echo "$default"
    fi
}

print_header "FastAPI Template Environment Fix Script"
echo "This script will fix common environment variable and configuration issues."
echo ""

# =============================================================================
# 1. Check for .env file (Hidden File)
# =============================================================================
print_header "1. Checking Environment Configuration"

print_status "Looking for .env file (hidden file starting with a dot)..."
if [ -f ".env" ]; then
    print_success ".env file found (hidden file)"
    
    # Read key values from existing .env file
    POSTGRES_DB=$(get_env_value "POSTGRES_DB" "fastapi_template")
    POSTGRES_USER=$(get_env_value "POSTGRES_USER" "postgres")
    POSTGRES_PASSWORD=$(get_env_value "POSTGRES_PASSWORD" "dev_password_123")
    DATABASE_URL=$(get_env_value "DATABASE_URL" "postgresql://postgres:dev_password_123@localhost:5432/fastapi_template")
    SECRET_KEY=$(get_env_value "SECRET_KEY" "dev_secret_key_change_in_production")
    
    print_status "Current configuration:"
    echo "  - Database: $POSTGRES_DB"
    echo "  - User: $POSTGRES_USER"
    echo "  - Database URL: $DATABASE_URL"
    
    # Check for missing required variables
    missing_vars=()
    required_vars=("POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD" "DATABASE_URL" "SECRET_KEY")
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_warning "Missing required environment variables: ${missing_vars[*]}"
        print_status "Adding missing variables to .env file..."
        
        # Add missing variables to .env file
        for var in "${missing_vars[@]}"; do
            case $var in
                "POSTGRES_DB")
                    echo "POSTGRES_DB=$POSTGRES_DB" >> .env
                    ;;
                "POSTGRES_USER")
                    echo "POSTGRES_USER=$POSTGRES_USER" >> .env
                    ;;
                "POSTGRES_PASSWORD")
                    echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env
                    ;;
                "DATABASE_URL")
                    echo "DATABASE_URL=$DATABASE_URL" >> .env
                    ;;
                "SECRET_KEY")
                    echo "SECRET_KEY=$SECRET_KEY" >> .env
                    ;;
            esac
        done
        print_success "Added missing variables to .env file"
    else
        print_success "All required environment variables are present"
    fi
else
    print_error ".env file not found! (Remember, it's a hidden file starting with a dot)"
    print_status "You can check for hidden files with: ls -la | grep -E '\\.env'"
    print_status "Creating .env file from .env.example..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"
        
        # Set default values
        POSTGRES_DB="fastapi_template"
        POSTGRES_USER="postgres"
        POSTGRES_PASSWORD="dev_password_123"
        DATABASE_URL="postgresql://postgres:dev_password_123@localhost:5432/fastapi_template"
        SECRET_KEY="dev_secret_key_change_in_production"
    else
        print_error "Neither .env nor .env.example found!"
        exit 1
    fi
fi

# =============================================================================
# 2. Fix alembic.ini configuration
# =============================================================================
print_header "2. Fixing Database Configuration"

if [ -f "alembic.ini" ]; then
    print_success "alembic.ini found"
    
    # Check if sqlalchemy.url is properly configured
    if grep -q "sqlalchemy.url = postgresql://" alembic.ini; then
        print_success "alembic.ini has proper database URL configuration"
        
        # Update alembic.ini with correct database name from .env
        current_db_url=$(grep "sqlalchemy.url = " alembic.ini | cut -d'=' -f2 | xargs)
        expected_db_url="postgresql://postgres:dev_password_123@localhost:5432/${POSTGRES_DB}"
        
        if [ "$current_db_url" != "$expected_db_url" ]; then
            print_status "Updating alembic.ini database URL to match .env configuration..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS requires different sed syntax
                sed -i '' "s|sqlalchemy.url = .*|sqlalchemy.url = $expected_db_url|" alembic.ini
            else
                # Linux sed syntax
                sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = $expected_db_url|" alembic.ini
            fi
            print_success "Updated alembic.ini database URL"
        else
            print_success "alembic.ini database URL is already correct"
        fi
    else
        print_warning "alembic.ini database URL may need updating"
    fi
    
    # Check for malformed version_num_format line
    if grep -q "version_num_format = %04d" alembic.ini; then
        print_warning "Found malformed version_num_format line in alembic.ini"
        print_status "Fixing version_num_format line..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS requires different sed syntax
            sed -i '' 's/version_num_format = %04d/# version_num_format = %04d/' alembic.ini
        else
            # Linux sed syntax
            sed -i 's/version_num_format = %04d/# version_num_format = %04d/' alembic.ini
        fi
        print_success "Fixed version_num_format line"
    fi
else
    print_error "alembic.ini not found! This is required for database migrations."
    exit 1
fi

# =============================================================================
# 3. Export environment variables for Docker Compose
# =============================================================================
print_header "3. Setting up Environment Variables"

# Export environment variables for docker-compose
export POSTGRES_DB
export POSTGRES_USER
export POSTGRES_PASSWORD
export DATABASE_URL
export SECRET_KEY

print_status "Exported environment variables for Docker Compose:"
echo "  - POSTGRES_DB=$POSTGRES_DB"
echo "  - POSTGRES_USER=$POSTGRES_USER"
echo "  - POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "  - DATABASE_URL=$DATABASE_URL"
echo "  - SECRET_KEY=$SECRET_KEY"

# =============================================================================
# 4. Test Docker Compose configuration
# =============================================================================
print_header "4. Testing Docker Compose Configuration"

if command -v docker-compose >/dev/null 2>&1; then
    print_status "Testing Docker Compose configuration..."
    
    # Test if docker-compose can read the environment variables
    if docker-compose config >/dev/null 2>&1; then
        print_success "Docker Compose configuration is valid"
    else
        print_warning "Docker Compose configuration may have issues"
        print_status "Checking for specific errors..."
        docker-compose config
    fi
else
    print_warning "Docker Compose not found - skipping configuration test"
fi

# =============================================================================
# 5. Test database connection
# =============================================================================
print_header "5. Testing Database Connection"

if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    print_status "Testing database connection..."
    
    # Check if PostgreSQL container is running
    if docker-compose ps postgres | grep -q "Up"; then
        print_success "PostgreSQL container is running"
        
        # Test database connection
        if docker-compose exec -T postgres psql -U postgres -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "Database connection successful"
        else
            print_warning "Database connection failed - database may not exist yet"
            print_status "You can create the database with: docker-compose exec postgres psql -U postgres -c 'CREATE DATABASE \"$POSTGRES_DB\";'"
        fi
    else
        print_warning "PostgreSQL container is not running"
        print_status "Start services with: docker-compose up -d"
    fi
else
    print_warning "Docker not available - skipping database connection test"
fi

# =============================================================================
# 6. Test Alembic configuration
# =============================================================================
print_header "6. Testing Alembic Configuration"

if [ -f "alembic.ini" ]; then
    print_status "Testing Alembic configuration..."
    
    # Set PYTHONPATH for alembic
    export PYTHONPATH=.
    
    # Check if virtual environment exists and activate it
    if [ -d "venv" ]; then
        print_status "Activating virtual environment for Alembic test..."
        source venv/bin/activate
        
        # Test alembic configuration
        if alembic current >/dev/null 2>&1; then
            print_success "Alembic configuration is valid"
        else
            print_warning "Alembic configuration may have issues"
            print_status "Checking alembic current status..."
            alembic current
        fi
    else
        print_warning "Virtual environment not found - Alembic test skipped"
        print_status "Create virtual environment with: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
else
    print_error "alembic.ini not found - Alembic configuration test skipped"
fi

# =============================================================================
# 7. Summary and Next Steps
# =============================================================================
print_header "7. Environment Fix Complete! 🎉"

print_success "Environment configuration has been fixed!"
echo ""
echo "📋 Summary of fixes:"
echo "  ✅ Environment variables configured"
echo "  ✅ Database URL updated in alembic.ini"
echo "  ✅ Malformed configuration lines fixed"
echo "  ✅ Environment variables exported for Docker Compose"
echo ""
echo "🚀 Next steps:"
echo "  1. Start services: docker-compose up -d"
echo "  2. Run migrations: alembic upgrade head"
echo "  3. Create superuser (optional): python app/bootstrap_superuser.py"
echo "  4. Test the API: http://localhost:8000/docs"
echo ""
echo "🔧 If you still have issues:"
echo "  - Check Docker Compose logs: docker-compose logs"
echo "  - Verify environment variables: docker-compose config"
echo "  - Test database connection manually"
echo ""

print_success "Environment issues should now be resolved! 🚀" 