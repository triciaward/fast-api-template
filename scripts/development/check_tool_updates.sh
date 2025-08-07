#!/bin/bash
# Check for tool updates and help manage version upgrades

set -e

echo "🔍 Checking for tool updates..."

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

# Auto-detect and activate virtual environment if available
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if we're in the right directory
if [ ! -f "requirements-dev.txt" ]; then
    print_error "Not in project root directory (requirements-dev.txt not found)"
    exit 1
fi

echo ""
print_info "Current pinned versions in requirements-dev.txt:"
echo "=================================================="

# Show current versions
grep -E "^[a-zA-Z]" requirements-dev.txt | while read line; do
    if [[ $line =~ ^([a-zA-Z0-9_-]+)==([0-9.]+) ]]; then
        tool="${BASH_REMATCH[1]}"
        version="${BASH_REMATCH[2]}"
        echo "  $tool: $version"
    fi
done

echo ""
print_info "Checking for outdated packages..."
echo "====================================="

# Check for outdated packages
outdated_output=$(pip list --outdated 2>/dev/null || echo "No outdated packages found")

if [[ "$outdated_output" == *"No outdated packages found"* ]] || [[ -z "$outdated_output" ]]; then
    print_success "All development tools are up to date!"
else
    echo "$outdated_output"
    echo ""
    print_warning "Some tools have newer versions available!"
    echo ""
    print_info "To update safely:"
    echo "1. Run: pip install -r requirements-dev.txt --upgrade"
    echo "2. Test: ./scripts/validate_ci.sh"
    echo "3. Update pinned versions in requirements-dev.txt if needed"
    echo "4. Commit changes: git add requirements-dev.txt && git commit -m 'Update tool versions'"
fi

echo ""
print_info "Tool update frequency reminder:"
echo "==================================="
echo "  • Black: Every 2-4 weeks (formatting rules change)"
echo "  • Ruff: Every 1-2 weeks (new linting rules)"
echo "  • Mypy: Every 3-6 weeks (type checking changes)"
echo "  • Python: Every 3-6 months (new features)"
echo "  • Pre-commit: Every 2-4 weeks (hook behavior changes)"
echo ""
print_warning "CI environments update these tools frequently!"
print_info "Our pinned versions protect you from 'whack-a-mole' CI failures." 