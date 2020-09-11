import pytest

from nonbonded.cli.projects.utilities import extract_identifiers
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


@pytest.mark.parametrize(
    "model_type, identifier_kwargs",
    [
        (Project, {"project_id": "project-1"}),
        (Study, {"project_id": "project-1", "study_id": "study-1"}),
        (
            Optimization,
            {
                "project_id": "project-1",
                "study_id": "study-1",
                "optimization_id": "optimization-1",
            },
        ),
        (
            Benchmark,
            {
                "project_id": "project-1",
                "study_id": "study-1",
                "benchmark_id": "benchmark-1",
            },
        ),
    ],
)
def test_extract_identifiers(model_type, identifier_kwargs):
    assert extract_identifiers(model_type, {**identifier_kwargs}) == identifier_kwargs
