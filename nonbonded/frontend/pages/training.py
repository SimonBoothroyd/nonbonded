import dash_html_components as html

from nonbonded.library.models.project import Project, Study

title = "Training Data"


def get_layout(project_model: Project, study_model: Study):

    layout = html.Div([html.H3("Lorem Ipsum")])
    return layout
