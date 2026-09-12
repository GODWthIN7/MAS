from fastapi import APIRouter, HTTPException
from uuid import UUID
from pydantic import BaseModel

from app.models.agent import Agent, AgentRole, AgentStatus
from app.core.services import get_agent_service

router = APIRouter(prefix="/agents", tags=["agents"])


class CreateAgentRequest(BaseModel):
    name: str
    role: AgentRole
    expertise: list[str] = []
    capacity: int = 5


class AgentStatusUpdate(BaseModel):
    status: AgentStatus


@router.post("", response_model=Agent)
async def create_agent(request: CreateAgentRequest) -> Agent:
    """Create a new agent."""
    service = get_agent_service()
    return service.create_agent(
        name=request.name,
        role=request.role,
        expertise=request.expertise,
        capacity=request.capacity,
    )


@router.get("", response_model=list[Agent])
async def list_agents() -> list[Agent]:
    """List all agents."""
    service = get_agent_service()
    return service.list_agents()


@router.get("/available", response_model=list[Agent])
async def list_available_agents() -> list[Agent]:
    """List available agents."""
    service = get_agent_service()
    return service.list_available_agents()


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: UUID) -> Agent:
    """Get agent by ID."""
    service = get_agent_service()
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{agent_id}/stats")
async def get_agent_stats(agent_id: UUID):
    """Get agent statistics."""
    service = get_agent_service()
    stats = service.get_agent_stats(agent_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Agent not found")
    return stats


@router.put("/{agent_id}/status", response_model=Agent)
async def update_agent_status(agent_id: UUID, request: AgentStatusUpdate) -> Agent:
    """Update agent status."""
    service = get_agent_service()
    agent = service.set_agent_status(agent_id, request.status)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/role/{role}", response_model=list[Agent])
async def get_agents_by_role(role: AgentRole) -> list[Agent]:
    """Get agents by role."""
    service = get_agent_service()
    return service.find_agents_by_role(role)
