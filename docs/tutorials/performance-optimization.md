# Performance Optimization Guide

This guide covers the comprehensive performance monitoring and optimization features included in the FastAPI template.

## ⚡ Overview

The template includes a complete performance monitoring system with tools for:

- **Database Query Monitoring** - Automatic detection of slow queries
- **Request Performance Tracking** - Monitor endpoint response times
- **Caching System** - In-memory caching with TTL support
- **Query Analysis** - SQL analysis with optimization suggestions
- **Performance Utilities** - Decorators and utilities for optimization

## 🛠️ Performance Utilities

### Import the Performance Module

```python
from app.utils.performance import (
    monitor_database_queries,
    monitor_request_performance,
    cache_result,
    QueryAnalyzer,
    optimize_query
)
```

### 1. Database Query Monitoring

**Enable automatic database query monitoring**:

```python
# In your main.py or application startup
from app.utils.performance import monitor_database_queries

# Enable database query monitoring (automatically enabled)
monitor_database_queries()
```

**What this does**:
- Automatically logs all database queries
- Detects slow queries (>100ms)
- Provides query execution time
- Logs SQL statements (truncated for security)

**Example output**:
```
INFO - Database query starting: SELECT * FROM users WHERE email = ?
WARNING - Slow database query detected (250ms): SELECT * FROM users JOIN posts ON users.id = posts.user_id
```

### 2. Request Performance Monitoring

**Monitor endpoint performance automatically**:

```python
from app.utils.performance import monitor_request_performance

@monitor_request_performance()
async def my_endpoint():
    """This endpoint will be automatically monitored."""
    # Your endpoint logic here
    return {"message": "Hello World"}
```

**Features**:
- Automatic request timing
- Slow request detection (>1 second)
- Performance logging
- Execution time tracking

**Example output**:
```
INFO - Request completed: my_endpoint (execution_time=0.045)
WARNING - Slow request detected: my_endpoint (execution_time=1.234)
```

### 3. Caching System

**Cache expensive operations**:

```python
from app.utils.performance import cache_result

@cache_result(ttl=300)  # Cache for 5 minutes
async def expensive_database_query(user_id: int):
    """This result will be cached for 5 minutes."""
    # Expensive database operation
    result = await db.execute(
        "SELECT * FROM users WHERE id = :user_id",
        {"user_id": user_id}
    )
    return result.fetchall()

@cache_result(ttl=60)  # Cache for 1 minute
async def external_api_call(api_key: str):
    """Cache external API calls."""
    response = await httpx.get(f"https://api.example.com/data?key={api_key}")
    return response.json()
```

**Cache Features**:
- Configurable TTL (Time To Live)
- Automatic cache invalidation
- Memory-efficient storage
- Cache hit/miss logging

### 4. Query Analysis

**Analyze and optimize database queries**:

```python
from app.utils.performance import QueryAnalyzer
from sqlalchemy.orm import Session

# Create a query analyzer
analyzer = QueryAnalyzer(db_session)

# Analyze a query
query = db_session.query(User).filter(User.email == "test@example.com")
analysis = analyzer.analyze_query(query)

print(analysis)
# Output:
# {
#     "sql": "SELECT users.id, users.email FROM users WHERE users.email = ?",
#     "estimated_cost": "LOW - Well-optimized query",
#     "suggestions": []
# }
```

**Analysis Features**:
- SQL query cost estimation
- Optimization suggestions
- Performance anti-pattern detection
- Query improvement recommendations

### 5. Query Optimization

**Optimize database queries**:

```python
from app.utils.performance import optimize_query

# Optimize a query with limits and eager loading
optimized_query = optimize_query(
    db_session.query(User).join(Post),
    limit=100
)

# The optimized query includes:
# - LIMIT clause
# - Eager loading for relationships
# - Optimized joins
```

## 📊 Performance Monitoring Examples

### 1. Monitor API Endpoints

```python
from fastapi import APIRouter
from app.utils.performance import monitor_request_performance

router = APIRouter()

@router.get("/users")
@monitor_request_performance()
async def get_users(skip: int = 0, limit: int = 100):
    """Get users with performance monitoring."""
    users = await db.fetch_all(
        "SELECT * FROM users LIMIT :limit OFFSET :skip",
        {"limit": limit, "skip": skip}
    )
    return users

@router.get("/users/{user_id}")
@monitor_request_performance()
async def get_user(user_id: int):
    """Get specific user with performance monitoring."""
    user = await db.fetch_one(
        "SELECT * FROM users WHERE id = :user_id",
        {"user_id": user_id}
    )
    return user
```

### 2. Cache Expensive Operations

```python
from app.utils.performance import cache_result

@cache_result(ttl=3600)  # Cache for 1 hour
async def get_user_statistics():
    """Cache expensive statistics calculation."""
    stats = await db.fetch_one("""
        SELECT 
            COUNT(*) as total_users,
            COUNT(CASE WHEN is_verified = true THEN 1 END) as verified_users,
            COUNT(CASE WHEN date_created >= NOW() - INTERVAL '7 days' THEN 1 END) as new_users
        FROM users
    """)
    return stats

@cache_result(ttl=300)  # Cache for 5 minutes
async def get_external_data(api_key: str):
    """Cache external API calls."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.external.com/data",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        return response.json()
```

### 3. Analyze Database Performance

```python
from app.utils.performance import QueryAnalyzer

async def analyze_user_queries():
    """Analyze user-related queries for optimization."""
    analyzer = QueryAnalyzer(db_session)
    
    # Analyze different query patterns
    queries = [
        db_session.query(User).filter(User.email.like("%@example.com")),
        db_session.query(User).join(Post).filter(Post.published == True),
        db_session.query(User).filter(User.date_created >= datetime.now() - timedelta(days=7))
    ]
    
    for i, query in enumerate(queries):
        analysis = analyzer.analyze_query(query)
        print(f"Query {i+1} Analysis:")
        print(f"  SQL: {analysis['sql']}")
        print(f"  Cost: {analysis['estimated_cost']}")
        print(f"  Suggestions: {analysis['suggestions']}")
        print()
```

## 🔧 Configuration

### Performance Monitoring Features

The performance monitoring system is **enabled by default** and includes:

- **Database Query Monitoring**: Automatically logs all database queries
- **Slow Query Detection**: Logs queries taking longer than 100ms
- **Request Performance Tracking**: Monitors endpoint execution times
- **Caching System**: In-memory caching with configurable TTL
- **Query Analysis**: SQL analysis with optimization suggestions

### Custom Performance Monitoring

```python
from app.utils.performance import monitor_request_performance
from app.core.logging_config import get_app_logger

logger = get_app_logger()

@monitor_request_performance()
async def custom_monitored_endpoint():
    """Custom endpoint with additional monitoring."""
    start_time = time.time()
    
    try:
        # Your endpoint logic
        result = await expensive_operation()
        
        # Custom performance logging
        execution_time = time.time() - start_time
        logger.info(
            "Custom endpoint completed",
            execution_time=execution_time,
            result_count=len(result)
        )
        
        return result
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Custom endpoint failed",
            execution_time=execution_time,
            error=str(e)
        )
        raise
```

## 📈 Performance Metrics

### 1. Database Metrics

Track database performance:

```python
from app.utils.performance import QueryAnalyzer

async def get_database_metrics():
    """Get comprehensive database performance metrics."""
    analyzer = QueryAnalyzer(db_session)
    
    # Get query statistics
    stats = {
        "total_queries": analyzer.query_count,
        "slow_queries": len(analyzer.slow_queries),
        "average_query_time": sum(q["time"] for q in analyzer.slow_queries) / len(analyzer.slow_queries) if analyzer.slow_queries else 0
    }
    
    return stats
```

### 2. Application Metrics

Track application performance:

```python
import psutil
import time

async def get_application_metrics():
    """Get application performance metrics."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "uptime": time.time() - start_time,
        "active_connections": len(psutil.net_connections())
    }
```

### 3. Custom Metrics

Create custom performance metrics:

```python
from app.utils.performance import cache_result

# Track API usage
api_usage_counter = 0

@cache_result(ttl=60)
async def get_api_usage_metrics():
    """Get API usage metrics."""
    global api_usage_counter
    
    return {
        "total_requests": api_usage_counter,
        "requests_per_minute": api_usage_counter / 60,
        "cache_hit_rate": 0.85,  # Example metric
        "average_response_time": 0.045  # seconds
    }

# Increment counter in your endpoints
@monitor_request_performance()
async def tracked_endpoint():
    global api_usage_counter
    api_usage_counter += 1
    # Your endpoint logic
    return {"message": "Tracked"}
```

## 🚨 Performance Alerts

### 1. Slow Query Alerts

```python
from app.utils.performance import monitor_database_queries
from app.core.logging_config import get_app_logger

logger = get_app_logger()

def slow_query_alert(query_time: float, sql: str):
    """Alert when slow queries are detected."""
    if query_time > 1000:  # 1 second
        logger.critical(
            "Critical slow query detected",
            query_time=query_time,
            sql=sql[:100] + "..." if len(sql) > 100 else sql
        )
        # Send alert to monitoring system
        send_alert("Critical slow query detected", {
            "query_time": query_time,
            "sql": sql
        })
```

### 2. Performance Degradation Alerts

```python
async def monitor_performance_degradation():
    """Monitor for performance degradation."""
    metrics = await get_application_metrics()
    
    if metrics["cpu_percent"] > 80:
        send_alert("High CPU usage detected", metrics)
    
    if metrics["memory_percent"] > 90:
        send_alert("High memory usage detected", metrics)
    
    if metrics["average_response_time"] > 1.0:
        send_alert("High response time detected", metrics)
```

## 🔍 Performance Troubleshooting

### 1. Identify Slow Queries

```python
from app.utils.performance import QueryAnalyzer

async def identify_slow_queries():
    """Identify and analyze slow queries."""
    analyzer = QueryAnalyzer(db_session)
    
    # Get all slow queries
    slow_queries = analyzer.slow_queries
    
    for query in slow_queries:
        analysis = analyzer.analyze_query(query["query"])
        print(f"Slow Query Analysis:")
        print(f"  Time: {query['time']}ms")
        print(f"  SQL: {analysis['sql']}")
        print(f"  Suggestions: {analysis['suggestions']}")
        print()
```

### 2. Optimize Database Queries

```python
from app.utils.performance import optimize_query

async def optimize_user_queries():
    """Optimize user-related queries."""
    
    # Original query
    original_query = db_session.query(User).join(Post)
    
    # Optimized query
    optimized_query = optimize_query(original_query, limit=100)
    
    # Compare performance
    start_time = time.time()
    original_result = await original_query.all()
    original_time = time.time() - start_time
    
    start_time = time.time()
    optimized_result = await optimized_query.all()
    optimized_time = time.time() - start_time
    
    print(f"Original query time: {original_time:.3f}s")
    print(f"Optimized query time: {optimized_time:.3f}s")
    print(f"Improvement: {((original_time - optimized_time) / original_time * 100):.1f}%")
```

### 3. Cache Performance Analysis

```python
from app.utils.performance import cache_result

# Track cache performance
cache_hits = 0
cache_misses = 0

@cache_result(ttl=300)
async def tracked_cached_function():
    """Track cache performance."""
    global cache_hits, cache_misses
    
    # Your expensive operation
    result = expensive_operation()
    
    # Track cache performance
    cache_misses += 1
    return result

async def get_cache_metrics():
    """Get cache performance metrics."""
    total_requests = cache_hits + cache_misses
    hit_rate = cache_hits / total_requests if total_requests > 0 else 0
    
    return {
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "hit_rate": hit_rate,
        "total_requests": total_requests
    }
```

## 📚 Best Practices

### 1. Query Optimization

- **Use indexes** on frequently queried columns
- **Limit result sets** to prevent large data transfers
- **Use eager loading** to prevent N+1 query problems
- **Optimize joins** by selecting only needed columns
- **Use pagination** for large datasets

### 2. Caching Strategy

- **Cache expensive operations** (database queries, API calls)
- **Set appropriate TTL** based on data freshness requirements
- **Use cache invalidation** for data that changes frequently
- **Monitor cache hit rates** to optimize cache size
- **Consider distributed caching** for multiple instances

### 3. Monitoring Strategy

- **Set realistic thresholds** for slow query detection
- **Monitor trends** rather than individual events
- **Use different monitoring levels** for different environments
- **Implement alerting** for critical performance issues
- **Regular performance reviews** to identify optimization opportunities

### 4. Production Considerations


- **Monitor resource usage** of monitoring tools themselves
- **Set up proper logging** for performance data
- **Implement performance budgets** for critical endpoints
- **Regular performance audits** to maintain optimal performance

## 🎯 Next Steps

1. **Enable performance monitoring** - Start with basic query monitoring
2. **Identify bottlenecks** - Use the analysis tools to find slow queries
3. **Implement caching** - Add caching to expensive operations
4. **Set up alerts** - Configure alerts for performance issues
5. **Optimize continuously** - Regular performance reviews and improvements

---

**⚡ Your application now has enterprise-grade performance monitoring! Use these tools to ensure your application is fast, efficient, and scalable.** 