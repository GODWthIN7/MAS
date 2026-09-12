from fastapi import APIRouter, HTTPException
from uuid import UUID
from pydantic import BaseModel

from app.core.services import get_orchestrator_service

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


class InitiateCollaborationRequest(BaseModel):
    task_id: UUID
    team_id: UUID
    primary_agent_id: UUID


class AssignAndStartRequest(BaseModel):
    task_id: UUID
    agent_id: UUID


class CompleteTaskWorkflowRequest(BaseModel):
    task_id: UUID
    result: str = ""
    actual_hours: float = 0


@router.post("/collaborate", response_model=dict)
async def initiate_collaboration(request: InitiateCollaborationRequest):
    """Initiate collaboration on a task."""
    orchestrator = get_orchestrator_service()
    collab_id = orchestrator.initiate_collaboration(
        task_id=request.task_id,
        team_id=request.team_id,
        primary_agent_id=request.primary_agent_id,
    )
    if not collab_id:
        raise HTTPException(status_code=400, detail="Cannot initiate collaboration")
    return {"collaboration_id": collab_id}


@router.post("/assign-and-start")
async def assign_and_start_task(request: AssignAndStartRequest):
    """Assign task to agent and start execution."""
    orchestrator = get_orchestrator_service()
    assigned = orchestrator.assign_task_to_agent(request.task_id, request.agent_id)
    if not assigned:
        raise HTTPException(status_code=400, detail="Cannot assign task")
    started = orchestrator.start_task(request.task_id)
    if not started:
        raise HTTPException(status_code=400, detail="Cannot start task")
    return {"task_id": request.task_id, "agent_id": request.agent_id, "status": "started"}


@router.post("/complete-workflow")
async def complete_task_workflow(request: CompleteTaskWorkflowRequest):
    """Complete task and update all related entities."""
    orchestrator = get_orchestrator_service()
    success = orchestrator.complete_task_workflow(
        task_id=request.task_id,
        result=request.result,
        actual_hours=request.actual_hours,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Cannot complete task workflow")
    return {"task_id": request.task_id, "status": "completed"}


@router.get("/team/{team_id}/status")
async def get_workflow_status(team_id: UUID):
    """Get comprehensive workflow status for a team."""
    orchestrator = get_orchestrator_service()
    status = orchestrator.get_workflow_status(team_id)
    if not status:
        raise HTTPException(status_code=404, detail="Team not found")
    return status


@router.get("/agent/{agent_id}/workload")
async def get_agent_workload(agent_id: UUID):
    """Get current workload for an agent."""
    orchestrator = get_orchestrator_service()
    workload = orchestrator.get_agent_workload(agent_id)
    if not workload:
        raise HTTPException(status_code=404, detail="Agent not found")
    return workload
