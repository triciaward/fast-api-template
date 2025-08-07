#!/bin/bash
# Install git hooks to prevent template repository operations

set -e

echo "🔧 Installing Git Hooks for Template Protection..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy the pre-commit hook
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Git hooks installed successfully!"
echo ""
echo "🛡️  Protection enabled:"
echo "   - Pre-commit hook will warn about template repository operations"
echo "   - Users will be prompted before committing to template repo"
echo "   - Clear instructions provided for setting up new repository"
echo ""
echo "💡 To disable this protection (not recommended):"
echo "   rm .git/hooks/pre-commit" 