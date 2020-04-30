import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from nonbonded.frontend import project
from nonbonded.frontend.app import app

PROJECTS = ["Binary Mixture Feasibility"]


def initialize():

    app.layout = html.Div(
        children=[dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
    )


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):

    if pathname is None or pathname == "/":
        children = html.Div(
            children=[
                html.H1(children="Hello Dash"),
                *[dcc.Link(project_name, href="/project") for project_name in PROJECTS],
            ]
        )

    elif pathname.endswith("/project") or "/project/" in pathname:
        children = project.layout

    else:
        return "404"

    return children
