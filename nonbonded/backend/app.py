import os
from glob import glob

from fastapi import FastAPI, HTTPException

from nonbonded.library.models.project import Project

app = FastAPI()

PROJECT_DIRECTORY = os.path.join("rest", "projects")


@app.get("/")
async def root():
    return {}


@app.get("/projects")
async def get_projects():

    if not os.path.isdir(PROJECT_DIRECTORY):
        return {}

    project_paths = glob(os.path.join(PROJECT_DIRECTORY, "*.json"))

    projects = [Project.parse_file(project_path) for project_path in project_paths]

    return {x.identifier: x for x in projects}


@app.post("/projects/")
async def post_project(project: Project):

    os.makedirs(PROJECT_DIRECTORY, exist_ok=True)

    project_path = os.path.join(PROJECT_DIRECTORY, f"{project.identifier}.json")

    with open(project_path, "w") as file:
        file.write(project.json())

    return project


@app.get("/projects/{project_id}")
async def get_project(project_id):

    project_path = os.path.join(PROJECT_DIRECTORY, f"{project_id}.json")

    if not os.path.isfile(project_path):
        raise HTTPException(status_code=404, detail="Item not found")

    project = Project.parse_file(project_path)

    return project
