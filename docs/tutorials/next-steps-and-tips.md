# Next Steps & Development Tips

A comprehensive guide for developers using the FastAPI template, covering what to build first, common commands, and mistakes to avoid.

## 📋 Quick Reference - Common Commands & Endpoints

### Essential Commands
```bash
# Start all services
docker compose up -d

# Stop all services  
docker compose down

# View logs
docker compose logs -f



# Format code
ruff format .

# Check code quality
ruff check .

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Create superuser
python app/bootstrap_superuser.py

# Run validation checks
./scripts/development/validate_ci.sh
```

### Key Endpoints
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/system/health
- **Admin API**: http://localhost:8000/admin/users
- **Alternative Docs**: http://localhost:8000/redoc

### Database Commands
```bash
# Connect to database
docker compose exec postgres psql -U postgres -d fastapi_template

# Reset database (⚠️ destructive)
docker compose down -v && docker compose up -d
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Development Workflow
```bash
# 1. Start services
docker compose up -d

# 2. Make code changes
# 3. Check code quality
ruff check .

# 4. Format code
ruff format .

# 5. Commit changes
git add . && git commit -m "description"
```

## 🎯 Next Steps - What to Build First

### For Template Users (Creating New Projects)
1. **Follow the Quick Start** - Use the rename and customization scripts
2. **Set up your environment** - Run the setup scripts
3. **Explore the codebase** - Familiarize yourself with the domain-based structure
4. **Start with a simple model** - Create your first domain entity

### For Existing Projects (Ready to Build Features)

**Phase 1: Foundation (Week 1)**
1. **Customize branding** - Update README, project name, and documentation
2. **Explore the codebase** - Study the patterns in `app/` folder
3. **Set up your domain models** - Add core business entities to `app/models/`
4. **Create your first CRUD endpoints** - Use existing patterns in `app/api/`

**Phase 2: Core Features (Week 2-3)**
1. **Add main API endpoints** - Build primary business logic
2. **Implement data validation** - Create schemas in `app/schemas/`
3. **Add business logic** - Create services in `app/services/`
4. **Set up relationships** - Connect models with proper foreign keys

**Phase 3: Advanced Features (Week 4+)**
1. **Add authentication** - Use existing auth system for your endpoints
2. **Implement rate limiting** - Protect APIs from abuse
3. **Add background tasks** - Use Celery for long-running operations
4. **Set up monitoring** - Add logging and error tracking

### Quick Wins to Build First
1. **Simple CRUD endpoint** - Create a basic resource (e.g., `/items`)
2. **Data validation** - Add proper request/response schemas
3. **Error handling** - Customize error responses for your domain
4. **Basic tests** - Write tests for your new endpoints

### Recommended Learning Path
1. **Start with models** - Understand SQLAlchemy model patterns
2. **Learn FastAPI patterns** - Study existing endpoint implementations
3. **Master the auth system** - Understand JWT tokens and user management
4. **Explore advanced features** - Dive into background tasks, caching, etc.

## ⚠️ Common Gotchas - Solo Developer Mistakes

### Database & Migration Issues
- **❌ Forgetting to run migrations** - Always run `alembic upgrade head` after model changes
- **❌ Not using soft deletes** - Use the `SoftDeleteMixin` for important data
- **❌ Ignoring database constraints** - Add proper foreign keys and unique constraints
- **❌ Not testing migrations** - Test migrations on a copy of production data
- **❌ Not backing up before migrations** - Always backup production data before running migrations

### Authentication & Security
- **❌ Exposing sensitive data in logs** - Never log passwords, tokens, or personal info
- **❌ Not validating user permissions** - Always check user permissions in endpoints
- **❌ Using weak passwords** - The template enforces password strength, don't bypass it
- **❌ Not rate limiting** - Add rate limiting to prevent abuse
- **❌ Storing secrets in code** - Use environment variables for all secrets
- **❌ Not validating input data** - Always validate and sanitize user input

### API Design Mistakes
- **❌ Inconsistent response formats** - Use the existing response schemas as templates
- **❌ Not handling errors properly** - Use the existing error handling patterns
- **❌ Missing pagination** - Always paginate list endpoints using the existing utilities
- **❌ Not using domain-based organization** - Follow the existing domain structure
- **❌ Returning too much data** - Use response models to limit data exposure
- **❌ Not documenting endpoints** - Keep OpenAPI documentation current

### Development Workflow Issues

- **❌ Ignoring linting errors** - Fix all `ruff check` issues
- **❌ Not using pre-commit hooks** - Install and use pre-commit for code quality
- **❌ Forgetting to format code** - Run `ruff format .` regularly
- **❌ Not using type hints** - Add type annotations to improve code quality
- **❌ Committing broken code** - Never commit code that doesn't pass tests

### Docker & Environment Issues
- **❌ Not using Docker for consistency** - Always use `docker-compose up -d` for the app
- **❌ Mixing local and Docker environments** - Use Docker for the app, local Python for tools
- **❌ Not checking service health** - Verify services are running with health checks
- **❌ Ignoring environment variables** - Use `.env` files properly, don't hardcode values
- **❌ Not using .env.example** - Keep `.env.example` updated with all required variables
- **❌ Forgetting to rebuild containers** - Rebuild containers when dependencies change

### Performance & Scalability
- **❌ Not using database indexes** - Add indexes for frequently queried fields
- **❌ N+1 query problems** - Use SQLAlchemy's `selectinload()` for relationships
- **❌ Not caching expensive operations** - Use Redis for caching when appropriate
- **❌ Ignoring connection pooling** - The template configures this automatically
- **❌ Not monitoring performance** - Set up performance monitoring early
- **❌ Loading too much data** - Use pagination and filtering to limit data transfer

### Testing Mistakes
- **❌ Not testing edge cases** - Test error conditions and boundary values
- **❌ Not using test fixtures** - Use the existing test utilities and fixtures
- **❌ Testing implementation details** - Test behavior, not implementation
- **❌ Not cleaning up test data** - Use database transactions for test isolation
- **❌ Not testing error paths** - Test what happens when things go wrong
- **❌ Ignoring test coverage** - Aim for high test coverage, especially for critical paths

### Documentation & Maintenance
- **❌ Not updating API docs** - Keep OpenAPI documentation current
- **❌ Ignoring deprecation warnings** - Address warnings promptly
- **❌ Not monitoring logs** - Set up proper logging and monitoring
- **❌ Forgetting to backup data** - Implement regular database backups
- **❌ Not documenting decisions** - Document architectural decisions and trade-offs
- **❌ Ignoring security updates** - Keep dependencies updated for security patches

## 🚀 Advanced Tips & Best Practices

### Code Organization
- **Follow the existing patterns** - Study how the template organizes code by domains
- **Use domain-based structure** - Organize code by business domains (auth, users, system)
- **Keep models simple** - Don't put business logic in models
- **Use services for business logic** - Keep endpoints thin, services thick
- **Separate concerns** - Keep database, business logic, and API layers separate

### Security Best Practices
- **Validate all input** - Use Pydantic schemas for validation
- **Use HTTPS in production** - Never expose APIs over HTTP in production
- **Implement proper CORS** - Configure CORS for your frontend domains
- **Use environment-specific configs** - Different settings for dev/staging/prod
- **Regular security audits** - Review dependencies and code for vulnerabilities

### Performance Optimization
- **Use database indexes** - Add indexes for frequently queried fields
- **Implement caching** - Cache expensive operations with Redis
- **Optimize queries** - Use SQLAlchemy's query optimization features
- **Use background tasks** - Move long-running operations to Celery
- **Monitor performance** - Set up APM tools to track performance

### Deployment Considerations
- **Use environment variables** - Never hardcode configuration
- **Set up monitoring** - Implement logging, metrics, and alerting
- **Plan for scaling** - Design with horizontal scaling in mind
- **Backup strategy** - Implement automated database backups
- **CI/CD pipeline** - Set up automated testing and deployment

## 📚 Additional Resources

### Template Documentation
- [Getting Started](getting-started.md) - Complete setup guide
- [Authentication Guide](authentication.md) - User authentication and security
- [Database Management](database-management.md) - Database setup and migrations
- [Testing Guide](testing-and-development.md) - Testing best practices
- [Deployment Guide](deployment-and-production.md) - Production deployment
- [Optional Features](optional-features.md) - Advanced features and integrations
- [Health Monitoring](health-monitoring.md) - Health check endpoints and monitoring

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Official FastAPI docs
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/) - Database ORM docs
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/) - Data validation
- [Alembic Documentation](https://alembic.sqlalchemy.org/) - Database migrations
- [Docker Documentation](https://docs.docker.com/) - Containerization

### Community & Support
- [FastAPI Discord](https://discord.gg/VQjSZaeJmf) - FastAPI community
- [Stack Overflow](https://stackoverflow.com/questions/tagged/fastapi) - Q&A
- [GitHub Issues](https://github.com/triciaward/fast-api-template/issues) - Template issues

---

**Remember**: The template provides a solid foundation, but you're responsible for building your application on top of it. Take time to understand the patterns and conventions before making changes. 