from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TeamStatus(str, Enum):
    """Team operational status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Team(BaseModel):
    """Represents a development team of agents."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    status: TeamStatus = TeamStatus.ACTIVE
    agent_ids: list[UUID] = Field(default_factory=list)
    active_task_ids: list[UUID] = Field(default_factory=list)
    completed_task_ids: list[UUID] = Field(default_factory=list)
    team_lead_id: UUID | None = Field(default=None, description="Coordinator agent ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_agents(self) -> int:
        """Get total number of agents on team."""
        return len(self.agent_ids)

    @property
    def active_task_count(self) -> int:
        """Get current active task count."""
        return len(self.active_task_ids)

    @property
    def total_completed(self) -> int:
        """Get total completed tasks."""
        return len(self.completed_task_ids)

    @property
    def efficiency(self) -> float:
        """Calculate team efficiency (completed / total)."""
        total = self.active_task_count + self.total_completed
        if total == 0:
            return 0.0
        return round((self.total_completed / total) * 100, 2)
