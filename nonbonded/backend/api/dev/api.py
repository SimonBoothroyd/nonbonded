from fastapi import APIRouter

from nonbonded.backend.api.dev.endpoints import datasets, plotly, projects

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(plotly.router, prefix="/plotly", tags=["plotly"])
