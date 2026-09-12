from datetime import datetime
from uuid import UUID

from app.models.team import Team, TeamStatus


class TeamService:
    """Service for managing teams."""

    def __init__(self):
        self.teams: dict[UUID, Team] = {}

    def create_team(
        self, name: str, description: str = "", team_lead_id: UUID | None = None
    ) -> Team:
        """Create a new team."""
        team = Team(
            name=name,
            description=description,
            team_lead_id=team_lead_id,
        )
        self.teams[team.id] = team
        return team

    def get_team(self, team_id: UUID) -> Team | None:
        """Get team by ID."""
        return self.teams.get(team_id)

    def list_teams(self) -> list[Team]:
        """List all teams."""
        return list(self.teams.values())

    def list_active_teams(self) -> list[Team]:
        """List active teams."""
        return [t for t in self.teams.values() if t.status == TeamStatus.ACTIVE]

    def add_agent_to_team(self, team_id: UUID, agent_id: UUID) -> Team | None:
        """Add agent to team."""
        team = self.get_team(team_id)
        if team and agent_id not in team.agent_ids:
            team.agent_ids.append(agent_id)
            team.updated_at = datetime.utcnow()
            return team
        return None

    def remove_agent_from_team(self, team_id: UUID, agent_id: UUID) -> Team | None:
        """Remove agent from team."""
        team = self.get_team(team_id)
        if team and agent_id in team.agent_ids:
            team.agent_ids.remove(agent_id)
            team.updated_at = datetime.utcnow()
            return team
        return None

    def add_active_task(self, team_id: UUID, task_id: UUID) -> Team | None:
        """Add task to active task list."""
        team = self.get_team(team_id)
        if team and task_id not in team.active_task_ids:
            team.active_task_ids.append(task_id)
            team.updated_at = datetime.utcnow()
            return team
        return None

    def move_task_to_completed(self, team_id: UUID, task_id: UUID) -> Team | None:
        """Move task from active to completed list."""
        team = self.get_team(team_id)
        if team:
            if task_id in team.active_task_ids:
                team.active_task_ids.remove(task_id)
            if task_id not in team.completed_task_ids:
                team.completed_task_ids.append(task_id)
            team.updated_at = datetime.utcnow()
            return team
        return None

    def set_team_status(self, team_id: UUID, status: TeamStatus) -> Team | None:
        """Update team status."""
        team = self.get_team(team_id)
        if team:
            team.status = status
            team.updated_at = datetime.utcnow()
            return team
        return None

    def set_team_lead(self, team_id: UUID, agent_id: UUID) -> Team | None:
        """Set the team lead (coordinator)."""
        team = self.get_team(team_id)
        if team:
            team.team_lead_id = agent_id
            team.updated_at = datetime.utcnow()
            return team
        return None

    def get_team_stats(self, team_id: UUID) -> dict | None:
        """Get team performance statistics."""
        team = self.get_team(team_id)
        if not team:
            return None
        return {
            "team_id": team.id,
            "name": team.name,
            "status": team.status,
            "total_agents": team.total_agents,
            "active_tasks": team.active_task_count,
            "completed_tasks": team.total_completed,
            "efficiency": team.efficiency,
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        }
