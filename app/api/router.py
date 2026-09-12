from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.agents import router as agents_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.teams import router as teams_router
from app.api.routes.orchestration import router as orchestration_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(agents_router)
api_router.include_router(tasks_router)
api_router.include_router(teams_router)
api_router.include_router(orchestration_router)
