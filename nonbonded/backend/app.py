import os
from glob import glob

from fastapi import FastAPI, HTTPException
from starlette.responses import Response

from nonbonded.library.models.data import DataSetSummary, Substance
from nonbonded.library.models.project import Project
from nonbonded.library.molecules.utilities import smiles_to_image

app = FastAPI()

PROJECT_DIRECTORY = os.path.join("rest", "projects")


@app.get("/")
async def root():
    return {}


@app.get("/projects")
async def get_projects():

    if not os.path.isdir(PROJECT_DIRECTORY):
        return {}

    project_paths = glob(os.path.join(PROJECT_DIRECTORY, "*/project.json"))

    projects = [Project.parse_file(project_path) for project_path in project_paths]

    return {x.identifier: x for x in projects}


@app.post("/projects/")
async def post_project(project: Project):

    project_directory = os.path.join(PROJECT_DIRECTORY, project.identifier)
    os.makedirs(project_directory, exist_ok=True)

    project_path = os.path.join(project_directory, f"project.json")

    with open(project_path, "w") as file:
        file.write(project.json())

    return project


@app.get("/projects/{project_id}")
async def get_project(project_id):

    project_directory = os.path.join(PROJECT_DIRECTORY, project_id)
    project_path = os.path.join(project_directory, f"project.json")

    if not os.path.isfile(project_path):
        raise HTTPException(status_code=404, detail="Item not found")

    project = Project.parse_file(project_path)

    return project


@app.get("/molimage/{smiles}")
async def get_molecule_image(smiles):

    substance = Substance.from_url_string(smiles)

    svg_content = smiles_to_image(substance.smiles)
    svg_response = Response(svg_content, media_type="image/svg+xml")

    return svg_response


@app.get("/projects/{project_id}/{study_id}/test/summary")
async def get_test_set(project_id, study_id):

    study_directory = os.path.join(PROJECT_DIRECTORY, project_id, study_id)
    study_path = os.path.join(study_directory, "test_set_summary.json")

    if not os.path.isfile(study_path):
        raise HTTPException(status_code=404, detail="Item not found")

    data_set_summary = DataSetSummary.parse_file(study_path)

    return data_set_summary


@app.post("/projects/{project_id}/{study_id}/test/summary")
async def post_test_set(project_id, study_id, data_set_summary: DataSetSummary):

    study_directory = os.path.join(PROJECT_DIRECTORY, project_id, study_id)
    os.makedirs(study_directory, exist_ok=True)

    study_path = os.path.join(study_directory, "test_set_summary.json")

    with open(study_path, "w") as file:
        file.write(data_set_summary.json())

    return data_set_summary
