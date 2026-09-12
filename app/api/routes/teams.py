from fastapi import APIRouter, HTTPException
from uuid import UUID
from pydantic import BaseModel

from app.models.team import Team, TeamStatus
from app.core.services import get_team_service

router = APIRouter(prefix="/teams", tags=["teams"])


class CreateTeamRequest(BaseModel):
    name: str
    description: str = ""
    team_lead_id: UUID | None = None


class AddAgentRequest(BaseModel):
    agent_id: UUID


class AddTaskRequest(BaseModel):
    task_id: UUID


@router.post("", response_model=Team)
async def create_team(request: CreateTeamRequest) -> Team:
    """Create a new team."""
    service = get_team_service()
    return service.create_team(
        name=request.name,
        description=request.description,
        team_lead_id=request.team_lead_id,
    )


@router.get("", response_model=list[Team])
async def list_teams() -> list[Team]:
    """List all teams."""
    service = get_team_service()
    return service.list_teams()


@router.get("/status/active", response_model=list[Team])
async def list_active_teams() -> list[Team]:
    """List active teams."""
    service = get_team_service()
    return service.list_active_teams()


@router.get("/{team_id}", response_model=Team)
async def get_team(team_id: UUID) -> Team:
    """Get team by ID."""
    service = get_team_service()
    team = service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/{team_id}/stats")
async def get_team_stats(team_id: UUID):
    """Get team statistics."""
    service = get_team_service()
    stats = service.get_team_stats(team_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Team not found")
    return stats


@router.post("/{team_id}/agents", response_model=Team)
async def add_agent_to_team(team_id: UUID, request: AddAgentRequest) -> Team:
    """Add agent to team."""
    service = get_team_service()
    team = service.add_agent_to_team(team_id, request.agent_id)
    if not team:
        raise HTTPException(status_code=400, detail="Cannot add agent to team")
    return team


@router.delete("/{team_id}/agents/{agent_id}", response_model=Team)
async def remove_agent_from_team(team_id: UUID, agent_id: UUID) -> Team:
    """Remove agent from team."""
    service = get_team_service()
    team = service.remove_agent_from_team(team_id, agent_id)
    if not team:
        raise HTTPException(status_code=400, detail="Cannot remove agent from team")
    return team


@router.post("/{team_id}/tasks", response_model=Team)
async def add_task_to_team(team_id: UUID, request: AddTaskRequest) -> Team:
    """Add task to team's active tasks."""
    service = get_team_service()
    team = service.add_active_task(team_id, request.task_id)
    if not team:
        raise HTTPException(status_code=400, detail="Cannot add task to team")
    return team


@router.put("/{team_id}/status", response_model=Team)
async def update_team_status(team_id: UUID, status: TeamStatus) -> Team:
    """Update team status."""
    service = get_team_service()
    team = service.set_team_status(team_id, status)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
