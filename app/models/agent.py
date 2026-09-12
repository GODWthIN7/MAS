from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent roles in the development team."""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"


class AgentStatus(str, Enum):
    """Agent operational status."""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


class Agent(BaseModel):
    """Represents an AI agent in the development team."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    role: AgentRole
    status: AgentStatus = AgentStatus.IDLE
    expertise: list[str] = Field(default_factory=list, description="Technical expertise areas")
    capacity: int = Field(default=5, ge=1, le=20, description="Concurrent tasks this agent can handle")
    active_tasks: int = Field(default=0, ge=0, description="Currently active tasks")
    total_completed: int = Field(default=0, ge=0, description="Lifetime completed tasks")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_available(self) -> bool:
        """Check if agent can take new tasks."""
        return self.status == AgentStatus.IDLE and self.active_tasks < self.capacity

    def can_handle(self, expertise_required: list[str]) -> bool:
        """Check if agent has required expertise."""
        return any(exp in self.expertise for exp in expertise_required)
