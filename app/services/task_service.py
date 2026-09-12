from datetime import datetime
from uuid import UUID

from app.models.task import Task, TaskStatus, TaskPriority


class TaskService:
    """Service for managing tasks."""

    def __init__(self):
        self.tasks: dict[UUID, Task] = {}

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        required_expertise: list[str] | None = None,
        team_id: UUID | None = None,
        estimated_hours: float = 1.0,
    ) -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            required_expertise=required_expertise or [],
            team_id=team_id,
            estimated_hours=estimated_hours,
        )
        self.tasks[task.id] = task
        return task

    def get_task(self, task_id: UUID) -> Task | None:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(self) -> list[Task]:
        """List all tasks."""
        return list(self.tasks.values())

    def list_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """List tasks with specific status."""
        return [t for t in self.tasks.values() if t.status == status]

    def list_tasks_by_priority(self, priority: TaskPriority) -> list[Task]:
        """List tasks with specific priority."""
        return [t for t in self.tasks.values() if t.priority == priority]

    def list_pending_tasks(self) -> list[Task]:
        """List all pending tasks."""
        return self.list_tasks_by_status(TaskStatus.PENDING)

    def list_ready_tasks(self) -> list[Task]:
        """List tasks ready to be assigned (no dependencies blocking)."""
        return [t for t in self.list_pending_tasks() if t.is_ready]

    def assign_task(self, task_id: UUID, agent_id: UUID) -> Task | None:
        """Assign task to an agent."""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.assigned_agent_id = agent_id
            task.status = TaskStatus.ASSIGNED
            return task
        return None

    def start_task(self, task_id: UUID) -> Task | None:
        """Start task execution."""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.ASSIGNED:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()
            return task
        return None

    def complete_task(self, task_id: UUID, result: str = "", actual_hours: float = 0) -> Task | None:
        """Mark task as completed."""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.IN_PROGRESS:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.actual_hours = actual_hours
            task.completed_at = datetime.utcnow()
            return task
        return None

    def fail_task(self, task_id: UUID, error: str = "") -> Task | None:
        """Mark task as failed."""
        task = self.get_task(task_id)
        if task and task.status in (TaskStatus.IN_PROGRESS, TaskStatus.ASSIGNED):
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.utcnow()
            return task
        return None

    def block_task(self, task_id: UUID) -> Task | None:
        """Block task due to external dependencies."""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.BLOCKED
            return task
        return None

    def unblock_task(self, task_id: UUID) -> Task | None:
        """Unblock task and return to pending."""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.BLOCKED:
            task.status = TaskStatus.PENDING
            return task
        return None

    def add_dependency(self, task_id: UUID, dependency_id: UUID) -> Task | None:
        """Add a dependency to a task."""
        task = self.get_task(task_id)
        if task and dependency_id not in task.dependencies:
            task.dependencies.append(dependency_id)
            return task
        return None

    def resolve_dependency(self, task_id: UUID, dependency_id: UUID) -> Task | None:
        """Remove a resolved dependency."""
        task = self.get_task(task_id)
        if task and dependency_id in task.dependencies:
            task.dependencies.remove(dependency_id)
            return task
        return None

    def get_task_stats(self, task_id: UUID) -> dict | None:
        """Get task statistics."""
        task = self.get_task(task_id)
        if not task:
            return None
        return {
            "task_id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "assigned_agent_id": task.assigned_agent_id,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "duration": task.duration,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
        }
