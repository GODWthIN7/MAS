from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    """Represents a task for agent execution."""
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent_id: UUID | None = Field(default=None)
    team_id: UUID | None = Field(default=None)
    required_expertise: list[str] = Field(default_factory=list)
    dependencies: list[UUID] = Field(default_factory=list, description="Task IDs that must complete first")
    result: str = Field(default="", description="Task execution result or output")
    error: str = Field(default="", description="Error message if task failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    estimated_hours: float = Field(default=1.0, ge=0.1, description="Estimated effort in hours")
    actual_hours: float = Field(default=0.0, ge=0, description="Actual effort spent")

    @property
    def is_ready(self) -> bool:
        """Check if task is ready to be assigned (no blocking dependencies)."""
        return self.status == TaskStatus.PENDING and not self.dependencies

    @property
    def duration(self) -> float | None:
        """Get task duration if completed."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 3600
        return None
