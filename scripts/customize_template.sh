#!/bin/bash

# FastAPI Template Customization Script Wrapper
# This script provides an easy way to run the template customization

set -e

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

# Check if we're in the right directory
if [ ! -f "scripts/customize_template.py" ]; then
    print_error "This script must be run from the project root directory."
    print_info "Please navigate to the project root and try again."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    print_info "Please install Python 3 and try again."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_warning "This doesn't appear to be a git repository."
    print_info "The customization will still work, but git remote updates will be skipped."
fi

print_info "Starting FastAPI Template Customization..."
echo

# Run the Python customization script
python3 scripts/customize_template.py

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    echo
    print_success "Template customization completed!"
    print_info "You can now start developing your application."
else
    print_error "Template customization failed."
    exit 1
fi 