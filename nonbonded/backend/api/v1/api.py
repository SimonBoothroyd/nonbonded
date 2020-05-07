from fastapi import APIRouter

from nonbonded.backend.api.v1.endpoints import molecules, projects

api_router = APIRouter()
api_router.include_router(molecules.router, prefix="/molecules", tags=["molecules"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
