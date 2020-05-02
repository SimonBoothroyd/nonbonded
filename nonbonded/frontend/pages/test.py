import dash_html_components as html
import requests

from nonbonded.library.models.data import DataSetSummary
from nonbonded.library.models.project import Project, Study

title = "Test Data"


def get_layout(project_model: Project, study_model: Study):

    summary_response = requests.get(
        url=(
            f"http://127.0.0.1:5000/projects/{project_model.identifier}/"
            f"{study_model.identifier}/test/summary"
        )
    )

    if not summary_response:
        return html.H3("The studies test set could not be retrieved.")

    data_set_summary = DataSetSummary(**summary_response.json())

    layout = [
        html.H3("Benchmark Test Set", className="text-center"),
        html.Hr(),
        html.P(
            f"The benchmark test set contains a total of "
            f"{data_set_summary.n_data_points} physical property data points."
        ),
    ]

    for substance in data_set_summary.substances:

        substance_src_url = substance.components.to_url_string()
        substance_src_url_split = substance_src_url.split(".")

        for component_src_url in substance_src_url_split:

            full_src_url = f"http://127.0.0.1:5000/molimage/{component_src_url}"

            layout.append(
                html.Img(
                    src=full_src_url,
                    width="175px",
                    height="175px",
                    style={"border": "1px solid grey"},
                )
            )

    return layout
