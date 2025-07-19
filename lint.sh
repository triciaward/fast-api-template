#!/bin/bash

echo "🔍 Running Code Quality Checks..."
echo "=================================="

echo ""
echo "🎨 Running Ruff (formatting & linting)..."
ruff check app/ && echo "✅ Ruff checks passed!" || echo "❌ Ruff found issues"

echo ""
echo "🔍 Running MyPy (type checking)..."
mypy app/ && echo "✅ MyPy checks passed!" || echo "❌ MyPy found type issues"

echo ""
echo "🔧 To auto-fix ruff issues: ruff check --fix app/"
echo "📖 To format code: ruff format app/" 