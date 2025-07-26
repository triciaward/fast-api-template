#!/bin/bash

# FastAPI Template - Directory Renaming Script
# This script renames the template directory to your project name

set -e  # Exit on any error

echo "🚀 FastAPI Template - Step 1: Rename Directory"
echo "=============================================="
echo ""
echo "This script will rename the template directory to your project name."
echo "This is the FIRST step in customizing your template."
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/customize_template.py" ]; then
    echo "❌ Error: This script must be run from the template root directory."
    echo "   Make sure you're in the 'fast-api-template' folder."
    exit 1
fi

# Check if we're still in the template directory
if [ "$(basename "$PWD")" = "fast-api-template" ]; then
    echo "✅ You're in the template directory. Let's rename it!"
else
    echo "❌ Error: You're not in the 'fast-api-template' directory."
    echo "   Current directory: $(basename "$PWD")"
    echo "   Expected directory: fast-api-template"
    echo ""
    echo "   Please navigate to the template directory and run this script again."
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
    echo "🎉 STEP 1 COMPLETE!"
    echo "=================="
    echo ""
    echo "🚨 IMPORTANT: You must restart VS Code now!"
    echo ""
    echo "Next steps:"
    echo "1. Close VS Code completely"
    echo "2. Open VS Code again"
    echo "3. Open the folder: $PROJECT_SLUG"
    echo "4. Run the next script: ./scripts/customize_template.sh"
    echo ""

    echo ""
    echo "⚠️  CRITICAL FOR AI ASSISTANTS:"
    echo "   - STOP here and wait for user to restart VS Code"
    echo "   - DO NOT continue with next steps automatically"
    echo "   - User must manually restart VS Code and open the renamed directory"
    echo "   - Only continue after user confirms VS Code has been restarted"
    echo ""
    echo "The template is now ready for customization!"
else
    echo "❌ Error: Failed to rename directory."
    echo "   Make sure you have write permissions and the directory isn't open in another application."
    exit 1
fi 