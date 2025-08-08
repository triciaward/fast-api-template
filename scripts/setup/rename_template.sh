#!/bin/bash

# FastAPI Template - Directory Renaming Script
# This script renames the template directory to your project name

set -e  # Exit on any error

echo "🚀 FastAPI Template - Step 1: Rename Directory (Required)"
echo "========================================================"
echo ""
echo "This script will rename the template directory to your project name."
echo "This is REQUIRED - you must customize the template before starting development."
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/setup/customize_template.py" ]; then
    echo "❌ Error: This script must be run from the template root directory."
    echo "   Make sure you're in the 'fast-api-template' folder."
    exit 1
fi

# Check if we're still in the template directory
if [ "$(basename "$PWD")" = "fast-api-template" ]; then
    echo "✅ You're in the template directory. Ready to rename!"
else
    echo "❌ Error: You're not in the 'fast-api-template' directory."
    echo "   Current directory: $(basename "$PWD')"
    echo "   Expected directory: fast-api-template"
    echo ""
    echo "   Please navigate to the template directory and run this script again."
    echo "   This step is required before you can start development."
    exit 1
fi

# Get project name from user
echo ""
echo "Please enter your project name:"
echo "  Examples: 'My Awesome Project', 'Todo App Backend', 'E-commerce API'"
echo ""
read -p "Project name: " PROJECT_NAME

if [ -z "$PROJECT_NAME" ]; then
    echo "❌ Error: Project name cannot be empty."
    exit 1
fi

# Generate project slug from project name and append _backend
PROJECT_SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//' | sed 's/_$//')_backend

echo ""
echo "📋 Summary:"
echo "  Project Name: $PROJECT_NAME"
echo "  Directory Name: $PROJECT_SLUG"
echo ""

# Confirm with user
read -p "Continue with renaming? (y/N): " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "❌ Renaming cancelled."
    exit 0
fi

# Navigate to parent directory
cd ..

# Rename the directory
echo ""
echo "🔄 Renaming directory..."
mv "fast-api-template" "$PROJECT_SLUG"

if [ $? -eq 0 ]; then
    echo "✅ Directory renamed successfully!"
    echo ""
    echo "🎉 Directory renamed successfully!"
    echo "================================"
    echo ""
    echo "📝 Next steps (required):"
    echo "1. Restart VS Code to ensure it recognizes the new directory name"
    echo "2. Run the customization script: ./scripts/setup/customize_template.sh"
    echo "3. Then set up your development environment: ./scripts/setup/quick_start.sh"
    echo ""
    echo "🚨 IMPORTANT: You must complete both customization steps before starting development!"
    echo "   - User must manually restart VS Code and open the renamed directory"
    echo "   - Only continue after user confirms VS Code has been restarted"
    echo "   - Wait for user to copy/paste the message above"
    echo ""
    echo "The template is now ready for customization!"
else
    echo "❌ Error: Failed to rename directory."
    echo "   Make sure you have write permissions and the directory isn't open in another application."
    exit 1
fi 