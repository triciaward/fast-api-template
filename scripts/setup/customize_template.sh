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
if [ ! -f "scripts/setup/customize_template.py" ]; then
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

# Check if we're in a renamed project directory (should end with _backend)
if [[ ! "$(basename "$PWD")" =~ _backend$ ]]; then
    print_warning "This doesn't appear to be a renamed project directory!"
    print_info "Current directory: $(basename "$PWD")"
    print_info "This script should be run from a renamed project directory (ending with _backend)."
    print_info "If you haven't renamed the template yet, please:"
    print_info "1. Run the rename script first: ./scripts/setup/rename_template.sh"
    print_info "2. Restart VS Code and open the renamed directory"
    print_info "3. Then run this script"
    echo
    print_warning "⚠️  CRITICAL: Make sure you have restarted VS Code after renaming!"
    print_info "   This script should only be run AFTER restarting VS Code and opening the renamed directory."
    echo
    confirm=$(read -p "Continue anyway? (y/N): " -n 1 -r)
    echo
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_error "Customization cancelled."
        exit 1
    fi
fi

# Run the Python customization script
python3 scripts/setup/customize_template.py

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    echo
    print_success "Template customization completed!"
    print_info "You can now start developing your application."
else
    print_error "Template customization failed."
    exit 1
fi 