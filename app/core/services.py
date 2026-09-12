from functools import lru_cache

from app.services.agent_service import AgentService
from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.services.collaboration_service import CollaborationService
from app.services.orchestrator_service import OrchestratorService


@lru_cache
def get_agent_service() -> AgentService:
    """Get singleton agent service."""
    return AgentService()


@lru_cache
def get_task_service() -> TaskService:
    """Get singleton task service."""
    return TaskService()


@lru_cache
def get_team_service() -> TeamService:
    """Get singleton team service."""
    return TeamService()


@lru_cache
def get_collaboration_service() -> CollaborationService:
    """Get singleton collaboration service."""
    return CollaborationService()


@lru_cache
def get_orchestrator_service() -> OrchestratorService:
    """Get singleton orchestrator service."""
    return OrchestratorService(
        agent_service=get_agent_service(),
        task_service=get_task_service(),
        team_service=get_team_service(),
        collab_service=get_collaboration_service(),
    )
