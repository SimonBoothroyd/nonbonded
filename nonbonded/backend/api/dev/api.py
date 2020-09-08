from fastapi import APIRouter

from nonbonded.backend.api.dev.endpoints import datasets, molecules, molsets, projects

api_router = APIRouter()
api_router.include_router(molecules.router, prefix="/molecules", tags=["molecules"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(molsets.router, prefix="/molsets", tags=["molsets"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
