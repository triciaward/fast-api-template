#!/bin/bash
# Fix pre-commit setup for existing FastAPI template projects

set -e

echo "🔧 Fixing pre-commit setup for existing project..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository!"
    echo "   Please run this script from your project root directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "   Please create and activate your virtual environment first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if pre-commit is already installed
if ! python -m pip show pre-commit > /dev/null 2>&1; then
    echo "📦 Installing pre-commit..."
    python -m pip install pre-commit
    echo "✅ Pre-commit installed"
else
    echo "✅ Pre-commit already installed"
fi

# Install the git hooks
echo "🔗 Installing pre-commit hooks..."
python -m pre_commit install

# Verify the hooks are installed
if [ -f ".git/hooks/pre-commit" ]; then
    echo "✅ Pre-commit hooks installed successfully"
else
    echo "❌ Failed to install pre-commit hooks"
    exit 1
fi

# Run initial check on all files
echo "🔍 Running initial pre-commit check on all files..."
echo "   This may take a few minutes on first run..."
python -m pre_commit run --all-files

echo ""
echo "🎉 Pre-commit setup complete!"
echo ""
echo "📋 What this gives you:"
echo "   ✅ Template repository protection (prevents accidental commits to template)"
echo "   ✅ Automatic code formatting with Black"
echo "   ✅ Linting with Ruff"
echo "   ✅ Type checking with MyPy"
echo "   ✅ All checks run automatically before each commit"
echo ""
echo "💡 Next time you commit, all checks will run automatically!"
echo "   If any check fails, the commit will be blocked until you fix the issues."
