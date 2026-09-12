from uuid import UUID

from app.models.collaboration import Collaboration, CollaborationStatus


class CollaborationService:
    """Service for managing agent collaboration."""

    def __init__(self):
        self.collaborations: dict[UUID, Collaboration] = {}

    def create_collaboration(
        self,
        task_id: UUID,
        team_id: UUID,
        primary_agent_id: UUID,
        supporting_agent_ids: list[UUID] | None = None,
    ) -> Collaboration:
        """Create a new collaboration session."""
        collab = Collaboration(
            task_id=task_id,
            team_id=team_id,
            primary_agent_id=primary_agent_id,
            supporting_agent_ids=supporting_agent_ids or [],
        )
        self.collaborations[collab.id] = collab
        return collab

    def get_collaboration(self, collab_id: UUID) -> Collaboration | None:
        """Get collaboration by ID."""
        return self.collaborations.get(collab_id)

    def list_collaborations(self) -> list[Collaboration]:
        """List all collaborations."""
        return list(self.collaborations.values())

    def list_collaborations_by_task(self, task_id: UUID) -> list[Collaboration]:
        """List collaborations for a specific task."""
        return [c for c in self.collaborations.values() if c.task_id == task_id]

    def list_collaborations_by_team(self, team_id: UUID) -> list[Collaboration]:
        """List collaborations for a specific team."""
        return [c for c in self.collaborations.values() if c.team_id == team_id]

    def list_active_collaborations(self) -> list[Collaboration]:
        """List ongoing collaborations."""
        return [c for c in self.collaborations.values() if c.status == CollaborationStatus.IN_PROGRESS]

    def start_collaboration(self, collab_id: UUID) -> Collaboration | None:
        """Start a collaboration session."""
        collab = self.get_collaboration(collab_id)
        if collab and collab.status == CollaborationStatus.INITIATED:
            collab.status = CollaborationStatus.IN_PROGRESS
            return collab
        return None

    def add_message(self, collab_id: UUID, message: str) -> Collaboration | None:
        """Add a message to collaboration."""
        collab = self.get_collaboration(collab_id)
        if collab:
            collab.add_message(message)
            return collab
        return None

    def add_decision(self, collab_id: UUID, decision: str) -> Collaboration | None:
        """Record a decision in collaboration."""
        collab = self.get_collaboration(collab_id)
        if collab:
            collab.add_decision(decision)
            return collab
        return None

    def add_supporting_agent(self, collab_id: UUID, agent_id: UUID) -> Collaboration | None:
        """Add a supporting agent to collaboration."""
        collab = self.get_collaboration(collab_id)
        if collab and agent_id not in collab.supporting_agent_ids:
            collab.supporting_agent_ids.append(agent_id)
            return collab
        return None

    def complete_collaboration(self, collab_id: UUID) -> Collaboration | None:
        """Mark collaboration as completed."""
        collab = self.get_collaboration(collab_id)
        if collab and collab.status == CollaborationStatus.IN_PROGRESS:
            from datetime import datetime
            collab.status = CollaborationStatus.COMPLETED
            collab.completed_at = datetime.utcnow()
            return collab
        return None

    def fail_collaboration(self, collab_id: UUID) -> Collaboration | None:
        """Mark collaboration as failed."""
        collab = self.get_collaboration(collab_id)
        if collab and collab.status == CollaborationStatus.IN_PROGRESS:
            from datetime import datetime
            collab.status = CollaborationStatus.FAILED
            collab.completed_at = datetime.utcnow()
            return collab
        return None

    def get_collaboration_summary(self, collab_id: UUID) -> dict | None:
        """Get collaboration summary."""
        collab = self.get_collaboration(collab_id)
        if not collab:
            return None
        return {
            "collaboration_id": collab.id,
            "task_id": collab.task_id,
            "team_id": collab.team_id,
            "status": collab.status,
            "total_collaborators": collab.total_collaborators,
            "primary_agent_id": collab.primary_agent_id,
            "supporting_agents": len(collab.supporting_agent_ids),
            "messages": len(collab.messages),
            "decisions": len(collab.decision_log),
            "created_at": collab.created_at,
            "completed_at": collab.completed_at,
        }
