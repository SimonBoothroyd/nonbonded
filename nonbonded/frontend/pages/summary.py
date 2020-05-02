import dash_html_components as html

from nonbonded.library.models.project import Optimization, Project, Study

title = "Summary"


def get_optimization_summary(optimization: Optimization):

    card_content = [
        html.Div(
            [
                html.H6(optimization.title, className="card-title"),
                # html.Hr(),
                html.P(optimization.description, className="card-text"),
            ]
        ),
    ]

    return html.Li(card_content)


def get_layout(project_model: Project, study_model: Study):

    if len(project_model.studies) == 0:
        return html.H3("No study was selected.")

    study = project_model.studies[0]

    layout = [
        html.H3(study.title, className="text-center"),
        html.Hr(),
        html.P(study.description),
    ]

    n_optimizations = len(study.optimizations)

    if n_optimizations > 0:

        layout.extend(
            [html.Br(), html.H4("Optimizations", className="text-center"), html.Br(),]
        )

        optimization_list = []

        for optimization in study.optimizations:
            optimization_list.append(get_optimization_summary(optimization))

        layout.append(html.Ul(optimization_list))

        return html.Div(layout)
