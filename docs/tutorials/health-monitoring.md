# Health Monitoring Guide

This guide covers the comprehensive health monitoring system included in the FastAPI template.

## 🏥 Overview

The template includes a complete health monitoring system with 7 different endpoints designed for various use cases:

- **Load Balancer Health Checks** - Simple status checks
- **Kubernetes Probes** - Readiness and liveness checks
- **Comprehensive Monitoring** - Detailed system status
- **Database Health** - Database-specific monitoring
- **Application Metrics** - Performance and usage metrics

## 📊 Health Check Endpoints

### 1. Basic Health Check
**Endpoint**: `GET /api/v1/health`

**Purpose**: Simple application status check

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T18:05:06.289177Z",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": {"status": "unknown"},
    "application": "healthy",
    "redis": {"status": "unknown"},
    "external_services": {"status": "unknown"}
  }
}
```

### 2. Simple Health Check
**Endpoint**: `GET /api/v1/health/simple`

**Purpose**: Load balancer health check (minimal response)

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T18:05:06.289177Z"
}
```

### 3. Readiness Probe
**Endpoint**: `GET /api/v1/health/ready`

**Purpose**: Kubernetes readiness probe - checks if app is ready to receive traffic

**Response** (Success):
```json
{
  "ready": true,
  "timestamp": "2025-08-06T18:05:06.289177Z",
  "components": {
    "database": {"ready": true},
    "application": {"ready": true}
  }
}
```

**Response** (Failure):
```json
{
  "error": {
    "message": "Service not ready",
    "type": "ReadinessError",
    "code": "service_unavailable"
  }
}
```

### 4. Liveness Probe
**Endpoint**: `GET /api/v1/health/live`

**Purpose**: Kubernetes liveness probe - checks if app is alive and should not be restarted

**Response**:
```json
{
  "alive": "true",
  "timestamp": "2025-08-06T18:05:06.289177Z"
}
```

### 5. Detailed Health Check
**Endpoint**: `GET /api/v1/health/detailed`

**Purpose**: Comprehensive system status with all component checks

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T18:05:06.289177Z",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time": 0.002
    },
    "redis": {
      "status": "healthy",
      "response_time": 0.001
    },
    "external_services": {
      "email": {
        "status": "configured",
        "host": "smtp.gmail.com",
        "port": 587
      }
    }
  }
}
```

### 6. Database Health Check
**Endpoint**: `GET /api/v1/health/database`

**Purpose**: Database-specific health and performance metrics

**Response**:
```json
{
  "status": "healthy",
  "response_time": 0.002,
  "table_count": 8,
  "connection_pool": {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_recycle": 3600
  },
  "database_url": "localhost:5432/fastapi_template"
}
```

### 7. Metrics Endpoint
**Endpoint**: `GET /api/v1/health/metrics`

**Purpose**: Application metrics and performance data

**Response**:
```json
{
  "application": {
    "uptime": 3600,
    "version": "1.0.0",
    "environment": "development"
  },
  "system": {
    "cpu_percent": 2.5,
    "memory_percent": 15.3,
    "disk_usage_percent": 45.2
  },
  "database": {
    "active_connections": 3,
    "pool_size": 5,
    "overflow": 0
  }
}
```

## 🚀 Usage Examples

### Load Balancer Configuration

**Nginx Configuration**:
```nginx
upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check for load balancer
    location /health {
        proxy_pass http://fastapi_backend/api/v1/health/simple;
        access_log off;
    }
}
```

### Kubernetes Configuration

**Deployment with Health Checks**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: fastapi
        image: your-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
        # Readiness probe
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        # Liveness probe
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
```

### Docker Compose with Health Checks

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/simple"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fastapi_template
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: dev_password_123
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

## 🔧 Configuration

### Environment Variables

Configure health check behavior through environment variables:

```bash
# Enable/disable specific health checks
ENABLE_REDIS=true
ENABLE_CELERY=false

# Health check timeouts
HEALTH_CHECK_TIMEOUT=5
DATABASE_HEALTH_TIMEOUT=3

# Metrics collection
ENABLE_METRICS=true
METRICS_INTERVAL=60
```

### Custom Health Checks

Add custom health checks to your application:

```python
from app.api.api_v1.endpoints.health import router
from app.core.logging_config import get_app_logger

logger = get_app_logger()

@router.get("/health/custom")
async def custom_health_check():
    """Custom health check for your specific needs."""
    try:
        # Your custom health check logic
        external_service_status = check_external_service()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "custom_check": {
                "external_service": external_service_status,
                "custom_metric": get_custom_metric()
            }
        }
    except Exception as e:
        logger.error("Custom health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
```

## 📊 Monitoring Integration

### Prometheus Metrics

The metrics endpoint can be integrated with Prometheus:

```python
# Add Prometheus metrics to your health checks
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
health_check_counter = Counter('health_checks_total', 'Total health checks')
health_check_duration = Histogram('health_check_duration_seconds', 'Health check duration')

@router.get("/health/metrics")
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint."""
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

### Grafana Dashboard

Create a Grafana dashboard for your health metrics:

```json
{
  "dashboard": {
    "title": "FastAPI Health Dashboard",
    "panels": [
      {
        "title": "Health Check Status",
        "type": "stat",
        "targets": [
          {
            "expr": "health_checks_total",
            "legendFormat": "Total Health Checks"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "health_check_duration_seconds",
            "legendFormat": "Health Check Duration"
          }
        ]
      }
    ]
  }
}
```

## 🚨 Alerting

### Health Check Alerts

Set up alerts for health check failures:

```python
# Example alerting logic
async def send_health_alert(status: str, details: dict):
    """Send alert when health check fails."""
    if status == "unhealthy":
        await send_slack_alert(
            channel="#alerts",
            message=f"🚨 Health check failed: {details}"
        )
        await send_email_alert(
            subject="Health Check Alert",
            body=f"Application health check failed: {details}"
        )
```

### Kubernetes Alerts

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: fastapi-health-alerts
spec:
  groups:
  - name: fastapi-health
    rules:
    - alert: FastAPIHealthCheckFailed
      expr: up{job="fastapi"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "FastAPI health check failed"
        description: "FastAPI application is not responding to health checks"
```

## 🔍 Troubleshooting

### Common Issues

**1. Health Check Timeouts**
```bash
# Check if the application is responding
curl -v http://localhost:8000/api/v1/health/simple

# Check application logs
docker-compose logs api
```

**2. Database Connection Issues**
```bash
# Test database connectivity
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"

# Check database health endpoint
curl http://localhost:8000/api/v1/health/database
```

**3. Redis Connection Issues**
```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping

# Check if Redis is enabled in health checks
curl http://localhost:8000/api/v1/health/detailed
```

### Debug Mode

Enable debug logging for health checks:

```python
# In your application startup
import logging
logging.getLogger("app.api.api_v1.endpoints.health").setLevel(logging.DEBUG)
```

## 📚 Best Practices

### 1. Response Time Optimization
- Keep health check endpoints fast (< 100ms)
- Use caching for expensive checks
- Implement timeouts for external dependencies

### 2. Security Considerations
- Health endpoints should not expose sensitive information
- Use appropriate HTTP status codes
- Consider authentication for detailed health checks

### 3. Monitoring Strategy
- Use different endpoints for different purposes
- Set appropriate timeouts and intervals
- Implement proper alerting and escalation

### 4. Production Deployment
- Test health checks in staging environment
- Monitor health check response times
- Set up proper logging and alerting

## 🎯 Next Steps

1. **Test all health endpoints** - Verify they work in your environment
2. **Configure monitoring** - Set up Prometheus/Grafana integration
3. **Set up alerting** - Configure alerts for health check failures
4. **Customize for your needs** - Add application-specific health checks
5. **Deploy with confidence** - Use health checks in your production environment

---

**🏥 Your application now has enterprise-grade health monitoring! Use these endpoints to ensure your application is always healthy and responsive.** 