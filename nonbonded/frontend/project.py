import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from nonbonded.frontend.app import app
from nonbonded.frontend.pages import lorem, summary

# The style arguments for the sidebar.
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "0rem",
    "left": 0,
    "bottom": 0,
    "width": "24rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# The styles for the main content
CONTENT_STYLE = {
    "margin-left": "26rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Define the available pages
PAGES = {"summary": summary, "lorem": lorem}

ROOT_PAGE_ID = "summary"

sidebar = html.Div(
    children=[
        html.H2("Sidebar", className="display-4"),
        dcc.Link("Return to projects page", href="/"),
        html.Hr(),
        html.P("A simple sidebar layout with navigation links", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink(
                    page_module.title, href=f"/project/{page_id}", id=f"{page_id}-link"
                )
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

layout = html.Div([sidebar, content])


@app.callback(
    [Output(f"{page_id}-link", "active") for page_id in PAGES],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    return [page_id in pathname for page_id in PAGES]


@app.callback(Output("project-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):

    if pathname is None or not pathname.startswith("/project"):
        return html.Div([])

    if pathname == "/project":
        pathname = f"/project/{ROOT_PAGE_ID}"

    page_id = next(iter(page_id for page_id in PAGES if pathname.endswith(page_id)))

    return PAGES[page_id].layout
