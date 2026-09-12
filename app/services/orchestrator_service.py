from uuid import UUID

from app.models.agent import AgentStatus
from app.models.task import TaskStatus
from app.services.agent_service import AgentService
from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.services.collaboration_service import CollaborationService


class OrchestratorService:
    """Service for orchestrating multi-agent workflows."""

    def __init__(
        self,
        agent_service: AgentService,
        task_service: TaskService,
        team_service: TeamService,
        collab_service: CollaborationService,
    ):
        self.agent_service = agent_service
        self.task_service = task_service
        self.team_service = team_service
        self.collab_service = collab_service

    def assign_task_to_agent(self, task_id: UUID, agent_id: UUID) -> bool:
        """
        Assign a task to an agent and update all related entities.
        Returns True if assignment successful.
        """
        task = self.task_service.assign_task(task_id, agent_id)
        if not task:
            return False

        agent = self.agent_service.assign_task(agent_id)
        if not agent:
            self.task_service.get_task(task_id).status = TaskStatus.PENDING
            return False

        return True

    def start_task(self, task_id: UUID) -> bool:
        """Start task execution."""
        task = self.task_service.start_task(task_id)
        if task and task.assigned_agent_id:
            self.agent_service.set_agent_status(task.assigned_agent_id, AgentStatus.BUSY)
            return True
        return False

    def complete_task_workflow(
        self, task_id: UUID, result: str = "", actual_hours: float = 0
    ) -> bool:
        """
        Complete a task and update agent, team, and collaboration records.
        """
        task = self.task_service.complete_task(task_id, result, actual_hours)
        if not task or not task.assigned_agent_id or not task.team_id:
            return False

        # Update agent
        self.agent_service.complete_task(task.assigned_agent_id)

        # Update team
        self.team_service.move_task_to_completed(task.team_id, task_id)

        # Resolve dependencies for dependent tasks
        for other_task in self.task_service.list_tasks():
            if task_id in other_task.dependencies:
                self.task_service.resolve_dependency(other_task.id, task_id)
                if other_task.is_ready:
                    # Task is now ready to be assigned
                    pass

        return True

    def fail_task_workflow(self, task_id: UUID, error: str = "") -> bool:
        """
        Mark task as failed and handle cleanup.
        """
        task = self.task_service.fail_task(task_id, error)
        if not task or not task.assigned_agent_id:
            return False

        # Update agent
        self.agent_service.complete_task(task.assigned_agent_id)

        # Block any dependent tasks
        for other_task in self.task_service.list_tasks():
            if task_id in other_task.dependencies:
                self.task_service.block_task(other_task.id)

        return True

    def initiate_collaboration(
        self, task_id: UUID, team_id: UUID, primary_agent_id: UUID
    ) -> UUID | None:
        """
        Create and start a collaboration for a task.
        Returns collaboration ID.
        """
        team = self.team_service.get_team(team_id)
        if not team:
            return None

        # Find supporting agents (other available agents on team)
        supporting_agents = [
            aid
            for aid in team.agent_ids
            if aid != primary_agent_id and self.agent_service.get_agent(aid).is_available
        ]

        collab = self.collab_service.create_collaboration(
            task_id=task_id,
            team_id=team_id,
            primary_agent_id=primary_agent_id,
            supporting_agent_ids=supporting_agents,
        )

        self.collab_service.start_collaboration(collab.id)
        return collab.id

    def get_workflow_status(self, team_id: UUID) -> dict:
        """Get comprehensive workflow status for a team."""
        team = self.team_service.get_team(team_id)
        if not team:
            return {}

        agents = [self.agent_service.get_agent(aid) for aid in team.agent_ids]
        active_tasks = [self.task_service.get_task(tid) for tid in team.active_task_ids]
        collaborations = self.collab_service.list_collaborations_by_team(team_id)

        return {
            "team_id": team_id,
            "team_name": team.name,
            "team_status": team.status,
            "agents": {
                "total": len(agents),
                "available": len([a for a in agents if a.is_available]),
                "busy": len([a for a in agents if a.status == AgentStatus.BUSY]),
                "offline": len([a for a in agents if a.status == AgentStatus.OFFLINE]),
            },
            "tasks": {
                "active": len(active_tasks),
                "completed": len(team.completed_task_ids),
                "pending": len(self.task_service.list_pending_tasks()),
            },
            "collaborations": {
                "active": len(self.collab_service.list_active_collaborations()),
                "total": len(collaborations),
            },
            "team_efficiency": team.efficiency,
        }

    def get_agent_workload(self, agent_id: UUID) -> dict:
        """Get current workload for an agent."""
        agent = self.agent_service.get_agent(agent_id)
        if not agent:
            return {}

        assigned_tasks = [
            t
            for t in self.task_service.list_tasks()
            if t.assigned_agent_id == agent_id and t.status == TaskStatus.IN_PROGRESS
        ]

        return {
            "agent_id": agent_id,
            "name": agent.name,
            "role": agent.role,
            "capacity": agent.capacity,
            "active_tasks": agent.active_tasks,
            "utilization_percent": round((agent.active_tasks / agent.capacity) * 100, 2),
            "assigned_tasks": [{"id": t.id, "title": t.title} for t in assigned_tasks],
            "status": agent.status,
        }
