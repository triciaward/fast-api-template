# Development Workflow Issues

This folder contains troubleshooting guides for development workflow and authentication issues.

## 📁 Available Guides

### **[AI Assistant Workflow](./AI_ASSISTANT_WORKFLOW.md)**
- Critical workflow for AI assistants helping users
- VS Code restart requirements after template rename
- Proper workflow for template customization
- Preventing setup issues through correct procedures
- AI assistant best practices for template usage

### **[Auth Modularization](./auth-modularization.md)**
- Authentication system modularization
- Code organization improvements
- Maintainability and scalability benefits
- Migration from monolithic to modular structure
- No breaking changes to existing functionality

### **[API Keys Dashboard Authentication](./api-keys-dashboard-authentication-issue.md)**
- Admin panel authentication problems
- API keys dashboard access issues
- Superuser authentication problems
- Admin panel configuration
- Expected behavior vs actual issues

## 🚀 Quick Solutions

### Template Customization Workflow:
```bash
# Step 1: Rename directory
./scripts/rename_template.sh

# Step 2: Restart VS Code (CRITICAL!)

# Step 3: Customize files
./scripts/customize_template.sh

# Step 4: Setup environment
./scripts/setup_project.sh
```

### Commit & Push Workflow

Use the smart commit script to run hooks and keep your intended message:

```bash
./scripts/development/smart_commit.sh "feat: your message here"
git push origin main
```

This runs pre-commit hooks first (format, lint, type checks), stages auto-fixes, and then creates a commit with your original message. Avoids follow-up "chore: fix formatting" commits.

### Authentication Testing:
```bash
# Test login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=Admin123!"

# Test API keys dashboard with token
curl -X GET "http://localhost:8000/api/admin/api-keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### Auth System Verification:
```bash
# Check auth endpoints
curl http://localhost:8000/api/auth/oauth/providers

# Test registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"TestPassword123!"}'
```

## 📞 Getting Help

If you encounter workflow issues not covered in these guides:
1. Check the main [troubleshooting index](../TROUBLESHOOTING_README.md)
2. Review the [authentication guide](../../tutorials/authentication.md)
3. Follow the AI assistant workflow exactly
4. Verify all environment variables are set correctly
