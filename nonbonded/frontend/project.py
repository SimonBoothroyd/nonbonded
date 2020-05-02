import dash_bootstrap_components as dbc
import dash_html_components as html
import requests
from dash.dependencies import Input, Output

from nonbonded.frontend.app import app
from nonbonded.frontend.pages import summary, test, training
from nonbonded.library.models.project import Project

# The style arguments for the sidebar.
SIDEBAR_STYLE = {
    "height": "100%",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# The styles for the main content
CONTENT_STYLE = {"height": "100%", "padding": "3rem", "overflow": "auto"}

# Define the available pages
PAGES = {"summary": summary, "training": training, "test": test}

ROOT_PAGE_ID = "summary"

header = dbc.Navbar(
    children=[
        dbc.Col(dbc.NavbarBrand("", id="project-title")),
        dbc.Row(
            [
                dbc.Col(dbc.NavLink("Alcohol-Ester", href="#")),
                dbc.Col(
                    dbc.DropdownMenu(
                        children=[],
                        in_navbar=True,
                        label="Select a study",
                        id="project-study-selection",
                    ),
                ),
            ]
        ),
    ],
    color="dark",
    dark=True,
)

sidebar = html.Div(
    children=[
        dbc.Nav(
            [
                dbc.NavLink(page_module.title, href=f"{page_id}", id=f"{page_id}-link")
                for page_id, page_module in PAGES.items()
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
    id="project-sidebar",
)

content = html.Div(id="project-content", style=CONTENT_STYLE)

layout = html.Div(
    children=[
        html.Div(header, className="project__header"),
        html.Div(
            children=[
                html.Div(sidebar, className="project__sidebar"),
                html.Div(content, className="project__content"),
            ],
            className="project__container",
        ),
        html.Div(id="project-value", style={"display": "none"}),
    ],
)


@app.callback(
    [Output(f"{page_id}-link", "active") for page_id in PAGES],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    return [page_id in pathname for page_id in PAGES]


def load_project(project_name):

    project_response = requests.get(
        url=f"http://127.0.0.1:5000/projects/{project_name}"
    )

    if not project_response:
        return None

    project_json = project_response.json()
    project_model = Project(**project_json)

    return project_model


@app.callback(
    [
        Output("project-content", "children"),
        Output("project-title", "children"),
        Output("project-value", "children"),
        Output("project-study-selection", "children"),
    ],
    [Input("url", "pathname")],
)
def render_page_content(pathname):

    if pathname is None or not pathname.startswith("/project"):
        return html.Div([]), "", "", []

    pathname_split = pathname.split("/")
    pathname_split = [x for x in pathname_split if len(x) > 0]

    if len(pathname_split) < 3:
        return html.H4(children="Incorrect number of url arguments."), "", "", []

    project_name = pathname_split[1]

    if len(pathname_split) < 3:
        page_name = ROOT_PAGE_ID
    else:
        page_name = pathname_split[2]

    if page_name not in PAGES:
        return html.H4(children="Project page does not exist."), "", "", []

    project_model = load_project(project_name)

    if project_model is None:
        return (
            html.H4(children=f"The {project_name} project does not exist."),
            "",
            "",
            [],
        )

    study_names = [study.title for study in project_model.studies]
    study_items = [dbc.DropdownMenuItem(x, href="#") for x in study_names]

    current_study = project_model.studies[0]

    return (
        PAGES[page_name].get_layout(project_model, current_study),
        project_model.title,
        project_model.json(),
        study_items,
    )
