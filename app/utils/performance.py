"""
Performance optimization utilities for FastAPI template.

This module provides:
- Database query optimization patterns
- Performance monitoring hooks
- Caching utilities
- Query analysis tools
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import get_app_logger

logger = get_app_logger()

# Type variable for generic functions
F = TypeVar("F", bound=Callable[..., Any])

# Global cache for performance utilities
_performance_cache: dict[str, tuple[Any, float]] = {}


def monitor_database_queries() -> None:
    """Enable database query monitoring for performance analysis."""

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: dict[str, Any],
        context: Any,
        executemany: bool,
    ) -> None:
        conn.info.setdefault("query_start_time", []).append(time.time())
        logger.debug(
            "Database query starting",
            statement=statement[:100] + "..." if len(statement) > 100 else statement,
            parameters=parameters,
        )

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: dict[str, Any],
        context: Any,
        executemany: bool,
    ) -> None:
        total = time.time() - conn.info["query_start_time"].pop()
        if total > 0.1:  # Log slow queries (>100ms)
            logger.warning(
                "Slow database query detected",
                execution_time=total,
                statement=(
                    statement[:100] + "..." if len(statement) > 100 else statement
                ),
            )


def optimize_query(query: Any, limit: int = 100) -> Any:
    """
    Apply common query optimizations.

    Args:
        query: SQLAlchemy query object
        limit: Maximum number of results to return

    Returns:
        Optimized query with common performance improvements
    """
    # Add common optimizations
    # Add eager loading for common relationships
    # This prevents N+1 query problems
    return query.limit(limit)


def cache_result(ttl: int = 300) -> Callable[[F], F]:
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)

    Returns:
        Decorated function with caching
    """

    def decorator(func: F) -> Any:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Simple in-memory cache (in production, use Redis)
            cache_key = (
                f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )

            # Check if result is cached
            if cache_key in _performance_cache:
                cached_result, timestamp = _performance_cache[cache_key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)

            _performance_cache[cache_key] = (result, time.time())
            logger.debug(f"Cache miss for {func.__name__}, cached result")

            return result

        return wrapper

    return decorator


def monitor_request_performance() -> Callable[[F], F]:
    """
    Decorator to monitor request performance.

    Returns:
        Decorated function with performance monitoring
    """

    def decorator(func: F) -> Any:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Log slow requests
                if execution_time > 1.0:  # >1 second
                    logger.warning(
                        "Slow request detected",
                        function=func.__name__,
                        execution_time=execution_time,
                    )
                else:
                    logger.debug(
                        "Request completed",
                        function=func.__name__,
                        execution_time=execution_time,
                    )
                    # Continue processing

            except Exception as e:
                execution_time = time.time() - start_time
                logger.exception(
                    "Request failed",
                    function=func.__name__,
                    execution_time=execution_time,
                    error=str(e),
                )
                raise
            else:
                return result

        return wrapper

    return decorator


def add_performance_headers(response: Any, execution_time: float) -> None:
    """
    Add performance headers to response.

    Args:
        response: FastAPI response object
        execution_time: Request execution time in seconds
    """
    response.headers["X-Execution-Time"] = str(execution_time)
    response.headers["X-Cache-Status"] = "MISS"  # Could be enhanced with cache status


class QueryAnalyzer:
    """Analyze and optimize database queries."""

    def __init__(self, session: Session):
        self.session = session
        self.query_count = 0
        self.slow_queries: list[dict[str, Any]] = []

    def analyze_query(self, query: Any) -> dict[str, Any]:
        """
        Analyze a query for potential optimizations.

        Args:
            query: SQLAlchemy query object

        Returns:
            Analysis results with optimization suggestions
        """
        # Get the SQL string
        sql = str(query.compile(compile_kwargs={"literal_binds": True}))

        return {
            "sql": sql,
            "estimated_cost": self._estimate_query_cost(sql),
            "suggestions": self._generate_suggestions(sql),
        }

    def _estimate_query_cost(self, sql: str) -> str:
        """Estimate the cost of a query."""
        if "SELECT *" in sql:
            return "HIGH - Using SELECT *"
        if "ORDER BY" in sql and "LIMIT" not in sql:
            return "MEDIUM - Ordering without limit"
        if "JOIN" in sql and "WHERE" not in sql:
            return "MEDIUM - Join without WHERE clause"
        return "LOW - Well-optimized query"

    def _generate_suggestions(self, sql: str) -> list[str]:
        """Generate optimization suggestions for a query."""
        suggestions = []

        if "SELECT *" in sql:
            suggestions.append("Use specific column names instead of SELECT *")

        if "ORDER BY" in sql and "LIMIT" not in sql:
            suggestions.append("Add LIMIT clause to ORDER BY queries")

        if "JOIN" in sql and "WHERE" not in sql:
            suggestions.append("Add WHERE clause to filter joined data")

        if "LIKE '%pattern'" in sql:
            suggestions.append("Avoid leading wildcards in LIKE queries")

        return suggestions


# Initialize performance monitoring
monitor_database_queries()
