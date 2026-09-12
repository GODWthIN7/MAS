from fastapi import APIRouter, HTTPException
from uuid import UUID
from pydantic import BaseModel

from app.models.task import Task, TaskStatus, TaskPriority
from app.core.services import get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    required_expertise: list[str] = []
    team_id: UUID | None = None
    estimated_hours: float = 1.0


class AssignTaskRequest(BaseModel):
    agent_id: UUID


class CompleteTaskRequest(BaseModel):
    result: str = ""
    actual_hours: float = 0


@router.post("", response_model=Task)
async def create_task(request: CreateTaskRequest) -> Task:
    """Create a new task."""
    service = get_task_service()
    return service.create_task(
        title=request.title,
        description=request.description,
        priority=request.priority,
        required_expertise=request.required_expertise,
        team_id=request.team_id,
        estimated_hours=request.estimated_hours,
    )


@router.get("", response_model=list[Task])
async def list_tasks() -> list[Task]:
    """List all tasks."""
    service = get_task_service()
    return service.list_tasks()


@router.get("/status/pending", response_model=list[Task])
async def list_pending_tasks() -> list[Task]:
    """List pending tasks."""
    service = get_task_service()
    return service.list_pending_tasks()


@router.get("/status/ready", response_model=list[Task])
async def list_ready_tasks() -> list[Task]:
    """List ready tasks (no blocking dependencies)."""
    service = get_task_service()
    return service.list_ready_tasks()


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID) -> Task:
    """Get task by ID."""
    service = get_task_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/assign", response_model=Task)
async def assign_task(task_id: UUID, request: AssignTaskRequest) -> Task:
    """Assign task to agent."""
    service = get_task_service()
    task = service.assign_task(task_id, request.agent_id)
    if not task:
        raise HTTPException(status_code=400, detail="Cannot assign task")
    return task


@router.post("/{task_id}/start", response_model=Task)
async def start_task(task_id: UUID) -> Task:
    """Start task execution."""
    service = get_task_service()
    task = service.start_task(task_id)
    if not task:
        raise HTTPException(status_code=400, detail="Cannot start task")
    return task


@router.post("/{task_id}/complete", response_model=Task)
async def complete_task(task_id: UUID, request: CompleteTaskRequest) -> Task:
    """Mark task as completed."""
    service = get_task_service()
    task = service.complete_task(task_id, request.result, request.actual_hours)
    if not task:
        raise HTTPException(status_code=400, detail="Cannot complete task")
    return task


@router.get("/{task_id}/stats")
async def get_task_stats(task_id: UUID):
    """Get task statistics."""
    service = get_task_service()
    stats = service.get_task_stats(task_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Task not found")
    return stats
