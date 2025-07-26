# AI Assistant Workflow Guide

## 🚨 CRITICAL WORKFLOW FOR TEMPLATE PROJECT CREATION

When helping users create new projects from this FastAPI template, follow this EXACT workflow:

### Step 1: Run the Rename Script
```bash
./scripts/rename_template.sh
```

**What happens:**
- Script prompts for project name
- Renames directory from `fast-api-template` to `[project_name]_backend`
- Shows restart instructions

### Step 2: STOP and Wait for VS Code Restart ⚠️

**CRITICAL:** After the rename script completes, you MUST:

1. **STOP all automated commands**
2. **Tell the user to restart VS Code**
3. **Wait for user confirmation**

**Example message:**
```
✅ Directory renamed successfully!

🚨 IMPORTANT: You must restart VS Code now!

Please:
1. Close VS Code completely
2. Open VS Code again
3. Open the renamed folder: [project_name]_backend
4. Let me know when you're ready to continue

I'll wait here until you confirm VS Code has been restarted.
```

### Step 3: Wait for User Confirmation

**DO NOT continue until the user confirms:**
- VS Code has been restarted
- They are in the renamed directory
- They are ready to continue

### Step 4: Continue with Customization

Only after user confirmation, continue with:
```bash
./scripts/customize_template.sh
```

## ❌ WHAT NOT TO DO

**NEVER:**
- Automatically run `cd ../[project_name]_backend` after rename
- Automatically run `./scripts/customize_template.sh` after rename
- Continue with next steps without waiting for VS Code restart
- Assume the user has restarted VS Code

## ✅ WHAT TO DO

**ALWAYS:**
- Run rename script
- STOP and wait for VS Code restart
- Get explicit confirmation from user
- Only then continue with customization

## Why This Matters

The VS Code restart is crucial because:
- VS Code needs to recognize the new directory structure
- Prevents path conflicts and configuration issues
- Ensures all tools work correctly
- Prevents database connection problems

## Example Complete Workflow

```
User: "Help me create a new project called 'MyApp'"

Assistant:
1. Run: ./scripts/rename_template.sh
2. Wait for user input: "MyApp"
3. Script completes, shows restart message
4. STOP and say: "Please restart VS Code and open the renamed directory"
5. Wait for user: "OK, I've restarted VS Code"
6. Continue: ./scripts/customize_template.sh
```

This workflow prevents the exact issue that occurred where the AI assistant continued without the crucial VS Code restart step. 