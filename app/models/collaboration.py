from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CollaborationStatus(str, Enum):
    """Collaboration lifecycle states."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Collaboration(BaseModel):
    """Represents collaboration between agents on a task."""
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    team_id: UUID
    primary_agent_id: UUID = Field(description="Agent leading the collaboration")
    supporting_agent_ids: list[UUID] = Field(default_factory=list)
    status: CollaborationStatus = CollaborationStatus.INITIATED
    messages: list[str] = Field(default_factory=list, description="Interaction history")
    decision_log: list[str] = Field(default_factory=list, description="Key decisions made")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)

    @property
    def total_collaborators(self) -> int:
        """Get total agents involved."""
        return 1 + len(self.supporting_agent_ids)

    def add_message(self, message: str) -> None:
        """Record a collaboration message."""
        self.messages.append(f"[{datetime.utcnow().isoformat()}] {message}")

    def add_decision(self, decision: str) -> None:
        """Record a decision made during collaboration."""
        self.decision_log.append(f"[{datetime.utcnow().isoformat()}] {decision}")
