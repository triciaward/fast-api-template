"""
Celery task management endpoints.

This module provides API endpoints for submitting, monitoring, and managing
Celery background tasks.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.logging_config import get_app_logger
from app.services.celery import (
    cancel_task,
    get_active_tasks,
    get_celery_stats,
    get_task_status,
    is_celery_enabled,
    submit_task,
)

# Get logger
app_logger = get_app_logger()

router = APIRouter()


# Pydantic models for request/response
class TaskSubmitRequest(BaseModel):
    task_name: str = Field(..., description="Name of the task to execute")
    args: list[Any] = Field(default=[], description="Positional arguments for the task")
    kwargs: dict[str, Any] = Field(
        default={}, description="Keyword arguments for the task"
    )


class TaskSubmitResponse(BaseModel):
    task_id: str = Field(..., description="ID of the submitted task")
    task_name: str = Field(..., description="Name of the submitted task")
    status: str = Field(..., description="Initial status of the task")
    message: str = Field(..., description="Response message")


class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    status: str = Field(..., description="Current status of the task")
    ready: bool = Field(..., description="Whether the task is complete")
    successful: bool = Field(..., description="Whether the task completed successfully")
    failed: bool = Field(..., description="Whether the task failed")
    result: Optional[Any] = Field(
        None, description="Task result if completed successfully"
    )
    error: Optional[str] = Field(None, description="Error message if task failed")


class TaskCancelResponse(BaseModel):
    task_id: str = Field(..., description="ID of the cancelled task")
    cancelled: bool = Field(
        ..., description="Whether the task was cancelled successfully"
    )
    message: str = Field(..., description="Response message")


class ActiveTaskResponse(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    name: str = Field(..., description="Name of the task")
    worker: str = Field(..., description="Worker processing the task")
    args: list[Any] = Field(..., description="Task arguments")
    kwargs: dict[str, Any] = Field(..., description="Task keyword arguments")
    time_start: Optional[float] = Field(None, description="Task start time")


class CeleryStatsResponse(BaseModel):
    enabled: bool = Field(..., description="Whether Celery is enabled")
    broker_url: Optional[str] = Field(None, description="Celery broker URL")
    result_backend: Optional[str] = Field(None, description="Celery result backend")
    active_workers: Optional[int] = Field(None, description="Number of active workers")
    registered_tasks: Optional[int] = Field(
        None, description="Number of registered tasks"
    )
    active_tasks: Optional[int] = Field(None, description="Number of active tasks")
    error: Optional[str] = Field(
        None, description="Error message if stats retrieval failed"
    )


def check_celery_enabled() -> None:
    """Dependency to check if Celery is enabled."""
    if not is_celery_enabled():
        raise HTTPException(
            status_code=503,
            detail="Celery is not enabled. Set ENABLE_CELERY=true to enable background tasks.",
        )


@router.get("/status", response_model=CeleryStatsResponse)
async def get_celery_status() -> CeleryStatsResponse:
    """
    Get Celery service status and statistics.

    Returns:
        CeleryStatsResponse: Celery status and statistics
    """
    try:
        stats = get_celery_stats()
        return CeleryStatsResponse(**stats)
    except Exception as e:
        app_logger.error("Failed to get Celery status", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get Celery status")


@router.post("/tasks/submit", response_model=TaskSubmitResponse)
async def submit_celery_task(
    request: TaskSubmitRequest, _: None = Depends(check_celery_enabled)
) -> TaskSubmitResponse:
    """
    Submit a new Celery task.

    Args:
        request: Task submission request

    Returns:
        TaskSubmitResponse: Task submission result
    """
    try:
        app_logger.info(
            "Submitting Celery task",
            task_name=request.task_name,
            args=request.args,
            kwargs=request.kwargs,
        )

        result = submit_task(request.task_name, *request.args, **request.kwargs)

        if result is None:
            raise HTTPException(status_code=500, detail="Failed to submit task")

        response = TaskSubmitResponse(
            task_id=result.id,
            task_name=request.task_name,
            status="PENDING",
            message="Task submitted successfully",
        )

        app_logger.info(
            "Celery task submitted successfully",
            task_id=result.id,
            task_name=request.task_name,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(
            "Failed to submit Celery task",
            task_name=request.task_name,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to submit task")


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_celery_task_status(
    task_id: str, _: None = Depends(check_celery_enabled)
) -> TaskStatusResponse:
    """
    Get the status of a Celery task.

    Args:
        task_id: ID of the task to check

    Returns:
        TaskStatusResponse: Task status information
    """
    try:
        status_info = get_task_status(task_id)

        if status_info is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return TaskStatusResponse(**status_info)

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(
            "Failed to get task status", task_id=task_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.delete("/tasks/{task_id}/cancel", response_model=TaskCancelResponse)
async def cancel_celery_task(
    task_id: str, _: None = Depends(check_celery_enabled)
) -> TaskCancelResponse:
    """
    Cancel a running Celery task.

    Args:
        task_id: ID of the task to cancel

    Returns:
        TaskCancelResponse: Task cancellation result
    """
    try:
        app_logger.info("Attempting to cancel Celery task", task_id=task_id)

        cancelled = cancel_task(task_id)

        if cancelled:
            response = TaskCancelResponse(
                task_id=task_id, cancelled=True, message="Task cancelled successfully"
            )
            app_logger.info("Celery task cancelled successfully", task_id=task_id)
        else:
            response = TaskCancelResponse(
                task_id=task_id,
                cancelled=False,
                message="Failed to cancel task or task not found",
            )
            app_logger.warning("Failed to cancel Celery task", task_id=task_id)

        return response

    except Exception as e:
        app_logger.error(
            "Failed to cancel task", task_id=task_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/tasks/active", response_model=list[ActiveTaskResponse])
async def get_active_celery_tasks(
    _: None = Depends(check_celery_enabled),
) -> list[ActiveTaskResponse]:
    """
    Get list of currently active Celery tasks.

    Returns:
        List[ActiveTaskResponse]: List of active tasks
    """
    try:
        active_tasks = get_active_tasks()

        return [ActiveTaskResponse(**task) for task in active_tasks]

    except Exception as e:
        app_logger.error("Failed to get active tasks", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get active tasks")


# Convenience endpoints for common tasks
@router.post("/tasks/send-email", response_model=TaskSubmitResponse)
async def submit_email_task(
    to_email: str, subject: str, body: str, _: None = Depends(check_celery_enabled)
) -> TaskSubmitResponse:
    """
    Submit an email sending task.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body

    Returns:
        TaskSubmitResponse: Task submission result
    """
    try:
        result = submit_task(
            "app.services.celery_tasks.send_email_task", to_email, subject, body
        )

        if result is None:
            raise HTTPException(status_code=500, detail="Failed to submit email task")

        return TaskSubmitResponse(
            task_id=result.id,
            task_name="send_email_task",
            status="PENDING",
            message="Email task submitted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(
            "Failed to submit email task",
            to_email=to_email,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to submit email task")


@router.post("/tasks/process-data", response_model=TaskSubmitResponse)
async def submit_data_processing_task(
    data: list[dict[str, Any]], _: None = Depends(check_celery_enabled)
) -> TaskSubmitResponse:
    """
    Submit a data processing task.

    Args:
        data: List of data items to process

    Returns:
        TaskSubmitResponse: Task submission result
    """
    try:
        result = submit_task("app.services.celery_tasks.process_data_task", data)

        if result is None:
            raise HTTPException(
                status_code=500, detail="Failed to submit data processing task"
            )

        return TaskSubmitResponse(
            task_id=result.id,
            task_name="process_data_task",
            status="PENDING",
            message=f"Data processing task submitted successfully for {len(data)} items",
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(
            "Failed to submit data processing task",
            data_count=len(data),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to submit data processing task"
        )


@router.post("/tasks/cleanup", response_model=TaskSubmitResponse)
async def submit_cleanup_task(
    _: None = Depends(check_celery_enabled),
) -> TaskSubmitResponse:
    """
    Submit a cleanup task.

    Returns:
        TaskSubmitResponse: Task submission result
    """
    try:
        result = submit_task("app.services.celery_tasks.cleanup_task")

        if result is None:
            raise HTTPException(status_code=500, detail="Failed to submit cleanup task")

        return TaskSubmitResponse(
            task_id=result.id,
            task_name="cleanup_task",
            status="PENDING",
            message="Cleanup task submitted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error("Failed to submit cleanup task", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit cleanup task")


@router.post("/tasks/long-running", response_model=TaskSubmitResponse)
async def submit_long_running_task(
    duration: int = 60, _: None = Depends(check_celery_enabled)
) -> TaskSubmitResponse:
    """
    Submit a long-running task for testing purposes.

    Args:
        duration: Task duration in seconds (default: 60)

    Returns:
        TaskSubmitResponse: Task submission result
    """
    try:
        result = submit_task("app.services.celery_tasks.long_running_task", duration)

        if result is None:
            raise HTTPException(
                status_code=500, detail="Failed to submit long-running task"
            )

        return TaskSubmitResponse(
            task_id=result.id,
            task_name="long_running_task",
            status="PENDING",
            message=f"Long-running task submitted successfully (duration: {duration}s)",
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(
            "Failed to submit long-running task",
            duration=duration,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to submit long-running task"
        )
