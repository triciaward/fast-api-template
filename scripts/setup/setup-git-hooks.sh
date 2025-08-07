#!/bin/bash
# Setup git hooks to run CI validation automatically

echo "🔧 Setting up automatic CI validation..."

# Create the pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
echo "🔍 Running CI validation before push..."
if ! ./scripts/development/validate_ci.sh; then
    echo "❌ CI validation failed! Please fix the issues before pushing."
    exit 1
fi
echo "✅ CI validation passed! Proceeding with push..."
EOF

# Make it executable
chmod +x .git/hooks/pre-push

echo "✅ Git hooks installed!"
echo "🔍 Now the validation will run automatically before every push"
echo "🚀 You can still run ./scripts/development/validate_ci.sh manually anytime" 