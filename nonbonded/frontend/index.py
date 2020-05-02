from typing import Dict

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import requests
from dash.dependencies import Input, Output

from nonbonded.frontend import project
from nonbonded.frontend.app import app
from nonbonded.frontend.project import ROOT_PAGE_ID
from nonbonded.library.models.project import Project


def initialize():

    app.layout = html.Div(
        children=[dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
    )


def build_project_cards(projects: Dict[str, Project]):

    card_rows = []

    for project_id, project_model in projects.items():

        author_list = ", ".join(x.name for x in project_model.authors)

        card_content = [
            dbc.CardBody(
                [
                    html.H5(
                        dcc.Link(
                            project_model.title,
                            href=f"/project/{project_id}/{ROOT_PAGE_ID}",
                        ),
                        className="card-title",
                    ),
                    html.H6(author_list),
                    html.Hr(),
                    html.P(project_model.abstract, className="card-text"),
                ]
            ),
        ]

        card_rows.append(
            dbc.Row(
                [dbc.Col(dbc.Card(card_content), width={"size": 10, "offset": 1})],
                className="mb-4",
            ),
        )

    cards = html.Div(card_rows)
    return cards


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):

    if pathname is None or pathname == "/":

        projects_result = requests.get(url="http://127.0.0.1:5000/projects")

        children = [html.Div([html.H1(children="Projects")], className="app__header")]

        if projects_result:

            projects = {
                project_id: Project(**project_json)
                for project_id, project_json in projects_result.json().items()
            }

            project_cards = build_project_cards(projects)
            children.append(project_cards)

        else:
            children.append(html.H4(children="The REST API could not be reached."))

        html.Div(children=children)

    elif pathname.endswith("/project"):
        children = html.H4(children="No project specified.")

    elif "/project/" in pathname:
        children = project.layout

    else:
        return "404"

    container = html.Div(children, className="app__container")
    return container
