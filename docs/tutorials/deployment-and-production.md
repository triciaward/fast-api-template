# Deployment and Production Tutorial

Welcome to the deployment and production tutorial! This guide will teach you how to take your FastAPI application from development to production, ensuring it's secure, scalable, and reliable.

---

## 🚦 What You Need (Production Checklist)

✅ A VPS like Hetzner, DigitalOcean, or AWS EC2  
✅ [Coolify](https://coolify.io/docs/) installed (or another PaaS)  
✅ Your repo pushed to GitHub  
✅ Domain managed via Cloudflare (recommended)  
✅ Docker and Docker Compose installed  
✅ A `.env.production` file with your secrets  

---

## What is Production Deployment?

Think of production deployment like opening a restaurant. You've been cooking in your kitchen (development), but now you need to:
- **Set up a proper restaurant** (production server)
- **Hire staff** (deploy your application)
- **Ensure food safety** (security measures)
- **Handle many customers** (scalability)
- **Monitor everything** (health checks and logging)

---

## Production File Structure

```
your-project/
├── .env.production          # Production secrets (never commit)
├── docker-compose.yml       # Production services
├── Dockerfile              # App container definition
├── requirements.txt        # Python dependencies
├── alembic/               # Database migrations
├── app/                   # Your FastAPI application
└── scripts/               # Deployment utilities
```

---

## Example .env.production

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@prod-db:5432/prod_db
SECRET_KEY=your-super-secure-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-production-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=True
ENABLE_RATE_LIMITING=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REGISTER=3/minute
ENABLE_REDIS=true
REDIS_URL=redis://prod-redis:6379/0
ENABLE_SENTRY=true
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production
```

---

## Example docker-compose.yml (Production)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: ${COMPOSE_PROJECT_NAME:-fast-api-template}-postgres-1
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

  # Optional Redis service - only used when ENABLE_REDIS=true
  redis:
    image: redis:7-alpine
    container_name: ${COMPOSE_PROJECT_NAME:-fast-api-template}-redis-1
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network
    restart: unless-stopped
    profiles:
      - redis  # Only start when explicitly requested

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ${COMPOSE_PROJECT_NAME:-fast-api-template}-api-1
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}
      ENABLE_REDIS: ${ENABLE_REDIS:-false}
      ENABLE_WEBSOCKETS: ${ENABLE_WEBSOCKETS:-false}
      ENABLE_CELERY: ${ENABLE_CELERY:-false}
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      ENABLE_SENTRY: ${ENABLE_SENTRY:-false}
      SENTRY_DSN: ${SENTRY_DSN:-}
      SENTRY_ENVIRONMENT: ${SENTRY_ENVIRONMENT:-production}
    ports:
      - "${API_PORT}:8000"
    depends_on:
      - postgres
    networks:
      - app-network
    restart: unless-stopped
    volumes:
      - .:/code  # Mount entire project for live code editing
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Optional Celery worker service - only used when ENABLE_CELERY=true
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ${COMPOSE_PROJECT_NAME:-fast-api-template}-celery-worker-1
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}
      ENABLE_REDIS: ${ENABLE_REDIS:-false}
      ENABLE_WEBSOCKETS: ${ENABLE_WEBSOCKETS:-false}
      ENABLE_CELERY: ${ENABLE_CELERY:-false}
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      ENABLE_SENTRY: ${ENABLE_SENTRY:-false}
      SENTRY_DSN: ${SENTRY_DSN:-}
      SENTRY_ENVIRONMENT: ${SENTRY_ENVIRONMENT:-production}
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    restart: unless-stopped
    profiles:
      - celery  # Only start when explicitly requested

volumes:
  postgres_data:
    name: ${COMPOSE_PROJECT_NAME:-fast-api-template}-postgres_data
  redis_data:
    name: ${COMPOSE_PROJECT_NAME:-fast-api-template}-redis_data

networks:
  app-network:
    name: ${COMPOSE_PROJECT_NAME:-fast-api-template}-app-network
    driver: bridge
```

> **Important:** Make sure the `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` values in your `.env.production` file match what you set in `docker-compose.yml`. If they don't match, your app will not be able to connect to the database.

---

## Production Settings (What to Check)

- `ENVIRONMENT=production`
- `SECRET_KEY` is strong and unique (use `openssl rand -hex 32`)
- `DATABASE_URL` points to your production DB
- `ENABLE_RATE_LIMITING=true`
- `ENABLE_REDIS=true` (if using Redis)
- `ENABLE_SENTRY=true` (if using Sentry/GlitchTip)
- All email and OAuth credentials are set for production
- CORS is restricted to your production domains
- `SENTRY_ENVIRONMENT=production`

---

## Deploying with Coolify (Step-by-Step)

```mermaid
flowchart TD
  A[Push to GitHub] --> B[Login to Coolify]
  B --> C[Add New App]
  C --> D[Select Repository]
  D --> E[Configure Build]
  E --> F[Set Environment Variables]
  F --> G[Deploy]
  G --> H[Monitor Logs]
```

### Coolify Deployment Flow

1. **Push your code to GitHub**
2. **Log in to your Coolify dashboard**
3. **Click "Add New App"**
4. **Select your GitHub repo**
5. **Set build and run commands** (e.g., `docker-compose up -d` or `uvicorn app.main:app --host 0.0.0.0 --port 8000`)
6. **Add environment variables** (copy from `.env.production`)
7. **Deploy!**

> **Migrations Note:** By default, Coolify does NOT run database migrations automatically. After your app is deployed, you must run migrations manually (e.g., via the Coolify web terminal or SSH):
> ```bash
> docker-compose exec api alembic upgrade head
> ```
> You can automate this by adding a custom build or release step if desired.

> For more, see [Coolify's official docs](https://coolify.io/docs/).

---

## Caddy + Cloudflare Setup (for HTTPS & Proxy)

**Caddyfile Example:**

```
yourdomain.com {
  reverse_proxy localhost:8000
  tls {
    dns cloudflare {env.CLOUDFLARE_API_TOKEN}
  }
}
```

- [Caddy Cloudflare DNS Docs](https://caddyserver.com/docs/automatic-https#dns-provider)
- [Cloudflare API Tokens](https://developers.cloudflare.com/api/tokens/create/)

**Architecture Overview:**

```mermaid
graph TD
  A[User DNS Query] --> B[Cloudflare DNS]
  B --> C[Caddy Reverse Proxy]
  C --> D[FastAPI App]
```

**Steps:**
1. Get a Cloudflare API token with DNS edit permissions
2. Set `CLOUDFLARE_API_TOKEN` in your environment
3. Use the above Caddyfile to enable HTTPS and proxy to your app

---

## Where to Put Files

- Place `.env.production` in your project root (never commit to git)
- Place `docker-compose.yml` in your project root
- Place `Caddyfile` in your server's home directory (or wherever Caddy runs)

---

## Quick Reference: Deploying

1. **Build and run Docker containers:**
    ```bash
    docker-compose -f docker-compose.yml up -d
    ```
2. **Run migrations:**
    ```bash
    docker-compose exec api alembic upgrade head
    ```
3. **Create a superuser:**
    ```bash
    docker-compose exec api python app/bootstrap_superuser.py
    ```
4. **Set up Caddy for HTTPS**
5. **Point your domain to your server's IP in Cloudflare**

---

## Useful Tools & Links

### Database Management
- **[pgAdmin](https://www.pgadmin.org/)**: Web-based PostgreSQL admin tool
- **[Beekeeper Studio](https://www.beekeeperstudio.io/)**: Modern SQL editor and database manager
- **[DBeaver](https://dbeaver.io/)**: Universal database tool

### Monitoring & Logs
- **[Coolify Docs](https://coolify.io/docs/)**: Self-hosted PaaS platform
- **[Caddy Docs](https://caddyserver.com/docs/)**: Modern web server with automatic HTTPS
- **[Cloudflare Docs](https://developers.cloudflare.com/)**: CDN and DNS management

### Development Tools
- **[Docker Compose](https://docs.docker.com/compose/)**: Multi-container Docker applications
- **[GitHub Actions](https://docs.github.com/en/actions)**: CI/CD automation

---

## Troubleshooting

- **App won't start?** Check environment variables and logs
- **Database connection errors?** Check `DATABASE_URL` and DB status
- **HTTPS not working?** Check Caddy and Cloudflare DNS settings
- **Email not sending?** Check SMTP credentials

---

## Glossary

- **VPS**: Virtual Private Server, a virtualized server hosted by a cloud provider.
- **PaaS**: Platform as a Service, a cloud computing model that provides a platform for developing and deploying applications.
- **CI/CD**: Continuous Integration/Continuous Deployment, automated processes for building, testing, and deploying code.
- **DNS**: Domain Name System, translates domain names to IP addresses.
- **CDN**: Content Delivery Network, distributes content across multiple servers worldwide for faster access.
- **SSL/TLS**: Security protocols for encrypting data transmitted over the internet.

---

## Next Steps

Now that you understand production deployment, you can:
1. **Choose your deployment platform** (Coolify, Heroku, AWS, GCP, etc.)
2. **Set up monitoring and alerting** for your application
3. **Implement automated backups** for data safety
4. **Configure CI/CD pipelines** for automated deployments
5. **Set up staging environments** for testing before production

Remember: Production deployment is about reliability, security, and scalability. Start simple and add complexity as your application grows! 